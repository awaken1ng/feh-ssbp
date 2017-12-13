import os
from ssbp import SSBP
from PIL import Image


def split_cellmap(unit, ssbp):
    for cell_map_name in ssbp.cell_maps:
        cell_map = ssbp.cell_maps[cell_map_name]
        # Check if texture exists
        if os.path.exists(os.path.join(f'data/Unit/{unit}', cell_map['image path'])):
            # Create the output folders if it doesn't exist
            for path in ['output', f'output/{unit}', f'output/{unit}/tex']:
                if not os.path.exists(path):
                    os.mkdir(path)
            # Open the texture
            tex_im = Image.open(f"data/Unit/{unit}/{cell_map['image path']}")
            for cell in cell_map['cells']:
                # Cut out the part
                part = tex_im.crop(
                    cell['pos'] + (cell['size'][0] + cell['pos'][0],
                                   cell['size'][1] + cell['pos'][1])
                )
                # Save it
                part.save(f"output/{unit}/tex/{cell['name']}.png")

if __name__ == "__main__":
    unit = 'ch04_12_Tiki_F_Normal'
    split_cellmap(unit)
