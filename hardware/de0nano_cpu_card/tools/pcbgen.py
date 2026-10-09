"""Netlist-driven .kicad_pcb footprint placer -- the PCB-side counterpart to
kicadgen.py. Parses a KiCad netlist (from `kicad-cli sch export netlist`)
for component->footprint/value and net->(ref,pin) connectivity, parses real
.kicad_mod footprint files for their pad sets, and places each component's
full footprint definition on a board with pads wired to the right net.

Much simpler than the schematic generator: PCB footprint pad coordinates are
already authored in the board's native (Y-down) space, no Y-flip needed, and
a footprint instance just embeds the library file's content near-verbatim
(no "Library:Name" prefixing the way schematic symbols needed).
"""
import re, uuid, os

FPSTAGE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fpstage")
CS1800_FP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                          "libraries", "footprints", "cs1800.pretty")


def u():
    return str(uuid.uuid4())


def balanced_block(text, start_idx):
    depth = 0
    i = start_idx
    in_str = False
    while i < len(text):
        c = text[i]
        if c == '"' and text[i - 1] != '\\':
            in_str = not in_str
        elif not in_str:
            if c == '(':
                depth += 1
            elif c == ')':
                depth -= 1
                if depth == 0:
                    return text[start_idx:i + 1]
        i += 1
    raise ValueError("unbalanced")


def find_blocks(text, tag):
    out = []
    i = 0
    pat = "(" + tag
    while True:
        idx = text.find(pat, i)
        if idx == -1:
            break
        nc = text[idx + len(pat)]
        if nc in (' ', '"', '\n', '\t'):
            blk = balanced_block(text, idx)
            out.append((idx, blk))
            i = idx + len(blk)
        else:
            i = idx + len(pat)
    return out


class Netlist:
    """Parses a kicad-cli `sch export netlist` output file."""
    def __init__(self, path):
        text = open(path).read()
        comp_section = text[text.index("(components"):text.index("(nets")]
        nets_section = text[text.index("(nets"):]

        self.footprint = {}   # ref -> lib_id string, e.g. "Device:R"
        self.value = {}       # ref -> value string
        entries = re.findall(
            r'\(comp\s*\(ref "([^"]+)"\)\s*\(value "([^"]*)"\)\s*\(footprint "([^"]*)"\)',
            comp_section)
        for ref, value, fp in entries:
            self.footprint[ref] = fp
            self.value[ref] = value

        # pin_net[ref][pin_number] = net_name
        self.pin_net = {}
        for net_idx, net_blk in find_blocks(nets_section, "net"):
            nm = re.search(r'\(name "([^"]*)"\)', net_blk)
            if not nm:
                continue
            net_name = nm.group(1)
            if net_name == "":
                continue
            for node_idx, node_blk in find_blocks(net_blk, "node"):
                rm = re.search(r'\(ref "([^"]+)"\)', node_blk)
                pm = re.search(r'\(pin "([^"]+)"\)', node_blk)
                if not (rm and pm):
                    continue
                ref, pin = rm.group(1), pm.group(1)
                self.pin_net.setdefault(ref, {})[pin] = net_name


class FootprintDef:
    _cache = {}

    def __init__(self, lib_id):
        """lib_id like 'Device:R' (stock, staged in fpstage/<BaseName>.kicad_mod)
        or 'cs1800:DIN41617_31P_Male_Angled' (project-local, in CS1800_FP/)."""
        self.lib_id = lib_id
        nick, name = lib_id.split(":", 1)
        if nick == "cs1800":
            path = os.path.join(CS1800_FP, f"{name}.kicad_mod")
        else:
            path = os.path.join(FPSTAGE, f"{name}.kicad_mod")
        self.text = open(path).read()
        m = re.search(r'\(footprint "([^"]+)"', self.text)
        self.name = m.group(1)
        self.pad_numbers = set(re.findall(r'\(pad "([^"]*)"', self.text))


def load_footprint(lib_id):
    if lib_id not in FootprintDef._cache:
        FootprintDef._cache[lib_id] = FootprintDef(lib_id)
    return FootprintDef._cache[lib_id]


class NetTable:
    """Assigns sequential net IDs to net names as they're first used."""
    def __init__(self):
        self.ids = {"": 0}
        self.next_id = 1

    def get(self, name):
        if name not in self.ids:
            self.ids[name] = self.next_id
            self.next_id += 1
        return self.ids[name]

    def declarations(self):
        items = sorted(self.ids.items(), key=lambda kv: kv[1])
        return "\n".join(f'  (net {nid} "{name}")' for name, nid in items)


def render_footprint_instance(ref, value, fpdef: FootprintDef, x, y, rot,
                               pin_net: dict, nettable: NetTable, locked=False):
    """pin_net: {pad_number: net_name} for this instance's connected pads
    (omit a pad number to leave it unconnected)."""
    text = fpdef.text

    # Replace the top-level (footprint "Name" ...) opening with our instance
    # placement. The library file's own (at ...) (if any) doesn't exist at
    # top level for .kicad_mod files (position is only set on placement).
    top_idx = text.index(f'(footprint "{fpdef.name}"')
    top_blk = balanced_block(text, top_idx)
    # insert (at X Y ROT) and (locked) right after the opening, before the
    # first existing child (e.g. (version ...) or (layer ...))
    insert_pos = top_idx + len(f'(footprint "{fpdef.name}"')
    locked_s = " locked" if locked else ""
    header = f'{locked_s}\n\t(layer "F.Cu")\n\t(uuid "{u()}")\n\t(at {x} {y} {rot})\n'
    body = top_blk[len(f'(footprint "{fpdef.name}"'):-1]  # strip wrapper, keep inner content
    # drop any pre-existing (layer ...) / (at ...) in body (library files have (layer "F.Cu") only, no (at))
    body = re.sub(r'\n\t\(layer "F\.Cu"\)', '', body, count=1)

    # Replace Reference/Value properties
    body = re.sub(r'\(property "Reference" "REF\*\*"', f'(property "Reference" "{ref}"', body, count=1)
    body = re.sub(r'\(property "Value" "[^"]*"', f'(property "Value" "{value}"', body, count=1)

    # Insert (net ID "NAME") into each connected pad, right before its closing paren
    for padnum, netname in pin_net.items():
        nid = nettable.get(netname)
        pad_pat = f'(pad "{padnum}" '
        idx = body.index(pad_pat)
        blk = balanced_block(body, idx)
        insert_at = idx + len(blk) - 1
        body = body[:insert_at] + f'\n\t\t(net {nid} "{netname}")\n\t' + body[insert_at:]

    return f'(footprint "{fpdef.name}"{header}{body})\n'
