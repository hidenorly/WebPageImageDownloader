#   Copyright 2023 hidenorly
#
#   Licensed baseUrl the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed baseUrl the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations baseUrl the License.

import argparse
import os
import random
import requests
import string
import random
import time
from PIL import Image
from io import BytesIO
from urllib.parse import urljoin
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException


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

    def isSameDomain(url1, url2, baseUrl=""):
        isSame = urlparse(url1).netloc == urlparse(url2).netloc
        isbaseUrl =  ( (baseUrl=="") or url2.startswith(baseUrl) )
        return isSame and isbaseUrl

    def downloadImagesFromWebPage_(driver, pagesUrls, pageUrl, outputPath, minDownloadSize=None, baseUrl="", maxDepth=1, depth=0):
        if depth > maxDepth:
            return

        driver.get(pageUrl)
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, 'img'))
        )
        # download image
        for img_tag in driver.find_elements(By.TAG_NAME, 'img'):
            imageUrl = img_tag.get_attribute('src')
            if imageUrl:
                imageUrl = urljoin(pageUrl, imageUrl)
                WebPageImageDownloader.downloadImage(imageUrl, outputPath, minDownloadSize)

        # get links to other pages
        elements = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.TAG_NAME, 'a'))
        )
        for element in elements:
            try:
                href = element.get_attribute('href')
                if href and WebPageImageDownloader.isSameDomain(pageUrl, href, baseUrl):
                    oldLen= len(pagesUrls)
                    pagesUrls.add(href)
                    if len(pagesUrls)>oldLen:
                        if href.endswith(".jpg") or href.endswith(".jpeg") or href.endswith(".png"):
                            WebPageImageDownloader.downloadImage(href, outputPath, minDownloadSize)
                        else:
                            WebPageImageDownloader.downloadImagesFromWebPage_(driver, pagesUrls, href, outputPath, minDownloadSize, baseUrl, maxDepth, depth + 1)
            except StaleElementReferenceException:
                continue

    def downloadImagesFromWebPage(url, outputPath, minDownloadSize=None, baseUrl="", maxDepth=1):
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        driver = webdriver.Chrome(options=options)
        driver.set_window_size(1920, 1080)

        pagesUrls=set()
        WebPageImageDownloader.downloadImagesFromWebPage_(driver, pagesUrls, url, outputPath, minDownloadSize, baseUrl, maxDepth)
        driver.quit()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Download images from web pages')
    parser.add_argument('pages', metavar='PAGE', type=str, nargs='+', help='Web pages to download images from')
    parser.add_argument('-o', '--output', dest='outputPath', type=str, default='.', help='Output folder')
    parser.add_argument('--minSize', type=str, help='Minimum size of images to download (format: WIDTHxHEIGHT)')
    parser.add_argument('--maxDepth', type=int, default=1, help='maximum depth of links to follow')
    parser.add_argument('--baseUrl', type=str, default="", help='Specify base url if you want to restrict download under the baseUrl')
    args = parser.parse_args()

    minDownloadSize = None
    if args.minSize:
        minDownloadSize = tuple(map(int, args.minSize.split('x')))

    if not os.path.exists(args.outputPath):
        os.makedirs(args.outputPath)

    for page in args.pages:
        WebPageImageDownloader.downloadImagesFromWebPage(page, args.outputPath, minDownloadSize, args.baseUrl, args.maxDepth)
