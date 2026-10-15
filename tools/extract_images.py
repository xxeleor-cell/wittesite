"""Извлечение фотографий продукции из исходных PDF-каталогов.

Запуск:  python3 tools/extract_images.py [путь_к_папке_с_каталогами]
По умолчанию каталоги ищутся в ~/Downloads/witte.
Требуется: pip install pymupdf pillow

Координаты кадров заданы в системе «1400 px по длинной стороне страницы».
Результат: site/assets/img/p/<id>.jpg и копии PDF в site/docs/.
"""
import io
import os
import shutil
import sys

import fitz  # PyMuPDF
from PIL import Image, ImageChops

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/Downloads/witte")
OUT = os.path.join(ROOT, "site", "assets", "img", "p")
DOCS = os.path.join(ROOT, "site", "docs")

PDF = {
    "hy": "恒元绿丰农牧中性说明.pdf",
    "cast": "돈사주철 바닥铸铁漏粪板.pdf",
    "drinker": "돼지용 음수대猪用饮水器pig drinker.pdf",
    "tower": "사료탑과 부속품料塔及配件.pdf",
    "trough": "사료통XF料槽.pdf",
    "panel": "LW PP PVC PANEAL AND FLOOR.pdf",
}
PPTX = "养猪智能硬件英文版.pptx"
PPTX_IMG = {(3, 6): "ctrl-k16pro", (4, 5): "ctrl-k16", (5, 5): "ctrl-k9", (6, 5): "ctrl-bcm1",
            (7, 5): "ctrl-bcs1", (8, 8): "sensor-1", (8, 5): "sensor-2", (8, 34): "sensor-3"}
# Публикуемые копии каталогов (нейтральные версии, без чужих брендов в названии файла)
DOC_FILES = {
    "hy": "katalog-mikroklimat-obogrev.pdf",
    "cast": "katalog-chugunnye-poly.pdf",
    "drinker": "katalog-poilki.pdf",
    "tower": "katalog-bunkery-kormovye-linii.pdf",
    "trough": "katalog-kormushki-komplektuyushchie.pdf",
    "panel": "katalog-poly-paneli-steklo-plastik.pdf",
}

# Стандартные позиции карточек в каталоге LW (разворот 1400×957)
L1, L2 = (68, 133, 298, 297), (68, 494, 298, 658)
R1, R2 = (758, 133, 988, 297), (758, 494, 988, 658)
L2b, R2b = (68, 518, 298, 682), (758, 518, 988, 682)
T1, T2, T3 = (68, 133, 298, 297), (68, 365, 298, 529), (68, 598, 298, 762)
U1, U2, U3 = (758, 133, 988, 297), (758, 365, 988, 529), (758, 598, 988, 762)

