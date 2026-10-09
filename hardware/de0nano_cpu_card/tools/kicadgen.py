"""Minimal KiCad-6-format .kicad_sch generator, upgraded to v10 via kicad-cli afterward.
Parses real symbol library files (as shipped with KiCad 10) for pin geometry, embeds
their verbatim definitions into each sheet's lib_symbols cache, places component
instances, and wires every pin to a net via a short stub + global_label (or a power
symbol for power nets).
"""
import re, uuid, math, os

STAGE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "symstage")

def u():
    return str(uuid.uuid4())

def balanced_block(text, start_idx):
    """Given text[start_idx] == '(', return the full balanced-paren substring."""
    depth = 0
    i = start_idx
    in_str = False
    while i < len(text):
        c = text[i]
        if c == '"' and text[i-1] != '\\':
            in_str = not in_str
        elif not in_str:
            if c == '(':
                depth += 1
            elif c == ')':
                depth -= 1
                if depth == 0:
                    return text[start_idx:i+1]
        i += 1
    raise ValueError("unbalanced")

def find_nested_blocks(text, tag):
    """Like find_blocks, but for blocks nested just inside an outer block whose
    own text starts with the same tag at index 0 (so find_blocks would just
    re-match the whole outer span and never see what's inside it). Starts the
    scan one character in, skipping the outer match."""
    out = []
    i = 1
    pat = "(" + tag
    while True:
        idx = text.find(pat, i)
        if idx == -1:
            break
        nc = text[idx+len(pat)]
        if nc in (' ', '"', '\n', '\t'):
            blk = balanced_block(text, idx)
            out.append(blk)
            i = idx + len(blk)
        else:
            i = idx + len(pat)
    return out


def find_blocks(text, tag):
    """Find all top-level-ish balanced blocks starting with '(tag ' or '(tag\"'."""
    out = []
    i = 0
    pat = "(" + tag
    while True:
        idx = text.find(pat, i)
        if idx == -1:
            break
        # ensure next char after tag is space or quote (word boundary)
        nc = text[idx+len(pat)]
        if nc in (' ', '"', '\n', '\t'):
            blk = balanced_block(text, idx)
            out.append((idx, blk))
            i = idx + len(blk)
        else:
            i = idx + len(pat)
    return out

