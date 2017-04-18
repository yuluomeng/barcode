from PIL import Image

from scan import UPC


IMG_TO_BARCODE = {
    '1.png': '123456789012',
    '1_stretched.png': '123456789012'
}


if __name__ == '__main__':

    for filename, expected in IMG_TO_BARCODE.items():
        img = Image.open('imgs/%s' % filename).convert('1')
        barcode = UPC(img).scan()

        print('Actual Barcode: %s, Expected Barcode: %s, Match: %s' % (
            barcode, expected, barcode == expected))