# id -> (каталог, страница, рамка)
BOX = {
    # --- Климат (hy, портрет 1005×1400)
    "hyfb-1": ("hy", 3, (94, 216, 840, 716)),
    "hyfb-2": ("hy", 4, (126, 356, 290, 480)),
    "hy-cone-1": ("hy", 5, (250, 165, 905, 465)),
    "hy-cone-2": ("hy", 5, (644, 818, 962, 966)),
    "hya-1": ("hy", 6, (90, 170, 860, 660)),
    "hyb-1": ("hy", 7, (160, 170, 890, 490)),
    "hybf-1": ("hy", 8, (90, 170, 830, 660)),
    "hynf-1": ("hy", 9, (190, 165, 925, 435)),
    "hyn-1": ("hy", 10, (90, 170, 850, 585)),
    "deflector-1": ("hy", 11, (628, 198, 892, 462)),
    "shutter-1": ("hy", 11, (138, 678, 862, 1082)),
    "turbine-1": ("hy", 12, (248, 218, 602, 402)),
    "roofvent-1": ("hy", 12, (98, 698, 272, 872)),
    "circ-1": ("hy", 12, (674, 738, 892, 942)),
    "inlet-1": ("hy", 13, (118, 138, 922, 742)),
    "roofinlet-1": ("hy", 13, (118, 908, 922, 1112)),
    "lighttrap-1": ("hy", 14, (88, 178, 842, 592)),
    "lighttrap-2": ("hy", 14, (78, 1028, 882, 1192)),
    "pad-1": ("hy", 15, (118, 208, 882, 402)),
    "pad-2": ("hy", 16, (178, 218, 522, 642)),
    "cooler-1": ("hy", 17, (108, 148, 912, 492)),
    "padsink-1": ("hy", 19, (108, 168, 922, 472)),
    "padsink-2": ("hy", 19, (108, 898, 922, 1132)),
    "washer-1": ("hy", 20, (108, 188, 892, 582)),
    "coalbox-1": ("hy", 22, (588, 188, 792, 492)),
    "oil-1": ("hy", 23, (148, 208, 612, 572)),
    "elec-1": ("hy", 24, (128, 188, 842, 582)),
    "radiator-1": ("hy", 25, (108, 168, 892, 432)),
    "freshrad-1": ("hy", 26, (148, 208, 802, 552)),
    # --- Поилки (drinker, альбом 1400×950)
    "nipple-1": ("drinker", 1, (0, 290, 1300, 430)),
    "nipple-2": ("drinker", 2, (285, 150, 445, 430)),
    "nipple-3": ("drinker", 2, (915, 100, 1065, 430)),
    "nipple-4": ("drinker", 2, (345, 360, 480, 640)),
    "nipple-5": ("drinker", 3, (745, 380, 1330, 500)),
    "nipple-6": ("drinker", 3, (815, 570, 1265, 835)),
    "nipple-7": ("drinker", 2, (895, 580, 1045, 880)),
    "nipple-piglet": ("drinker", 3, (750, 175, 1330, 340)),
    "nipple-orifice": ("drinker", 3, (435, 160, 625, 305)),
    "bowl-round-1": ("drinker", 4, (60, 100, 330, 235)),
    "bowl-round-2": ("drinker", 4, (760, 100, 1030, 240)),
    "bowl-oval-1": ("drinker", 5, (50, 100, 290, 280)),
    "bowl-rect-1": ("drinker", 5, (720, 120, 920, 260)),
    "bowl-rect-2": ("drinker", 5, (720, 640, 920, 790)),
    "sowtrough-fx-1": ("drinker", 6, (155, 120, 495, 265)),
    "pigletfeeder-fx-1": ("drinker", 6, (785, 125, 1105, 265)),
    "waterlevel-1": ("drinker", 6, (895, 545, 1365, 895)),
    "pipe-1": ("drinker", 7, (35, 80, 655, 905)),
    # --- Каталог LW (полы, панели, стеклопластик)
    "lw6040": ("panel", 3, R1), "lw6050": ("panel", 3, R2),
    "lw6060": ("panel", 4, L1), "lw6060c": ("panel", 4, L2),
    "lw6040b": ("panel", 4, R1), "lw6040c": ("panel", 4, R2),
    "lw6020": ("panel", 5, L1), "lw6020b": ("panel", 5, L2),
    "lwjr12040": ("panel", 5, R1), "lwd6040": ("panel", 5, R2),
    "lwd6050": ("panel", 6, L1), "lwd6060": ("panel", 6, L2),
    "lwd6070": ("panel", 6, R1), "lwd6060c": ("panel", 6, R2),
    "lwd6060c10": ("panel", 7, L1), "lwg6040": ("panel", 7, L2),
    "lwg6050": ("panel", 7, R1),
    "lwg6050c10": ("panel", 8, L1), "lwg6060": ("panel", 8, L2),
    "f32019": ("panel", 8, R1), "lwg6080": ("panel", 8, R2),
    "lwg6040b": ("panel", 9, L1), "lwg6060c": ("panel", 9, L2),
    "lws6030": ("panel", 9, R1), "lws6040": ("panel", 9, R2),
    "lws6050": ("panel", 10, L1), "lws6060": ("panel", 10, L2),
    "k8040b": ("panel", 10, R1), "doser-1": ("panel", 10, R2),
    "connector-22083": ("panel", 11, L2), "endplug-1": ("panel", 11, R1),
    "handle-1": ("panel", 11, R2),
    "floorplug-1": ("panel", 12, L1), "frpplug-1": ("panel", 12, (68, 413, 298, 577)),
    "stringtee-1": ("panel", 12, R1), "nylonfast-1": ("panel", 12, (758, 413, 965, 577)),
    "stopper-1": ("panel", 13, (68, 133, 298, 297)), "hornpipe-1": ("panel", 13, (68, 554, 298, 718)),
    "hopper62010": ("panel", 13, (758, 133, 988, 297)), "hopper62011": ("panel", 13, (758, 330, 988, 494)),
    "telefast-1": ("panel", 13, (758, 554, 988, 718)),
    "pipefast-1": ("panel", 14, (68, 133, 298, 297)), "pigletbowl-22091": ("panel", 14, (68, 471, 298, 635)),
    "frpbracket-1": ("panel", 14, (68, 668, 298, 832)), "elbowtee-1": ("panel", 14, (758, 133, 965, 297)),
    "midsupport-1": ("panel", 14, (758, 436, 965, 600)),
    "doorcover-1": ("panel", 15, (68, 133, 298, 297)), "telepipe-1": ("panel", 15, (68, 462, 298, 626)),
    "butterfly-1": ("panel", 15, (787, 133, 988, 410)), "frp-hero": ("panel", 15, (768, 690, 1030, 910)),
    "frp-delta": ("panel", 16, (68, 133, 641, 390)), "frp-t1": ("panel", 16, (758, 133, 1331, 390)),
    "frp-t2": ("panel", 17, (68, 133, 641, 390)), "frp-profile": ("panel", 17, (758, 133, 1331, 390)),
    "pvc-hero": ("panel", 18, (60, 125, 395, 282)),
    "lw20015zzp": ("panel", 18, L2b), "lw25035zzp": ("panel", 18, R1), "lw25035rxp": ("panel", 18, R2b),
    "lw25035rzp": ("panel", 19, L1), "lw25035zzp2": ("panel", 19, L2b),
    "lw50020zz": ("panel", 19, R1), "lw60020rzp": ("panel", 19, R2b),
    "lw50030zz": ("panel", 20, L1), "lw60030zzp": ("panel", 20, L2b),
    "lw50822zz": ("panel", 20, R1), "lw50035zz": ("panel", 20, R2b),
    "lw60035zz": ("panel", 21, L1), "lw74035zz": ("panel", 21, L2b),
    "lw50035zzp": ("panel", 21, R1), "lw50035rzp": ("panel", 21, R2b),
    "pvc-zx": ("panel", 22, (68, 127, 641, 297)),
    "lw100035zx": ("panel", 23, L1), "lw50075zzp": ("panel", 23, R1), "lw90050zx": ("panel", 23, R2b),
    "lw96550zx": ("panel", 24, L1), "lw50035rxpg": ("panel", 24, L2b),
    "lw60035rxpg": ("panel", 24, R1), "pvc-uslot": ("panel", 24, R2b),
    "pvc-oval": ("panel", 25, T1), "pvc-reducer": ("panel", 25, T2), "pvc-l": ("panel", 25, T3),
    "pvc-y": ("panel", 25, U1), "pvc-ji": ("panel", 25, U2), "pvc-post1": ("panel", 25, U3),
    "pvc-post2": ("panel", 26, T1), "pvc-post3": ("panel", 26, T2), "pvc-post4": ("panel", 26, T3),
    "pvc-feedpipe": ("panel", 26, U1), "pvc-h50": ("panel", 26, U2), "pvc-h35": ("panel", 26, U3),
    "pvc-h20": ("panel", 27, T1), "pvc-i15": ("panel", 27, T2), "pvc-square": ("panel", 27, T3),
    "pvc-t": ("panel", 27, U1), "pvc-angle": ("panel", 27, U2), "pvc-feedelbow": ("panel", 27, U3),
    "pp-1": ("panel", 28, (68, 180, 331, 542)), "pp-2": ("panel", 28, (372, 180, 635, 542)),
    "pp-3": ("panel", 28, (758, 180, 1325, 360)), "pp-4": ("panel", 28, (758, 540, 1325, 728)),
    "case-1": ("panel", 29, (68, 123, 557, 481)), "case-2": ("panel", 29, (68, 498, 557, 856)),
    "case-3": ("panel", 29, (833, 123, 1322, 481)), "case-4": ("panel", 29, (833, 498, 1322, 856)),
    "case-5": ("panel", 30, (68, 123, 557, 481)), "case-6": ("panel", 30, (68, 498, 557, 856)),
    "case-7": ("panel", 30, (833, 123, 1322, 481)), "case-8": ("panel", 30, (833, 498, 1322, 856)),
    "plant-1": ("panel", 1, (49, 137, 657, 487)), "plant-2": ("panel", 1, (743, 137, 1351, 485)),
    "plant-3": ("panel", 1, (49, 503, 657, 870)), "plant-4": ("panel", 1, (743, 503, 1351, 870)),
    "stock-1": ("panel", 2, (49, 203, 448, 502)), "stock-2": ("panel", 2, (953, 553, 1351, 853)),
}

