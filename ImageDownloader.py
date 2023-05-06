#   Copyright 2023 hidenorly
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import argparse
import os
import random
import requests
import string
import random
from PIL import Image
from io import BytesIO
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.common.by import By

class WebPageImageDownloader:
    def getRandomFilename():
        letters = string.ascii_lowercase
        return ''.join(random.choice(letters) for i in range(10))

    def getImageSize(data):
        try:
            with Image.open(BytesIO(data)) as img:
                return img.size
        except Exception:
            return None

    def downloadImage(imageUrl, outputPath, minDownloadSize=None):
        response = requests.get(imageUrl)
        if response.status_code == 200:
            # check image size
            size = WebPageImageDownloader.getImageSize(response.content)

            if minDownloadSize==None or (size and size[0] >= minDownloadSize[0] and size[1] >= minDownloadSize[1]):
                filename = os.path.join(outputPath, os.path.basename(imageUrl))
                f = None
                try:
                    f = open(filename, 'wb')
                except:
                    filename = os.path.join(outputPath, WebPageImageDownloader.getRandomFilename())
                    f = open(filename, 'wb')
                if f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

    def downloadImagesFromWebPage(url, outputPath, minDownloadSize=None):
        driver = webdriver.Chrome()
        driver.get(url)
        for img_tag in driver.find_elements(By.TAG_NAME, 'img'):
            imageUrl = img_tag.get_attribute('src')
            if imageUrl:
                imageUrl = urljoin(url, imageUrl)
                WebPageImageDownloader.downloadImage(imageUrl, outputPath, minDownloadSize)
        driver.quit()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Download images from web pages')
    parser.add_argument('pages', metavar='PAGE', type=str, nargs='+',
                        help='Web pages to download images from')
    parser.add_argument('-o', '--output', dest='outputPath', type=str, default='.',
                        help='Output folder')
    parser.add_argument('--minSize', type=str,
                        help='Minimum size of images to download (format: WIDTHxHEIGHT)')
    args = parser.parse_args()

    minDownloadSize = None
    if args.minSize:
        minDownloadSize = tuple(map(int, args.minSize.split('x')))

    if not os.path.exists(args.outputPath):
        os.makedirs(args.outputPath)

    for page in args.pages:
        WebPageImageDownloader.downloadImagesFromWebPage(page, args.outputPath, minDownloadSize)
