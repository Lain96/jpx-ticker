"""株価ティッカー帯の描画（サンプル版・実データ版で共通）。
帯: 半径 8.9 m・高さ 0.9 m・周 55.92 m の円筒面。1 周ぶんを幅 7952 px × 高さ 128 px の 1 枚（strip）に描く。
VRChat の VRCImageDownloader は 2048x2048 以下しか読めないので、strip を 4 つに切って縦に積んだ 1 枚（rows, 1996x512）にして配る。
rows: セグメント i（0..3）は下から i 段目（PNG では上から 3-i 段目）。各段の左右に 4 px ずつ、隣のセグメントの端を重ねて入れる
（i=0 の左は i=3 の右端、i=3 の右は i=0 の左端）。シェーダー JPX/TickerScroll がこれを元の帯に戻す。
"""
import math
import os
from PIL import Image, ImageDraw, ImageFont

H = 128
CIRC = 2 * math.pi * 8.9
W = int(round(CIRC / 0.9 * H / 16)) * 16        # 7952（4 分割しても 4 の倍数）
SEGS = 4
SEGW = W // SEGS                                # 1988
PAD = 4
ROWW = SEGW + 2 * PAD                           # 1996
SS = 2
# 日本語の太字フォント。Windows は游ゴシック Bold、Linux（GitHub Actions: apt の fonts-noto-cjk）は Noto Sans CJK JP Bold
_FONTS = [(r"C:\Windows\Fonts\YuGothB.ttc", 0), ("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc", 0), ("/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc", 0)]
FONT, FONT_INDEX = next(((p, i) for p, i in _FONTS if os.path.exists(p)), (_FONTS[0][0], 0))
BG = (5, 9, 22)
C_CODE = (140, 160, 195)
C_NAME = (235, 240, 250)
C_PRICE = (255, 255, 255)
C_UP = (255, 72, 60)        # 上昇: 赤
C_DOWN = (60, 225, 130)     # 下落: 緑
C_FLAT = (235, 240, 250)
C_NOTE = (120, 135, 165)


def fmt_price(v):
    if v >= 1000:
        return "{:,.0f}".format(v)
    return "{:,.1f}".format(v) if v >= 100 else "{:,.2f}".format(v)


def render_strip(entries, note, font_px=66):
    """entries: [(code, name, price_str, change_pct)]。幅に収まらなければ文字を小さくする。"""
    probe = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    gap_in = 28 * SS
    while True:
        f = ImageFont.truetype(FONT, font_px * SS, index=FONT_INDEX)
        fsm = ImageFont.truetype(FONT, int(font_px * SS * 0.62), index=FONT_INDEX)
        blocks = []
        for code, name, price, chg in entries:
            if chg > 0:
                arrow, col = "▲", C_UP
            elif chg < 0:
                arrow, col = "▼", C_DOWN
            else:
                arrow, col = "－", C_FLAT
            parts = [(code, fsm, C_CODE), (name, f, C_NAME), (price, f, C_PRICE), ("%s%.2f%%" % (arrow, abs(chg)), f, col)]
            w = sum(probe.textlength(t, font=ft) for t, ft, _ in parts) + gap_in * (len(parts) - 1)
            blocks.append((parts, w))
        blocks.append(([(note, fsm, C_NOTE)], probe.textlength(note, font=fsm)))
        total = sum(w for _, w in blocks)
        gap_out = (W * SS - total) / len(blocks)
        if gap_out >= 90 * SS or font_px <= 40:
            break
        font_px -= 2
    img = Image.new("RGB", (W * SS, H * SS), BG)
    d = ImageDraw.Draw(img)
    x = gap_out / 2
    for parts, w in blocks:
        cx = x
        for t, ft, col in parts:
            bb = d.textbbox((0, 0), "田", font=ft)
            cy = (H * SS - (bb[3] + bb[1])) / 2 - 1 * SS
            d.text((cx, cy), t, font=ft, fill=col)
            cx += probe.textlength(t, font=ft) + gap_in
        dx = x + w + gap_out / 2
        r = 7 * SS
        d.polygon([(dx, H * SS / 2 - r), (dx + r, H * SS / 2), (dx, H * SS / 2 + r), (dx - r, H * SS / 2)], fill=(60, 80, 130))
        x += w + gap_out
    d.rectangle([0, 0, W * SS, 3 * SS], fill=(18, 30, 62))
    d.rectangle([0, H * SS - 3 * SS, W * SS, H * SS], fill=(18, 30, 62))
    return img.resize((W, H), Image.LANCZOS), dict(font_px=font_px, gap_out_px=round(gap_out / SS), blocks=len(blocks))


def _wrap_crop(strip, x0, n):
    """strip の x0 から n px（帯は輪なので端をまたいでもよい）。"""
    x0 %= W
    if x0 + n <= W:
        return strip.crop((x0, 0, x0 + n, H))
    a = strip.crop((x0, 0, W, H))
    b = strip.crop((0, 0, x0 + n - W, H))
    out = Image.new("RGB", (n, H))
    out.paste(a, (0, 0))
    out.paste(b, (W - x0, 0))
    return out


def to_rows(strip):
    """strip(7952x128) → rows(1996x512)。"""
    out = Image.new("RGB", (ROWW, H * SEGS), BG)
    for i in range(SEGS):
        y = (SEGS - 1 - i) * H
        out.paste(_wrap_crop(strip, i * SEGW - PAD, ROWW), (0, y))   # 左の重なり + 中身 + 右の重なり
    return out
