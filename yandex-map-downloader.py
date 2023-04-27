#!/usr/bin/env python3

import sys
import json
import logging
import argparse

from ymaps.tile import Tile
from ymaps.map import Map, Coordinate, Borders
from ymaps.downloaders import DownloadSleepScheduler
from ymaps.render import PreviewRenderer

VERSION = '3.1064.0'

logger = logging.getLogger('ymaps')

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO, stream=sys.stdout)


class App():

    map = None

    def __parse_args(self):
        parser = argparse.ArgumentParser(description='Schaeffler store parser')
        parser.add_argument('--map', help='Map filename', type=str, required=True)
        parser.add_argument('--download', help='Download map', action='store_true', default=False)
        parser.add_argument('--preview', help='Preview map', action='store_true', default=False)
        self.args = parser.parse_args()


    def __init__(self):
        self.__parse_args()


    def download(self, filename):
        self.map = self.prepare_map(filename)

        self.map.download_scheduler = DownloadSleepScheduler
        self.map.download()


    def prepare_map(self, filename):
        data = json.loads(open(filename).read())

        borders = Borders(
            Coordinate(data['coord1']['lat'], data['coord1']['lon']),
            Coordinate(data['coord2']['lat'], data['coord2']['lon'])
        )

        return Map(borders, z=20, layer='sat', version=VERSION)

        logger.info(f"{len(self.map)=}")


    def preview(self, filename):
        if not self.map:
            self.map = self.prepare_map(filename)

        renderer = PreviewRenderer(self.map)
        renderer.render('overview.png')


    def run(self):
        if self.args.download:
            self.download(self.args.map)
        if self.args.preview:
            self.preview(self.args.map)


if __name__ == '__main__':
    app = App()
    sys.exit(app.run())
