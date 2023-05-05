import os
import time
import random
import shutil
import logging
import requests
import signal

from enum import Enum
from urllib3.exceptions import ProtocolError
from ymaps.timeout import TimeoutError

logger = logging.getLogger('ymaps')


class DownloadResultEnum(Enum):
    DOWNLOADED = 1
    ERROR = 2
    EXISTS = 3

class DownloadResult():

    def __init__(self, result: DownloadResultEnum, code: str=None):
        self.__result = result
        self.__code = code

    def is_retriable(self):
        return self.__result == DownloadResultEnum.ERROR and \
               self.__code in ['400', 'timeout', 'connection_error']

    def need_to_sleep(self):
        return self.__result == DownloadResultEnum.DOWNLOADED

    def is_success(self):
        return self.__result == DownloadResultEnum.DOWNLOADED

    @classmethod
    def fromstr(cls, s: str):
        if ',' not in s:
            return cls(DownloadResultEnum[s])
        else:
            return cls(DownloadResultEnum[s.split(',')[0]], s.split(',')[1])

    def __str__(self):
        if self.__code:
            return f"{self.__result.name},{self.__code}"
        else:
            return f"{self.__result.name}"

    def __repr__(self):
        return self.__str__()


# Downloader interface
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
        size, time_to_sleep = random.randint(100, 200), random.randint(5, 10)
        logger.info(f"Chunk size = {size}, time_to_sleep = {time_to_sleep}")
        return size, time_to_sleep

    def download(self):
        logger.warning(f"Started to download {len(self.objects)} objects")

        if len(self.objects) == 0:
            return

        chunk_size, time_to_sleep = self.get_next_chunk()
        tiles_in_chunk = 0

        # FIXME: Currently we assume that all objects are in the same path!
        if not os.path.isdir(os.path.dirname(self.objects[0].destination())):
            os.makedirs(os.path.dirname(self.objects[0].destination()))

        for obj in self.objects:

            destination = obj.destination()

            if not os.path.exists(destination):
                logger.info(f"Downloading {obj}")
                res = self.downloader.download(obj.url(), destination)
                logger.info(f"Download result: {res}")
                if res.is_success():
                    tiles_in_chunk += 1
                    if tiles_in_chunk > chunk_size:
                        chunk_size, time_to_sleep = self.get_next_chunk()
                        time.sleep(time_to_sleep)
                        tiles_in_chunk = 0
                else:
                    with open(f"{destination}.error", "w") as f:
                        f.write(str(res))
            else:
                logger.info(f"Object {obj} exists, skipping")


class RequestsDownloader(Downloader):

    def __init__(self):
        self.headers = {
            'Authority': 'core-sat.maps.yandex.net',
            'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
            'Accept-language': 'en-US,en;q=0.9',
            'Referer': 'https://yandex.ru/maps/213/moscow/hybrid/?ll=37.618045%2C55.753260&z=20',
            'Sec-ch-ua': '"Not:A-Brand";v="99", "Chromium";v="112"',
            'Sec-ch-ua-mobile': '?0',
            'Sec-ch-ua-platform': '"Linux"',
            'Sec-fetch-dest': 'image',
            'Sec-fetch-mode': 'no-cors',
            'Sec-fetch-site': 'cross-site',
            'Cache-Control': 'no-cache',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36'
        }


    def download(self, url, destination):
        def timeout_handler(signum, frame):
            raise TimeoutError

        req = requests.Request('GET', url, headers=self.headers)
        s = requests.Session()
        r = req.prepare()

        error_code = None
        old = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(15)

        try:
            response = s.send(r, stream=True)

            if response.status_code == 200:
                with open(destination, "wb") as f:
                    response.raw.decode_content = True
                    try:
                        shutil.copyfileobj(response.raw, f)
                    except ProtocolError as e:
                        logger.error(f"Could not download {url}: {e}")
                        return DownloadResult(DownloadResultEnum.ERROR, 'protocol_error')
            else:
                return DownloadResult(DownloadResultEnum.ERROR, str(response.status_code))

        except requests.exceptions.ConnectionError as e:
            return DownloadResult(DownloadResultEnum.ERROR, 'connection_error')
        except TimeoutError:
            return DownloadResult(DownloadResultEnum.ERROR, 'timeout')
        finally:
            # reinstall the old signal handler
            signal.signal(signal.SIGALRM, old)
            # cancel the alarm
            # this line should be inside the "finally" block (per Sam Kortchmar)
            signal.alarm(0)

        return DownloadResult(DownloadResultEnum.DOWNLOADED)
