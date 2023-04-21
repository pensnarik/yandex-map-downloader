#!/usr/bin/env python3

import sys
import json
import logging

from ymaps.tile import Tile
from ymaps.map import Map, Coordinate, Borders
from ymaps.downloaders import DownloadScheduler

VERSION = '3.1064.0'

logger = logging.getLogger('ymaps')

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO, stream=sys.stdout)


data = json.loads(open('moscow.json').read())

Borders = Borders(
	Coordinate(data['coord1']['lat'], data['coord1']['lon']),
	Coordinate(data['coord2']['lat'], data['coord2']['lon'])
)

map = Map(Borders, z=13, layer='sat', version=VERSION)

logger.info(f"{len(map)=}")

map.download_scheduler = DownloadScheduler
map.download()
