import os
import time
import random
import shutil
import logging
import requests
import signal
import subprocess

from urllib3.exceptions import ProtocolError
from ymaps import (DownloadableInterface, DownloaderInterface, DownloadResultEnum,
                   DownloadPolicyInterface, DownloadResult)
from ymaps.timeout import TimeoutError
from ymaps.download_policy import CommonDownloadPolicy

logger = logging.getLogger('ymaps')


class CurlDownloader(DownloaderInterface):

    def __init__(self):
        pass

    def download(self, url, destination):
        result = subprocess.run(
            ['curl', '-s', '--output', destination, url], stdout=subprocess.PIPE
        )

        if result.returncode > 0:
            return DownloadResult(DownloadResultEnum.ERROR, 'curl_error')

        return DownloadResult(DownloadResultEnum.DOWNLOADED)


class RequestsDownloader(DownloaderInterface):

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

        logger.info(f"{url=}")
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
