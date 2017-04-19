from PIL import Image

from scan import UPC


IMG_TO_BARCODE = {
    '1.png': '123456789012',
    '1_horizontal_stretch.png': '123456789012',
    '1_vertical_stretch.png': '123456789012',
    '1_shrunk.png': '123456789012',
    '2.png': '771234567003',
    '3.png': '671860013624'
}


if __name__ == '__main__':

    for filename, expected in IMG_TO_BARCODE.items():
        img = Image.open('imgs/%s' % filename)
        barcode = UPC(img).scan()

        print('Actual Barcode: %s, Expected Barcode: %s, Match: %s' % (
            barcode, expected, barcode == expected))