# Изображения, встроенные в PDF отдельными объектами: id -> (каталог, страница, индекс)
EMBED = {
    "silo-1": ("tower", 1, 0), "silo-2": ("tower", 4, 1), "silo-3": ("tower", 2, 1),
    "weigh-1": ("tower", 3, 0), "weigh-2": ("tower", 3, 2), "weigh-3": ("tower", 3, 3),
    "weigh-4": ("tower", 3, 4), "weigh-5": ("tower", 3, 5),
    "silohop-1": ("tower", 3, 6), "silohop-2": ("tower", 3, 10), "silohop-3": ("tower", 3, 11),
    "silohop-4": ("tower", 3, 12), "silohop-5": ("tower", 3, 13), "silohop-6": ("tower", 3, 14),
    "silohop-7": ("tower", 3, 8), "silohop-8": ("tower", 3, 7), "silohop-9": ("tower", 3, 9),
    "auger-1": ("tower", 4, 3), "auger-2": ("tower", 4, 4), "feedsys-1": ("tower", 4, 0),
    "chainline-1": ("tower", 4, 2),
    "drive-1": ("tower", 5, 0), "drive-2": ("tower", 5, 1), "chain-1": ("tower", 5, 2), "chain-2": ("tower", 5, 7),
    "corner-1": ("tower", 5, 3), "corner-2": ("tower", 5, 8),
    "clamp-1": ("tower", 5, 4),
    "lb-1": ("trough", 1, 1), "lb-2": ("trough", 1, 0), "lb-3": ("trough", 1, 11), "lb-4": ("trough", 1, 4),
    "lb-5": ("trough", 1, 9), "lb-6": ("trough", 1, 3), "xlg-1": ("trough", 1, 7),
    "corner-3": ("trough", 2, 0), "corner-4": ("trough", 2, 1), "corner-5": ("trough", 2, 2),
    "corner-6": ("trough", 2, 7), "corner-7": ("trough", 2, 9), "corner-8": ("trough", 2, 10),
    "outlet-1": ("trough", 2, 3), "outlet-2": ("trough", 2, 4), "outlet-3": ("trough", 2, 5),
    "outlet-4": ("trough", 2, 8), "outlet-5": ("trough", 2, 13), "outlet-6": ("trough", 2, 6),
    "mzj-1": ("trough", 3, 0), "xf-1": ("trough", 3, 1), "xk-1": ("trough", 3, 2),
    "zdld-1": ("trough", 3, 3), "zdld-2": ("trough", 3, 4), "zdfl-1": ("trough", 3, 5),
    "gk-1": ("trough", 3, 6), "gk-2": ("trough", 3, 7),
    "dw-1": ("trough", 4, 0), "dw-2": ("trough", 4, 1), "dw-3": ("trough", 4, 2),
    "dw-4": ("trough", 4, 3), "dw-5": ("trough", 4, 4), "dw-6": ("trough", 4, 5),
    "lt-1": ("trough", 5, 0), "lt-2": ("trough", 5, 1), "lt-3": ("trough", 5, 2), "lt-4": ("trough", 5, 11),
    "dp-1": ("trough", 5, 3), "dp-2": ("trough", 5, 4), "dp-3": ("trough", 5, 5), "dp-4": ("trough", 5, 6),
    "dp-5": ("trough", 5, 7), "dp-6": ("trough", 5, 9),
    "mzc-1": ("trough", 6, 1), "mzc-2": ("trough", 6, 2), "mzc-3": ("trough", 6, 3),
    "mzc-4": ("trough", 6, 6), "zncd-1": ("trough", 6, 4), "zncd-2": ("trough", 6, 5),
    "b01-1": ("trough", 7, 0), "b01-2": ("trough", 7, 1),
    "ybowl-1": ("trough", 7, 2), "ybowl-2": ("trough", 7, 3), "ybowl-3": ("trough", 7, 4),
    "j01": ("trough", 7, 5), "j02": ("trough", 7, 6), "j04": ("trough", 7, 7), "j02b": ("trough", 7, 8),
    "j05": ("trough", 7, 9), "j03": ("trough", 7, 10), "j03b": ("trough", 7, 11),
    "bwx01": ("trough", 8, 0), "bwx03-1": ("trough", 8, 1), "bwx03-2": ("trough", 8, 2),
    "blc01": ("trough", 8, 3), "blc02": ("trough", 8, 4), "blc03": ("trough", 8, 5),
    "blc04": ("trough", 8, 6), "blc05": ("trough", 8, 7), "blc06": ("trough", 8, 8),
    "dzb-1": ("trough", 9, 1), "dzb-2": ("trough", 9, 2), "spf-1": ("trough", 9, 3),
    "bwx02": ("trough", 9, 4), "tfc-1": ("trough", 9, 5),
    "cast-full": ("cast", 1, 6), "cast-semi": ("cast", 1, 8), "cast-round": ("cast", 1, 7),
    "cast-manure": ("cast", 1, 4), "cast-semi2": ("cast", 1, 9), "cast-2": ("cast", 2, 1),
    "cast-900a": ("cast", 4, 0), "cast-900b": ("cast", 4, 1),
    "castleg-1": ("cast", 5, 0), "castbeam-1": ("cast", 5, 1),
    "casttrough-1": ("cast", 5, 5), "casttrough-2": ("cast", 5, 10),
    "baffle-1": ("cast", 5, 8), "baffle-2": ("cast", 5, 9),
    "farrowfloor-1": ("cast", 6, 0), "farrowfloor-2": ("cast", 6, 1),
    "farrowfloor-3": ("cast", 6, 5), "farrowfloor-4": ("cast", 6, 6),
    "crate-2": ("cast", 7, 5), "crate-3": ("cast", 7, 6), "crate-4": ("cast", 7, 7),
    "stall-1": ("cast", 8, 1), "stall-2": ("cast", 8, 0),
}


