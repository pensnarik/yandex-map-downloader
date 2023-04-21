import os
import logging

from enum import Enum

logger = logging.getLogger('ymaps')

class TileStatus(Enum):
    DOWNLOADED = 1
    NOT_FOUND = 2
    QUEUED = 3
    ERROR = 4


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

    def status(self):
        if os.path.exists(self.destination()):
            return TileStatus.DOWNLOADED

        if os.path.exists(f'{self.destination()}.error'):
            with open(f'{self.destination()}.error') as f:
                code = f.read()
            if code == '404':
                return TileStatus.NOT_FOUND
            else:
                return TileStatus.ERROR

        return TileStatus.QUEUED


    def render(self):
        render_mapping = {
            TileStatus.QUEUED: "white",
            TileStatus.NOT_FOUND: "gray",
            TileStatus.DOWNLOADED: "green",
            TileStatus.ERROR: "red"
        }
        return render_mapping[self.status()]


    def __str__(self):
        return f"{self.x},{self.y},{self.z}@{self.layer}"