class SymbolDef:
    def __init__(self, filename, lib_nickname):
        path = os.path.join(STAGE, filename)
        with open(path) as f:
            self.text = f.read()
        self.lib_nickname = lib_nickname
        m = re.search(r'\(symbol "([^"]+)"', self.text)
        self.name = m.group(1)
        ext = re.search(r'\(extends "([^"]+)"\)', self.text)
        self.extends = ext.group(1) if ext else None
        self.pins = {}   # number -> dict(x,y,angle,name,etype)
        self._parse_pins(self.text)
        # Which unit number actually carries the pins. Convention is unit 1
        # (e.g. "Name_1_1"), but some library symbols (PWR_FLAG) put their pin
        # in unit 0 ("Name_0_0") instead -- detect it rather than assume.
        self.pin_unit = self._detect_pin_unit()

    def _detect_pin_unit(self):
        m = re.search(rf'\(symbol "{re.escape(self.name)}_(\d+)_\d+"\s*\(pin ', self.text)
        if m:
            return int(m.group(1))
        return 1

    def _parse_pins(self, text):
        etypes = ("input","output","bidirectional","tri_state","passive",
                  "free","unspecified","power_in","power_out","open_collector",
                  "open_emitter","no_connect")
        for idx, blk in find_blocks(text, "pin"):
            head = blk[:40]
            etype = None
            for et in etypes:
                if blk.startswith(f"(pin {et} "):
                    etype = et
                    break
            if etype is None:
                continue
            mat = re.search(r'\(at\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\)', blk)
            mname = re.search(r'\(name\s+"([^"]*)"', blk)
            mnum = re.search(r'\(number\s+"([^"]*)"', blk)
            if not (mat and mnum):
                continue
            x, y, a = float(mat.group(1)), float(mat.group(2)), float(mat.group(3))
            self.pins[mnum.group(1)] = dict(x=x, y=y, angle=a,
                                             name=mname.group(1) if mname else "",
                                             etype=etype)

    def lib_id(self):
        return f"{self.lib_nickname}:{self.name}"

    def cache_text(self, base_sym=None):
        """Return the embeddable lib_symbols entry text, with the top-level name
        prefixed 'lib_nickname:Name' (nested unit sub-symbols keep their short,
        unprefixed form).

        If this symbol `extends` a base (e.g. MAX3232 extends MAX232), kicad-cli's
        ERC does not reliably resolve pin connectivity through a hand-crafted
        `(extends ...)` reference in a schematic's cache -- so instead of embedding
        the short derived-only block + extends reference, flatten: splice the
        base's own unit sub-symbols (graphics + pins, renamed to the derived name)
        directly into the derived symbol's entry, and drop the extends reference
        entirely. This produces a fully self-contained symbol, which is what
        matters for a valid, ERC-clean schematic (a real KiCad save from the GUI
        would re-resolve this properly anyway)."""
        blocks = find_blocks(self.text, "symbol")
        idx, blk = blocks[0]
        blk = blk.replace(f'(symbol "{self.name}"', f'(symbol "{self.lib_nickname}:{self.name}"', 1)

        if base_sym:
            # drop the (extends "...") line
            blk = re.sub(r'\s*\(extends "[^"]+"\)', '', blk, count=1)
            base_blocks = find_blocks(base_sym.text, "symbol")
            base_top_idx, base_top = base_blocks[0]
            # the base's nested unit sub-symbols are the (symbol "Base_N_M" ...) blocks
            # directly inside its top-level block
            unit_blocks = find_nested_blocks(base_top, "symbol")
            renamed_units = [
                re.sub(rf'^\(symbol "{re.escape(base_sym.name)}(_\d+_\d+)"',
                       rf'(symbol "{self.name}\1"', ub)
                for ub in unit_blocks
            ]
            # splice the renamed unit blocks in just before the derived block's
            # closing paren (right before the trailing "(embedded_fonts no)\n\t)")
            insert_at = blk.rfind('(embedded_fonts')
            blk = blk[:insert_at] + "\n".join(renamed_units) + "\n\t\t" + blk[insert_at:]

        return blk


def load(filename, nickname):
    return SymbolDef(filename, nickname)


ROT = {0: (1,0,0,1), 90: (0,-1,1,0), 180: (-1,0,0,-1), 270: (0,1,-1,0)}

def transform(px, py, pa, cx, cy, rot):
    # Symbol library pin coordinates are authored in a Y-up convention; schematic
    # placement is Y-down. Flip Y (and the pin's direction angle) first, then apply
    # the instance's placement rotation in schematic (Y-down) space.
    py = -py
    pa = (-pa) % 360
    a,b,c,d = ROT[rot]
    nx = a*px + b*py
    ny = c*px + d*py
    na = (pa + rot) % 360
    return cx+nx, cy+ny, na


class Component:
    def __init__(self, sym: SymbolDef, ref, value, footprint, x, y, rot=0, base_sym=None):
        self.sym = sym
        self.base_sym = base_sym
        self.ref = ref
        self.value = value
        self.footprint = footprint
        GRID = 1.27
        self.x = round(round(x / GRID) * GRID, 2)
        self.y = round(round(y / GRID) * GRID, 2)
        self.rot = rot
        self.uuid = u()
        self.nets = {}      # pin_number -> net name (str) or None(leave as-is / already handled)
        self.nc = set()     # pin_numbers explicitly marked no-connect
        self.power = {}     # pin_number -> power symbol lib_id e.g. "power:+5V" (name shown)

    def pin(self, number, net=None, nc=False, power=None):
        """power, if given, is a SymbolDef for a single-pin power symbol (e.g. GND, +5V)."""
        if power:
            self.power[str(number)] = power
        elif nc:
            self.nc.add(str(number))
        elif net:
            self.nets[str(number)] = net
        return self

    def pins_source(self):
        return self.base_sym.pins if self.base_sym else self.sym.pins

    def pin_unit(self):
        return self.base_sym.pin_unit if self.base_sym else self.sym.pin_unit


