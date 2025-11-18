
import os
from pathlib import Path
import colorsys

def get_color(index, total):
    # Generate distinct colors using HSV space and convert to RGB
    hue = index / total
    r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
    return round(r, 3), round(g, 3), round(b, 3)

def split_wrl_by_solid(input_file, output_dir):
    with open(input_file, 'r', encoding='utf-8', errors='ignore') as file:
        lines = file.readlines()

    solid_blocks = {}
    current_solid = None
    buffer = []

    for line in lines:
        if line.strip().startswith("#---------- SOLID:"):
            if current_solid and buffer:
                solid_blocks[current_solid] = buffer
                buffer = []
            current_solid = line.split(":")[1].split(":")[0].strip()
            buffer.append(line)
        elif current_solid:
            buffer.append(line)

    if current_solid and buffer:
        solid_blocks[current_solid] = buffer

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    total_solids = len(solid_blocks)
    for idx, (solid_name, content) in enumerate(solid_blocks.items()):
        r, g, b = get_color(idx, total_solids)
        colored_content = []
        for line in content:
            if "diffuseColor" in line:
                line = f'\t\t\t\tdiffuseColor {r} {g} {b}\n'
            colored_content.append(line)

        out_path = output_dir / f"{solid_name}.wrl"
        with out_path.open("w") as f:
            f.write("#VRML V2.0 utf8\n\n")
            f.writelines(colored_content)
        print(f"Written: {out_path} with color RGB({r}, {g}, {b})")

if __name__ == "__main__":
    import argparse
    import colorsys
    parser = argparse.ArgumentParser(description="Split a WRL file into separate files per solid with unique colors.")
    parser.add_argument("input_file", help="Path to the input .wrl file")
    parser.add_argument("output_dir", help="Directory to write individual solid files")
    args = parser.parse_args()

    split_wrl_by_solid(args.input_file, args.output_dir)
