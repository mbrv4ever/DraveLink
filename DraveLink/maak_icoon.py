# Maakt DraveLink.ico vanuit hetzelfde logo als in de app.
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtWidgets import QApplication
import dravelink as dl

def main():
    app = QApplication([])
    sizes = [16, 24, 32, 48, 64, 128, 256]
    pics = [dl.make_logo(s) for s in sizes]
    base = pics[-1]
    # PyQt kan niet rechtstreeks multi-res .ico schrijven; we slaan PNG's op
    # en bouwen de .ico met Pillow als die er is, anders 1 PNG als icoon.
    out_ico = os.path.join(os.path.dirname(os.path.abspath(__file__)), "DraveLink.ico")
    try:
        from PIL import Image
        tmp = []
        for s, pm in zip(sizes, pics):
            fn = "_icon_%d.png" % s
            pm.save(fn, "PNG"); tmp.append(fn)
        imgs = [Image.open(f).convert("RGBA") for f in tmp]
        imgs[0].save(out_ico, format="ICO", sizes=[(s, s) for s in sizes])
        for f in tmp:
            try: os.remove(f)
            except Exception: pass
        print("Icoon gemaakt:", out_ico)
    except Exception as e:
        base.save(out_ico.replace(".ico", ".png"), "PNG")
        print("Pillow niet gevonden, PNG-icoon gemaakt i.p.v. .ico (%s)" % e)

if __name__ == "__main__":
    main()