class Sheet:
    def __init__(self, title, paper="A3"):
        self.title = title
        self.paper = paper
        self.components = []
        self.symdefs = {}   # lib_id -> (SymbolDef, base_or_None)

    def add(self, comp: Component):
        self.components.append(comp)
        self.symdefs[comp.sym.lib_id()] = (comp.sym, comp.base_sym)
        for psym in comp.power.values():
            self.symdefs[psym.lib_id()] = (psym, None)
        return comp

    def render(self):
        lib_symbols = []
        for lib_id, (sym, base) in self.symdefs.items():
            lib_symbols.append(sym.cache_text(base_sym=base))
        lib_symbols_text = "\n".join(lib_symbols)

        body = []
        for comp in self.components:
            body.append(self._render_component(comp))

        return f'''(kicad_sch (version 20211123) (generator eeschema)
  (uuid "{u()}")
  (paper "{self.paper}")
  (title_block
    (title "{self.title}")
    (date "2026-10-09")
    (rev "A")
    (company "CS1800 Project")
  )
  (lib_symbols
{lib_symbols_text}
  )
{"".join(body)}
)
'''

    def _render_component(self, comp: Component):
        out = []
        out.append(f'  (symbol (lib_id "{comp.sym.lib_id()}") (at {comp.x} {comp.y} {comp.rot}) '
                    f'(unit {comp.pin_unit()}) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) '
                    f'(uuid "{comp.uuid}")')
        out.append(f'    (property "Reference" "{comp.ref}" (at {comp.x} {comp.y-6} 0) (effects (font (size 1.27 1.27))))')
        out.append(f'    (property "Value" "{comp.value}" (at {comp.x} {comp.y-4} 0) (effects (font (size 1.27 1.27))))')
        out.append(f'    (property "Footprint" "{comp.footprint}" (at {comp.x} {comp.y} 0) (effects (font (size 1.27 1.27)) hide))')
        pins = comp.pins_source()
        for num in pins:
            out.append(f'    (pin "{num}" (uuid "{u()}"))')
        out.append('  )')
        wires_labels = []
        STUB = 2.54
        for num, pdata in pins.items():
            ax, ay, aangle = transform(pdata['x'], pdata['y'], pdata['angle'], comp.x, comp.y, comp.rot)
            ax, ay = round(ax, 3), round(ay, 3)
            out_dir = int(round((aangle + 180) % 360))
            rad = math.radians(out_dir)
            ex, ey = round(ax + STUB*math.cos(rad), 3), round(ay + STUB*math.sin(rad), 3)
            if num in comp.nc:
                wires_labels.append(f'  (no_connect (at {ax} {ay}) (uuid "{u()}"))')
                continue
            net = comp.nets.get(num)
            powersym = comp.power.get(num)
            if not net and not powersym:
                continue
            # Coincident pins with no wire between them are NOT considered connected by
            # KiCad's ERC -- a wire segment is required even when the two points are at
            # the exact same coordinate. So always draw the stub wire.
            wires_labels.append(f'  (wire (pts (xy {ax} {ay}) (xy {ex} {ey})) (stroke (width 0) (type default)) (uuid "{u()}"))')
            if powersym:
                wires_labels.append(_power_symbol_text(powersym, ex, ey))
            else:
                wires_labels.append(
                    f'  (global_label "{net}" (shape input) (at {ex} {ey} {out_dir}) '
                    f'(effects (font (size 1.27 1.27))) (uuid "{u()}"))'
                )
        return "\n".join(out) + "\n" + "\n".join(wires_labels) + "\n"


def _power_symbol_text(psym: SymbolDef, x, y):
    return (f'  (symbol (lib_id "{psym.lib_id()}") (at {x} {y} 0) (unit 1) '
            f'(exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) (uuid "{u()}")\n'
            f'    (property "Reference" "#PWR" (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide))\n'
            f'    (property "Value" "{psym.name}" (at {x} {y-2.54} 0) (effects (font (size 1.27 1.27))))\n'
            f'    (pin "1" (uuid "{uuid.uuid4()}"))\n'
            f'  )')
