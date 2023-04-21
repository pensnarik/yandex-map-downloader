import os
import logging

logger = logging.getLogger('ymaps')



class DownloadableInterface():

    def url(self):
        raise NotImplementedError

    def destination():
        raise NotImplementedError


class Tile(DownloadableInterface):

    def __init__(self, x: int, y: int, z: int, layer: str, version: str):
        self.x = x
        self.y = y
        self.z = z
        self.layer = layer
        self.version = version

    def url(self):
        if self.layer == 'sat':
            return f"https://core-sat.maps.yandex.net/tiles?l=sat&" \
                   f"v={self.version}&x={self.x}&y={self.y}&z={self.z}&scale=1&lang=ru_RU"
        else:
            raise NotImplementedError(f"Unknown layer: {self.layer}")

    def destination(self):
        return os.path.join('moscow-tiles', str(self.z), f'{self.x}-{self.y}.jpg')

    def __str__(self):
        return f"{self.x},{self.y},{self.z}@{self.layer}"
