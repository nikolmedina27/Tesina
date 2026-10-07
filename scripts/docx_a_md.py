"""Convierte la tesis (Word) a Markdown por capítulos en docs/tesis/.

Uso:  python scripts/docx_a_md.py
Solo usa la librería estándar (no requiere python-docx ni lxml).
"""
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DOCX = RAIZ / 'extras' / 'Tesis_TF1_Steelser.docx'
SALIDA = RAIZ / 'docs' / 'tesis'
IMG = SALIDA / 'img'

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
A = '{http://schemas.openxmlformats.org/drawingml/2006/main}'
R = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'
V = '{urn:schemas-microsoft-com:vml}'
REL = '{http://schemas.openxmlformats.org/package/2006/relationships}'

# Capítulo -> archivo. Se detecta por el texto del encabezado.
CAPITULOS = [
    (r'^Cap[ií]tulo I\.', '01_introduccion.md'),
    (r'^Cap[ií]tulo II\.', '02_revision_literatura.md'),
    (r'^Cap[ií]tulo III\.', '03_aporte.md'),
    (r'^Referencias$', '05_referencias.md'),
    (r'^ANEXOS$', '04_caso_estudio_anexos.md'),
]


def texto_parrafo(p):
    out = []
    for n in p.iter():
        if n.tag == W + 't':
            out.append(n.text or '')
        elif n.tag == W + 'tab':
            out.append(' ')
        elif n.tag == W + 'br':
            out.append(' ')
    return re.sub(r'\s+', ' ', ''.join(out)).strip()


def estilo(p):
    ppr = p.find(W + 'pPr')
    if ppr is not None and ppr.find(W + 'pStyle') is not None:
        return (ppr.find(W + 'pStyle').get(W + 'val') or '').lower()
    return ''


def imagenes(p, rels):
    ids = [b.get(R + 'embed') for b in p.iter(A + 'blip')]
    ids += [i.get(R + 'id') for i in p.iter(V + 'imagedata')]
    return [rels[i] for i in ids if i in rels]


def main():
    z = zipfile.ZipFile(DOCX)
    rels = {}
    for r in ET.fromstring(z.read('word/_rels/document.xml.rels')).iter(REL + 'Relationship'):
        if r.get('Target', '').startswith('media/'):
            rels[r.get('Id')] = r.get('Target')
    IMG.mkdir(parents=True, exist_ok=True)
    for target in set(rels.values()):
        (IMG / Path(target).name).write_bytes(z.read('word/' + target))

    body = ET.fromstring(z.read('word/document.xml')).find(W + 'body')
    archivos = {'00_portada_resumen.md': []}
    actual = '00_portada_resumen.md'
    for el in body:
        if el.tag == W + 'p':
            t = texto_parrafo(el)
            for target in imagenes(el, rels):
                archivos[actual].append(f'![{Path(target).stem}](img/{Path(target).name})')
            if not t:
                continue
            for patron, nombre in CAPITULOS:
                if re.match(patron, t):
                    actual = nombre
                    archivos.setdefault(actual, [])
                    break
            st = estilo(el)
            m = re.search(r'(heading|ttulo|titulo)(\d)', st)
            if m:
                archivos[actual].append('#' * min(int(m.group(2)), 5) + ' ' + t)
            elif 'prrafodelista' in st or 'listparagraph' in st:
                archivos[actual].append('- ' + t)
            elif 'descripcin' in st or 'caption' in st:
                archivos[actual].append(f'**{t}**')
            elif 'tabladeilustraciones' in st:
                archivos[actual].append('- ' + re.sub(r'\s+\d+$', '', t))
            else:
                archivos[actual].append(t)
        elif el.tag == W + 'tbl':
            filas = []
            for tr in el.iter(W + 'tr'):
                celdas = [' '.join(texto_parrafo(p) for p in tc.iter(W + 'p')).replace('|', '/').strip()
                          for tc in tr.findall(W + 'tc')]
                filas.append(celdas)
            if not filas:
                continue
            n = max(len(f) for f in filas)
            filas = [f + [''] * (n - len(f)) for f in filas]
            md = ['| ' + ' | '.join(filas[0]) + ' |', '|' + '---|' * n]
            md += ['| ' + ' | '.join(f) + ' |' for f in filas[1:]]
            archivos[actual].append('\n'.join(md))

    aviso = ('> Conversión automática de `extras/Tesis_TF1_Steelser.docx` generada por '
             '`scripts/docx_a_md.py`. No editar a mano: regenerar si cambia el Word.\n')
    for nombre, bloques in archivos.items():
        (SALIDA / nombre).write_text(aviso + '\n' + '\n\n'.join(bloques) + '\n', encoding='utf-8')
        print(f'{nombre}: {len(bloques)} bloques')


if __name__ == '__main__':
    main()
