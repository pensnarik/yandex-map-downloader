import os
import logging

from enum import Enum
from ymaps.downloaders import DownloadableInterface

logger = logging.getLogger('ymaps')

class TileStatus(Enum):
    DOWNLOADED = 1
    NOT_FOUND = 2
    QUEUED = 3
    ERROR = 4


class Tile(DownloadableInterface):

    def __init__(self, tile_map, x: int, y: int, z: int, layer: str, version: str='3.1064.0'):
        self.x = x
        self.y = y
        self.z = z
        self.layer = layer
        self.version = version
        self.tile_map = tile_map

    @classmethod
    def fromstr(cls, tile_map, s: str):
        x, y, z, layer = s.split(',')
        return cls(tile_map, x, y, z, layer)

    def url(self):
        if self.layer == 'sat':
            return f"https://core-sat.maps.yandex.net/tiles?l=sat&" \
                   f"v={self.version}&x={self.x}&y={self.y}&z={self.z}&scale=1&lang=ru_RU"
        else:
            raise NotImplementedError(f"Unknown layer: {self.layer}")

    def destination(self):
        if self.tile_map:
            path = self.tile_map.path()
        else:
            path = '.'

        return os.path.join(path, f'{self.x}-{self.y}.jpg')

    def status(self):
        if os.path.exists(self.destination()):
            return TileStatus.DOWNLOADED

        if os.path.exists(f'{self.destination()}.error'):
            with open(f'{self.destination()}.error') as f:
                code = f.read()
            if code == 'ERROR,404':
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
