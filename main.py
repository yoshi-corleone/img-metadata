import os
import glob
import requests
from bs4 import BeautifulSoup
from jpeg import Jpeg
from png import Png


def scraping():
    images = []
    url = "https://pycon.jp/2017/ja/sponsors/"
    res = requests.get(url)
    content = res.content
    soup = BeautifulSoup(content, 'html.parser')
    for link in soup.find_all("img"):
        if link.get("src").endswith(".jpg") or link.get("src").endswith(".png"):
            path = link.get("src")
            if not path.startswith("http"):
                path = "https://pycon.jp" + path
            images.append(path)
    for target in images:
        re = requests.get(target)
        with open("img/" + target.split("/")[-1], "wb") as f:
            f.write(re.content)


def parse_image():
    if not os.path.exists("img"):
        print("images directory not found")
        return

    children = glob.glob("img/*")
    files = [os.path.abspath(child) for child in children]

    jpeg_parser = Jpeg()
    png_parser = Png()
    parsers = [jpeg_parser, png_parser]

    for file in files:
        data = open(file, "rb").read()
        for parser in parsers:
            if parser.can_parse(data):
                result = parser.parse(data)
                print(result)


if __name__ == '__main__':
    # scraping()
    parse_image()
