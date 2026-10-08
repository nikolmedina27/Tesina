"""Genera plataforma/web/icono.png e icono.ico (viga I celeste con línea naranja) con Pillow."""
from pathlib import Path

from PIL import Image, ImageDraw

WEB = Path(__file__).resolve().parent.parent / 'plataforma' / 'web'
N = 256
img = Image.new('RGBA', (N, N), (0, 0, 0, 0))
grad = Image.new('RGBA', (N, N))
for y in range(N):
    for x in range(N):
        t = (x + y) / (2 * N)
        grad.putpixel((x, y), (int(8 + (27 - 8) * t), int(84 + (144 - 84) * t), int(160 + (255 - 160) * t), 255))
mask = Image.new('L', (N, N), 0)
ImageDraw.Draw(mask).rounded_rectangle([0, 0, N - 1, N - 1], radius=56, fill=255)
img.paste(grad, (0, 0), mask)
d = ImageDraw.Draw(img)
d.rectangle([56, 72, 200, 96], fill='white')          # ala superior
d.rectangle([116, 96, 140, 160], fill='white')        # alma
d.rectangle([56, 160, 200, 184], fill='white')        # ala inferior
d.rounded_rectangle([40, 204, 216, 220], radius=8, fill=(233, 115, 12, 255))
img.save(WEB / 'icono.png')
img.save(WEB / 'icono.ico', sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
print('OK', WEB / 'icono.ico')
