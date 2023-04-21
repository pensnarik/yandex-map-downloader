import os
import time
import random
import shutil
import logging
import requests

from enum import Enum

logger = logging.getLogger('ymaps')


class DownloadResult():
    DOWNLOADED = 1
    ERROR = 2
    EXISTS = 3


class Downloader():

    def download(self):
        raise NotImplementedError


class DownloadSimpleScheduler():

    def __init__(self, objects: list, downloader: Downloader):
        self.objects = objects
        self.downloader = downloader

    def download(self):
        for obj in self.objects:
            if not os.path.exists(obj.destination()):
                logger.info(f"Downloading {obj}")
                self.downloader.download(obj.url(), obj.destination())
            else:
                logger.info(f"Object {obj} exists, skipping")


class DownloadSleepScheduler():

    def __init__(self, objects: list, downloader: Downloader):
        self.objects = objects
        self.downloader = downloader

    def get_next_chunk(self):
        return random.randint(50, 100), random.randint(5, 10)

    def download(self):
        logger.info(f"Started to download {len(self.objects)} objects")

        chunk_size, time_to_sleep = self.get_next_chunk()
        tiles_in_chunk = 0

        for obj in self.objects:

            if not os.path.exists(obj.destination()):
                logger.info(f"Downloading {obj}")
                res = self.downloader.download(obj.url(), obj.destination())
                if res == DownloadResult.DOWNLOADED:
                    tiles_in_chunk += 1
                    if tiles_in_chunk > chunk_size:
                        chunk_size, time_to_sleep = self.get_next_chunk()
                        logger.info(f"Sleeping for {time_to_sleep} seconds, next chunk size is {chunk_size}")
                        time.sleep(time_to_sleep)
                        tiles_in_chunk = 0
            else:
                logger.info(f"Object {obj} exists, skipping")


class RequestsDownloader(Downloader):

    def __init__(self):
        self.headers = {
            'Authority': 'core-sat.maps.yandex.net',
            'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
            'Accept-language': 'en-US,en;q=0.9',
            'If-none-match': '"1029"',
            'Referer': 'https://yandex.ru/maps/213/moscow/hybrid/?ll=37.618045%2C55.753260&z=20',
            'Sec-ch-ua': '"Not:A-Brand";v="99", "Chromium";v="112"',
            'Sec-ch-ua-mobile': '?0',
            'Sec-ch-ua-platform': '"Linux"',
            'Sec-fetch-dest': 'image',
            'Sec-fetch-mode': 'no-cors',
            'Sec-fetch-site': 'cross-site',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36'
        }


    def download(self, url, destination):
        if not os.path.isdir(os.path.dirname(destination)):
            os.makedirs(os.path.dirname(destination))

        if os.path.exists(destination):
            return DownloadResult.EXISTS

        req = requests.Request('GET', url, headers=self.headers)
        s = requests.Session()
        r = req.prepare()

        try:
            response = s.send(r, stream=True)
        except requests.exceptions.ConnectionError as e:
            return DownloadResult.ERROR
        if response.status_code == 200:
            with open(destination, "wb") as f:
                response.raw.decode_content = True
                shutil.copyfileobj(response.raw, f)
            return DownloadResult.DOWNLOADED
        else:
            return DownloadResult.ERROR
