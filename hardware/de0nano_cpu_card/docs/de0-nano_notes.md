Mechanical notes on the Terasic DE0-nano board


CAD data: https://grabcad.com/library/altera-de0-nano-1

Terasic does not publish an official fully dimensioned 2D engineering drawing in the standard user manual, 
these specific placements are usually derived from open-source hardware designs, community-tested 3D models, and the standard pin pitches. 

The structural and placement specifications needed to build an adapter PCB or precision enclosure for the Terasic DE0-Nano (Cyclone IV version) are detailed below:

Header Specifications & Placements
The board uses two 40-pin (2x20) male expansion headers (GPIO-0 and GPIO-1) 
positioned along the two long parallel edges of the top side of the board. 

    Pin Pitch: Standard 2.54 mm (0.1 inch) center-to-center spacing between pins.
    Row Spacing: Within each 2x20 header, the spacing between row A and row B is 2.54 mm (0.1 inch).
    Header-to-Header Spacing (Width): The outer edges of the two 40-pin headers are positioned precisely to standard grid alignments. 
    Measured center-to-center from the innermost rows of GPIO-0 to GPIO-1, the spacing is 40.64 mm (1.6 inches).
    Offset from Board Edges: The headers are inset by roughly 1.64 mm from the outer 49 mm width edges.

Mounting Hole Information
The DE0-Nano ships with a clear plastic plexiglass dust shield attached by pre-installed screws and standoffs. 

    Hole Diameter / Screw Size: The board features M3 screw holes. factory-supplied brass standoffs and screws use a standard metric M3 thread. 

Hole Pattern Layout: The four mounting holes are arranged in a perfect rectangle inset from the board's outer edges.
Hole-to-Hole Distance (Length): 68.2 mm center-to-center along the long axis (75.2 mm outer dimension minus a 3.5 mm inset on each side).
Hole-to-Hole Distance (Width): 42.0 mm center-to-center along the short axis (49 mm outer dimension minus a 3.5 mm inset on each side).