def trim(im, pad=12):
    """Обрезать почти белые поля по краям."""
    bg = Image.new(im.mode, im.size, (255, 255, 255))
    diff = ImageChops.difference(im, bg).convert("L").point(lambda v: 255 if v > 18 else 0)
    bb = diff.getbbox()
    if not bb:
        return im
    x0, y0, x1, y1 = bb
    return im.crop((max(0, x0 - pad), max(0, y0 - pad), min(im.width, x1 + pad), min(im.height, y1 + pad)))


def save(im, name, maxside=1100):
    im = im.convert("RGB")
    im = trim(im)
    im.thumbnail((maxside, maxside), Image.LANCZOS)
    im.save(os.path.join(OUT, name + ".jpg"), quality=84, optimize=True, progressive=True)


def main():
    fitz.TOOLS.mupdf_display_errors(False)
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(DOCS, exist_ok=True)
    docs = {k: fitz.open(os.path.join(SRC, f)) for k, f in PDF.items()}
    cache = {}

    def page_img(k, n):
        if (k, n) not in cache:
            if len(cache) > 6:
                cache.clear()
            p = docs[k][n - 1]
            z = 3600 / max(p.rect.width, p.rect.height)
            pix = p.get_pixmap(matrix=fitz.Matrix(z, z))
            cache[(k, n)] = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        return cache[(k, n)]

    for name, (k, n, box) in sorted(BOX.items(), key=lambda x: (x[1][0], x[1][1])):
        im = page_img(k, n)
        s = max(im.size) / 1400
        save(im.crop(tuple(int(v * s) for v in box)), name)

    for name, (k, n, idx) in sorted(EMBED.items(), key=lambda x: (x[1][0], x[1][1])):
        p = docs[k][n - 1]
        z = 1400 / max(p.rect.width, p.rect.height)
        W, H = p.rect.width * z, p.rect.height * z
        boxes = []
        for info in p.get_image_info():
            b = fitz.Rect(info["bbox"]) * z
            b = b & fitz.Rect(0, 0, W, H)
            if b.is_empty or b.width < 60 or b.height < 45:
                continue
            if b.width > W * 0.9 and b.height > H * 0.9:
                continue
            if any(abs(b.x0 - o.x0) < 4 and abs(b.y0 - o.y0) < 4 and abs(b.x1 - o.x1) < 4 for o in boxes):
                continue
            boxes.append(b)
        b = boxes[idx]
        im = page_img(k, n)
        s = max(im.size) / 1400
        save(im.crop((int(b.x0 * s), int(b.y0 * s), int(b.x1 * s), int(b.y1 * s))), name)

    # Фото контроллеров и датчиков из презентации (PPTX)
    from pptx import Presentation
    pres = Presentation(os.path.join(SRC, PPTX))
    for n, slide in enumerate(pres.slides, 1):
        for sh in slide.shapes:
            key = (n, sh.shape_id)
            if sh.shape_type == 13 and key in PPTX_IMG:
                im = Image.open(io.BytesIO(sh.image.blob)).convert("RGBA")
                bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
                bg.alpha_composite(im)
                save(bg, PPTX_IMG[key])
    shutil.copyfile(os.path.join(SRC, PPTX), os.path.join(DOCS, "prezentaciya-kontrollery-mikroklimata.pptx"))

    for k, f in DOC_FILES.items():
        dst = os.path.join(DOCS, f)
        if not os.path.exists(dst):
            src = docs[k]
            # пересжатие изображений: файлы > 100 МБ не принимает GitHub, и их долго скачивать
            src.rewrite_images(dpi_threshold=200, dpi_target=150, quality=75)
            src.save(dst, garbage=4, deflate=True)
    print("images:", len(os.listdir(OUT)))


if __name__ == "__main__":
    main()
