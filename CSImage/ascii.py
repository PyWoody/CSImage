from PIL import Image


def main(image_path, new_width=0, new_height=0):
    if not any([new_width, new_height]):
        raise AttributeError('You must specify a width or height to rescale.')
    img = Image.open(image_path).convert('L')  # Greyscale


    width, height = img.size
    aspect_ratio = height / width

    if new_width:
        new_height = int(aspect_ratio * new_width * 0.55)  # .55?
    else:
        new_width = int(aspect_ratio * new_height * 0.55)  # .55?

    img = img.resize((new_width, new_height))

    pixels = img.getdata()

    chars = ['B', 'S', '#', '&', '@', '$', '%', '*', '!', ':', '.']
    # chars = ['*', 'S', '#', '&', '@', '$', '%', '*', '!', ':', '.']
    # chars = list("$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\|()1{}[]?-_+~<>i!lI;:,\"^`'. ")
    # chars = list(" .:-=+*#%@")
    new_pixels = ''.join([chars[pixel // 25] for pixel in pixels])

    new_pixels_count = len(new_pixels)
    ascii_image = '\n'.join(
        [
            new_pixels[index:index + new_width]
            for index in range(0, new_pixels_count, new_width)
        ]
    )
    return ascii_image



if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('image', nargs='?')
    args = parser.parse_args()
    img = args.image if args.image else r'/Users/sam/Projects/scripts/tmp/CSImage/test_dupe_proj_image.jpg'
    main(img)
