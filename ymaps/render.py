from PIL import Image, ImageDraw

from ymaps.map import Map

class PreviewRenderer():

    def __init__(self, map: Map):
        self.map = map

    def render(self, destination: str):
        self.image = Image.new("RGB", (self.map.width, self.map.height,), "white")
        draw = ImageDraw.Draw(self.image)

        for tile in self.map.tiles:
            draw.point((tile.x - self.map.x1, tile.y - self.map.y1), tile.render())

        self.image.save(destination)