#!/usr/bin/env python3

import os
import sys
import json
import logging
import argparse

from ymaps.download_policy import CommonDownloadPolicy
from ymaps.download_scheduler import DownloadSleepScheduler, DownloadSimpleScheduler
from ymaps.tile import Tile
from ymaps.map import Map, Coordinate, Borders
from ymaps.downloaders import RequestsDownloader
from ymaps.render import PreviewRenderer

VERSION = '3.1064.0'

logger = logging.getLogger('ymaps')

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO, stream=sys.stdout)


class App():

    map = None

    def __parse_args(self):
        parser = argparse.ArgumentParser(description='Schaeffler store parser')
        parser.add_argument('--map', help='Map filename', type=str, required=False)
        parser.add_argument('--download', help='Download map', action='store_true', default=False)
        parser.add_argument('--preview', help='Preview map', action='store_true', default=False)
        parser.add_argument('--tile', help='Tile', type=str, required=False)
        parser.add_argument('--scale', help='Scale', type=int, required=False)
        self.args = parser.parse_args()


    def __init__(self):
        self.__parse_args()


    def download_one_tile(self, tile_str: str):
        tile = Tile.fromstr(tile_map=None, s=tile_str)
        downloader = RequestsDownloader()
        scheduler = DownloadSimpleScheduler([tile], downloader, CommonDownloadPolicy)
        scheduler.download()


    def download(self, filename):
        self.map = self.prepare_map(filename)

        self.map.download_scheduler = DownloadSimpleScheduler(
            self.map.tiles,
            RequestsDownloader,
            CommonDownloadPolicy
        )

        if not os.path.exists(self.map.path()):
            os.makedirs(self.map.path())

        self.map.download_scheduler.download()


    def prepare_map(self, filename):
        data = json.loads(open(filename).read())

        borders = Borders(
            Coordinate(data['coord1']['lat'], data['coord1']['lon']),
            Coordinate(data['coord2']['lat'], data['coord2']['lon'])
        )

        return Map(data['name'], borders, z=self.args.scale, layer='sat', version=VERSION)

        logger.info(f"{len(self.map)=}")


    def preview(self, filename):
        if not self.map:
            self.map = self.prepare_map(filename)

        renderer = PreviewRenderer(self.map)
        renderer.render('overview.png')


    def run(self):
        if self.args.download:
            if self.args.tile:
                self.download_one_tile(self.args.tile)
            else:
                self.download(self.args.map)
        if self.args.preview:
            self.preview(self.args.map)


if __name__ == '__main__':
    app = App()
    sys.exit(app.run())
