import random
import logging

from ymaps import DownloaderInterface, DownloadPolicyInterface


logger = logging.getLogger('ymaps')


class DownloadSimpleScheduler():

    def __init__(self, objects: list, downloader: DownloaderInterface):
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

    def __init__(self, objects: list, downloader: DownloaderInterface, policy: DownloadPolicyInterface):
        self.objects = objects
        self.downloader = downloader
        self.policy = policy

    def get_next_chunk(self):
        size, time_to_sleep = random.randint(100, 200), random.randint(5, 10)
        logger.info(f"Chunk size = {size}, time_to_sleep = {time_to_sleep}")
        return size, time_to_sleep

    def download(self):
        logger.warning(f"Started to download {len(self.objects)} objects")

        if len(self.objects) == 0:
            logger.warning(f"Nothing to download: the map is empty")
            return

        chunk_size, time_to_sleep = self.get_next_chunk()
        tiles_in_chunk = 0

        for obj in self.objects:

            destination = obj.destination()

            logger.info(f"Downloading {obj}")
            download_policy = self.policy(obj)

            if download_policy.before_download():
                result = self.downloader().download(obj.url(), destination)
                logger.info(f"Download result: {result}")
                download_policy.after_download(result)
            else:
                logger.info(f"Skipping {obj} because of the policy")
