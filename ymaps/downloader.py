import os
import sys
import time
import math
import random
import shutil
import argparse
import datetime as dt
import configparser

import requests

from ymaps.tools import coordinates_to_tiles

class YMapDownloader(object):
    """Yandex Maps download module"""

    def __init__(self):
        random.seed()
        self.user_agent = 'Mozilla/5.0 (X11; Linux x86_64; rv:25.0) Gecko/20100101 Firefox/25.0'
        self.accept = 'image/png,image/*;q=0.8,*/*;q=0.5'
        self.accept_language = 'ru-ru,ru;q=0.8,en-us;q=0.5,en;q=0.3'
        self.accept_encoding = 'gzip, deflate'
        self.accept_charset = 'windows-1251,utf-8;q=0.7,*;q=0.7'

        parser = argparse.ArgumentParser(description='Yandex Map downloader.')
        parser.add_argument('--layer', type=str, help='Layer (sat, vec)', required=True)
        parser.add_argument('--conf', type=str, help='Configuration file', required=True)
        self.args = parser.parse_args()

        self.ReadConfig()
        self.referer = 'http://maps.yandex.net/?ll=37.621972%2C55.784424&spn=0.011029%2C0.004033&z=17&l={layer}'.format(layer=self.layer)
        if not os.path.isdir(self.dir_map):
            os.makedirs(self.dir_map)

    def Fail(self, msg=None):
        if msg is not None:
            print('Error: %s' % msg)
        sys.exit(1)

    def PutVariablesInDir(self, dir):
        vars = {'layer': self.layer, 'version': self.version,
                'date': dt.datetime.now().strftime('%Y%m%d')}
        result = dir
        for var in vars.keys():
            result = result.replace('{%s}' % var, vars.get(var, ''))
        return result

    def ReadConfig(self):
        config = configparser.SafeConfigParser()
        config.readfp(open(self.args.conf))
        self.layer = self.args.layer

        try:
            self.version = config.get('MAIN', 'Version%s' % self.layer.capitalize())
        except configparser.NoOptionError:
            self.Fail('There is not version information for layer %s' % self.layer)

        self.language = config.get('MAIN', 'Language')
        x1, y1 = list(map(float, config.get('MAIN', 'coords1').split(',')))
        x2, y2 = list(map(float, config.get('MAIN', 'coords2').split(',')))
        self.coords1 = [x1, y1]
        self.coords2 = [x2, y2]
        print('%s,%s - %s,%s' % (x1, y1, x2, y2))
        self.x1, self.y1 = coordinates_to_tiles(x1, y1, 18)
        self.x2, self.y2 = coordinates_to_tiles(x2, y2, 18)
        self.dir_map = self.PutVariablesInDir(config.get('MAIN', 'DirMap'))
        self.scale = config.get('MAIN', 'Scale')
        self.mirrors = [ '%s%02d.maps.yandex.net' % (self.layer, i) for i in range(1,5) ]
        print('%s,%s - %s,%s' % (self.x1, self.y1, self.x2, self.y2))

    def GetRandomMirror(self):
        return self.mirrors[random.randint(0,len(self.mirrors)-1)]

    def GetTileHost(self, layer):
        if layer == 'vec':
            return 'core-renderer-tiles.maps.yandex.net'
        elif layer == 'sat':
            return 'core-sat.maps.yandex.net'
        else:
            raise NotImplementedError(f"Unknow layer {layer}")

    def GetTileURL(self, layer, x, y, z, version, lang):
        if layer == 'vec':
            return f"/tiles?l=map&v={version}&x={x}&y={y}&z={z}&lang={lang}"
        elif layer == 'sat':
            return f"/tiles?l=sat&v={version}&x={x}&y={y}&z={z}&scale=1&lang={lang}"
        else:
            raise NotImplementedError(f"Unknow layer {layer}")

    def DownloadTile(self, x, y, z):
        image_type_mapping = {'vec': 'png', 'sat': 'jpg'}

        filename = f"./{self.dir_tiles}/{x}_{y}_{z}.{image_type_mapping[self.layer]}"

        if os.path.isfile(filename):
            return "e"

        url = self.GetTileURL(self.layer, x, y, z, self.version, self.language)

        headers = {"User-Agent": self.user_agent,
                   "Accept": self.accept,
                   "Accept-Language": self.accept_language,
                   "Accept-Encoding": self.accept_encoding,
                   "Accept-Charset": self.accept_charset,
                   "Referer": self.referer}
        req = requests.Request('GET', "https://%s%s" % (self.GetTileHost(self.layer), url), headers=headers)
        s = requests.Session()
        r = req.prepare()

        try:
            response = s.send(r, stream=True)
        except requests.exceptions.ConnectionError as e:
            return "!"
        if response.status_code == 200:
            with open(filename, "wb") as f:
                response.raw.decode_content = True
                shutil.copyfileobj(response.raw, f)
            return '+'
        else:
            return '!'

    def Sleep(self):
        seconds = random.randint(5,20)
        print("Sleepeng for {s} seconds...".format(s = seconds))
        time.sleep(seconds)

    def Start(self):
        PacketSize = random.randint(50,100)
        c = 0
        tiles_in_packet = 1
        print("Downloading next {c} tiles...".format(c = PacketSize))

        for z in map(int, self.scale.split(',')):

            print("Processing z = %s" % z)

            tiles_count = 1.0
            self.dir_tiles = os.path.join(self.dir_map, 'tiles', str(z))
            if not os.path.isdir(self.dir_tiles): os.makedirs(self.dir_tiles)

            x1, y1 = coordinates_to_tiles(*self.coords1, z)
            x2, y2 = coordinates_to_tiles(*self.coords2, z)
            start = {'x': x1, 'y': y1}
            end   = {'x': x2, 'y': y2}

            print("Start: %s" % start)
            print("End: %s" % end)

            self.total_tiles = (end['x'] + 1 - start['x'])*(end['y'] + 1 - start['y'])
            print("Total tiles to download: {total}".format(total=self.total_tiles))

            for x in range(start['x'], end['x'] + 1):
                for y in range(start['y'], end['y'] + 1):
                    flag = self.DownloadTile(x, y, z)
                    print("GET {: >3} {: >10} {: >10} | {:.2f}% {: ^1}".format(z, x, y, round((tiles_count/self.total_tiles)*100,2), flag))
                    if flag == '+':
                        tiles_in_packet += 1
                    c = c + 1
                    tiles_count = tiles_count + 1
                    if c == PacketSize:
                        if tiles_in_packet > 10:
                            self.Sleep()
                        else:
                            print("Skipping sleeping: < 10 tiles where downloaded in this packet")
                        c = 0
                        PacketSize = random.randint(50,100)
                        tiles_in_packet = 0
                        print("Downloading next {c} tiles...".format(c = PacketSize))

    def GetCoordAtZ(self, coord18, z):
        return int(math.floor(int(coord18) / math.pow(2, 18 - int(z))))