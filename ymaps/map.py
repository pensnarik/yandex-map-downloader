import math
import logging

from collections import namedtuple

from ymaps.tile import Tile
from ymaps.downloaders import RequestsDownloader

logger = logging.getLogger('ymaps')

Coordinate = namedtuple('Coordinate', 'lat lon')
Borders = namedtuple('Borders', 'coord1 coord2')


def to_pixels(coord, zoom):
    l = 2 * math.pi * 6378137.0
    d = l / 2.0
    h = 1.0 / l
    b = math.pow(2, zoom + 8) * h
    return (d - coord) * b


def coordinate_to_tiles(coordinate, zoom):
    tileSize = 256

    # Ellipsoid, WGS84, f = 298.257...
    a = 6378137.0
    b = 6356752.3142
    f = (a - b) / a
    e = math.sqrt(2*f - f**2) # В combine.js = .0818191908426

    rLat = math.radians(coordinate.lat)
    rLong = math.radians(coordinate.lon)

    tx = (coordinate.lon + 180.0) / 360.0 * (1 << zoom)
    # Google
    # y = (1.0 - math.log(math.tan(rLat) + 1.0 / math.cos(rLat)) / math.pi) / 2.0 * (1 << zoom)
    M = math.tan(math.pi / 4 + rLat / 2) / math.pow(math.tan(math.pi / 4 + math.asin(e * math.sin(rLat)) / 2), e)
    y = a * math.log(M)

    yp = to_pixels(y, zoom)
    # Pixels to tile
    ty = int(math.floor(yp / float(tileSize)))
    return (math.trunc(tx), math.trunc(ty))


class Map():

    tiles = []

    def __init__(self, borders: Borders, z: int, layer: str, version: str):
        self.z = z
        self.x1, self.y1 = coordinate_to_tiles(borders.coord1, z)
        self.x2, self.y2 = coordinate_to_tiles(borders.coord2, z)
        self.downloader = RequestsDownloader()
        self.version = version
        self.layer = layer

        logger.info(f"Map.__init__(): {self.x1=}, {self.y1=}, {self.x2=}, {self.y2=}")

        for x in range(self.x1, self.x2):
            for y in range(self.y1, self.y2):
                self.tiles.append(Tile(x, y, self.z, self.layer, self.version))

    def __len__(self):
        return len(self.tiles)

    def download(self):
        d = self.download_scheduler(self.tiles, self.downloader)
        d.download()
        del d
