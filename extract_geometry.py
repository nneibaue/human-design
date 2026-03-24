#!/usr/bin/env python3
"""Extract bodygraph geometry from bg_example.html template."""

import re
from pathlib import Path

template = Path("bg_example.html").read_text()

# Extract viewBox
viewbox_match = re.search(r'viewBox="([^"]+)"', template)
if viewbox_match:
    print(f"viewBox: {viewbox_match.group(1)}")

# Extract center positions and shapes
center_pattern = r'<g id="center_(\d+)_white"[^>]*>.*?(?:<path d="([^"]+)"|<rect[^>]*x="([\d.]+)" y="([\d.]+)"[^>]*width="([\d.]+)" height="([\d.]+)")'

centers = {}
for match in re.finditer(center_pattern, template, re.DOTALL):
    center_id = match.group(1)
    if match.group(2):  # path
        print(f"Center {center_id}: path (triangle/diamond)")
    else:  # rect
        x, y, width, height = match.group(3), match.group(4), match.group(5), match.group(6)
        print(f"Center {center_id}: rect at ({x}, {y}) size {width}x{height}")

# Extract gate elements
gate_pattern = r'<g id="gate(\d+)"[^>]*transform="([^"]+)"[^>]*>.*?<rect[^>]*x="([\d.]+)" y="([\d.]+)"'

gates = {}
for match in re.finditer(gate_pattern, template, re.DOTALL):
    gate_num = match.group(1)
    transform = match.group(2)
    x, y = match.group(3), match.group(4)
    gates[gate_num] = {"transform": transform, "x": x, "y": y}

print(f"\nFound {len(gates)} gates")
print(f"Gate 1: {gates.get('1')}")
print(f"Gate 10: {gates.get('10')}")
print(f"Gate 57: {gates.get('57')}")
