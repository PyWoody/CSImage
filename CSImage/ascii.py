import shutil
import time
import zlib

from io import BytesIO
from PIL import Image
from rich.align import Align
from rich.live import Live
from rich.table import Table

from search import process


def main(cwd):
    processed, matches = 0, 0
    with Live(generate_table(), refresh_per_second=4, screen=True) as live:
        for is_match, fpath, mem in process(cwd):
            height, width = shutil.get_terminal_size()
            height -= 50
            if is_match:
                matches += 1
                height = height // 2
                width = width // 2
            processed += 1
            if img := convert(mem, term_width=width, term_height=height):
                live.update(
                    generate_table(
                        img=img,
                        processed=processed,
                        matches=matches,
                        is_match=is_match
                    )
                )
                if is_match:
                    time.sleep(.2)

def generate_table(*, img=None, processed=None, matches=None, is_match=None):
    if img is None:
        return
    match_table = Table(show_header=False, show_footer=False, expand=True)
    if is_match:
        match_table.add_column()
        match_table.add_column()
        match_table.add_row(img, img)
    else:
        match_table.add_column()
        match_table.add_row(img)
    status = f'Processed: {processed} | Matches: {matches}    '
    table = Table(show_header=False, show_footer=False, expand=True)
    table.add_column()
    table.add_row(Align.center(match_table))
    table.add_row(Align.right(status))
    return table

def convert(mem, term_width, term_height):
    img = Image.open(BytesIO(zlib.decompress(mem))).convert('L')  # Greyscale
    width, height = img.size
    aspect_ratio = height / width
    if width > term_width:
        if (new_width := int(aspect_ratio * term_height * 0.55)) > 1:
            width = new_width
    if height > term_height:
        if (new_height := int(aspect_ratio * term_width * 0.55)) > 1:
            height = new_height
    img = img.resize((width, height))
    pixels = img.getdata()
    chars = ['B', 'S', '#', '&', '@', '$', '%', '*', '!', ':', '.']
    new_pixels = ''.join([chars[pixel // 25] for pixel in pixels])
    new_pixels_count = len(new_pixels)
    ascii_image = '\n'.join(
        [
            new_pixels[index:index + width]
            for index in range(0, new_pixels_count, width)
        ]
    )
    return ascii_image


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('cwd')
    args = parser.parse_args()
    main(args.cwd)
