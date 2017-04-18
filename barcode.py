
import requests


GOOGLE_BOOKS_URL = 'https://www.googleapis.com/books/v1/volumes?q=isbn:%s'


def find_author_and_title(isbn):
    """Find the book that the isbn identifies."""

    resp = requests.get(GOOGLE_BOOKS_URL % isbn).json()
    metadata = resp['items'][0]['volumeInfo']

    author = ' & '.join(metadata['authors'])
    title = ' '.join([metadata['title'], metadata['subtitle']])

    return title, author


if __name__ == '__main__':
    title, author = find_author_and_title('0399594493')

    print('"%s" by %s' % (title, author))
