
import numpy as np
from PIL import Image, ImageFilter


def partition(l, n):
    return zip(*[iter(l)] * n)


class UPC(object):

    LOOKUP = {
        (3, 2, 1, 1): '0',
        (1, 1, 2, 3): '0',
        (2, 2, 2, 1): '1',
        (1, 2, 2, 2): '1',
        (2, 1, 2, 2): '2',
        (2, 2, 1, 2): '2',
        (1, 4, 1, 1): '3',
        (1, 1, 4, 1): '3',
        (1, 1, 3, 2): '4',
        (2, 3, 1, 1): '4',
        (1, 2, 3, 1): '5',
        (1, 3, 2, 1): '5',
        (1, 1, 1, 4): '6',
        (4, 1, 1, 1): '6',
        (1, 3, 1, 2): '7',
        (2, 1, 3, 1): '7',
        (1, 2, 1, 3): '8',
        (3, 1, 2, 1): '8',
        (3, 1, 1, 2): '9',
        (2, 1, 1, 3): '9',
    }

    ## Lowest shade for what we'll consider a white pixel
    WHITE_PIXEL_CUTOFF = 200

    ## proprotion of the the barcode bars compared to the size of the image.
    MIN_BAR_PROPORTION = 0.6
    MAX_BAR_PROPORTION = 0.95

    MIN_WIDTH = 640

    def __init__(self, img):
        self.img = img.resize(
            (max(img.width, self.MIN_WIDTH), img.height), Image.BICUBIC)
        self.img = self.img.filter(ImageFilter.UnsharpMask).convert('1')
        self.width, self.height = self.img.size
        self.short_bar_heights, self.tall_bar_heights = self.find_bar_heights()

    def scan(self):
        """Calculates the digits in the barcode"""

        barcode = []
        spacing = [w for group in self.calc_spacing() for w in group]
        (_, (_, b1, b2, b3, _)) = np.histogram(spacing, 4)

        for group in self.calc_spacing():
            normalized = []
            for width in group:
                if width <= b1:
                    normalized.append(1)
                elif width <= b2:
                    normalized.append(2)
                elif width <= b3:
                    normalized.append(3)
                else:
                    normalized.append(4)

            for part in partition(normalized, 4):
                barcode.append(self.LOOKUP.get(part, -1))

        return ''.join(barcode)

    def is_short_bar(self, col_idx):
        """Does this col_idx refer to a short bar in the barcode?"""

        col = self.extract_column(col_idx)
        col_height = self.bar_height(col)
        min_height, max_height = self.short_bar_heights

        return min_height <= col_height <= max_height

    def is_tall_bar(self, col_idx):
        """Does this col_idx refer to a tall bar in the barcode?"""

        col = self.extract_column(col_idx)
        col_height = self.bar_height(col)
        min_height, max_height = self.tall_bar_heights

        return min_height <= col_height <= max_height

    def calc_spacing(self):
        """Calculate the spacing between the short bars in the barcode

        The spacing between the bars determines how the barcode is translated
        """
        groups = []
        for i, (start, end) in enumerate(self.find_bounds()):
            is_white = True
            ## skip the first bar on the second group, since it's supposed to
            ## start with a black bar.
            widths = [start, ] if i == 0 else []
            for col_idx in range(start, end + 1):

                if self.is_short_bar(col_idx):
                    if is_white:
                        widths.append(col_idx)
                    is_white = False
                else:
                    if not is_white:
                        widths.append(col_idx)
                    is_white = True

            ## add the last bar in the second group, since we skipped the first
            ## bar.
            if i == 1:
                widths.append(end)

            groups.append(np.diff(widths))

        return groups

    def find_bounds(self):
        """Find the bounds of the two chunks of the barcode.

        :returns: two iterables of (start, end) - one for each chunk
        """
        inside_bounds = False
        start = 0

        for col_idx in range(self.width):
            if not inside_bounds and self.is_tall_bar(col_idx):
                inside_bounds = True
                if start > 0:
                    yield start, col_idx
                    start = 0
            elif (inside_bounds and
                    self.find_next_bar_idx(col_idx) and
                    not self.is_tall_bar(self.find_next_bar_idx(col_idx))):
                inside_bounds = False
                start = col_idx

    def find_next_bar_idx(self, col_idx):
        """Find the height of the next black bar in the barcode."""

        for idx in range(col_idx, self.width):
            col = self.extract_column(idx)
            if self.bar_height(col) > 0:
                return idx

        return None

    def find_bar_heights(self):
        """Find the range of tall and short heights of the bars in the barcode

        The tall height of the barcode is to break the barcode into two groups.
        The short height of the barcode is the actual height of the bars
        with information.
        """
        bar_heights = set()

        for col_idx in range(self.width):
            bar_height = self.bar_height(self.extract_column(col_idx))

            if bar_height == 0:
                continue

            bar_heights.add(bar_height)

        avg_height = np.mean(list(bar_heights))
        short_sorted = sorted([
            height for height in bar_heights if height < avg_height])
        tall_sorted = sorted([
            height for height in bar_heights if height > avg_height])

        return (
            (short_sorted[0], short_sorted[-1]),
            (tall_sorted[0], tall_sorted[-1]))

    def bar_height(self, col):
        """Calculates the height of the black bar in the column.

        Does so naively, by finding the first black pixel in the column,
        and counting the number of consecutive black pixels that come after.
        """
        height = 0
        found_black_pixel = False
        for color in col:
            if color > self.WHITE_PIXEL_CUTOFF and found_black_pixel:
                break

            if color > self.WHITE_PIXEL_CUTOFF:
                continue

            if not found_black_pixel:
                found_black_pixel = True

            height += 1

        ## crude box filter to remove bars that aren't part of the barcode.
        if (self.MIN_BAR_PROPORTION * self.height <
                height < self.MAX_BAR_PROPORTION * self.height):
            return height
        return 0

    def extract_column(self, col_num):
        return self.img.crop((col_num, 0, col_num + 1, self.height)).getdata()
