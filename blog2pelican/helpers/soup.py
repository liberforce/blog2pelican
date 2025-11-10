import sys


def import_bs4():
    """Import and return bs4, otherwise sys.exit."""
    try:
        import bs4  # noqa: PLC0415
    except ImportError:
        error = (
            'Missing dependency "BeautifulSoup4" and "lxml" required to '
            "import XML files."
        )
        sys.exit(error)
    return bs4


def file_to_soup(xml, features="xml"):
    """Reads a file, returns soup."""
    bs4 = import_bs4()
    with open(xml, encoding="utf-8") as infile:
        xmlfile = infile.read()
    soup = bs4.BeautifulSoup(xmlfile, features)
    return soup
