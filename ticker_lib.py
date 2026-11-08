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


# ---- ボード（壁の青いモニター）用の表 ------------------------------------------------------------
# モニターは 6.84 m x 3.82 m（縦横比 1.79）。VRChat の画像読み込み上限 2048x2048 以下に収める。
BW, BH = 2048, 1144
B_BG_TOP, B_BG_BOT = (16, 44, 138), (24, 66, 176)
B_HEAD = (8, 24, 84)
B_LINE = (70, 110, 200)
B_UP = (255, 104, 92)       # 上昇: 赤（青地で読めるよう少し明るく）
B_DOWN = (96, 236, 156)     # 下落: 緑
B_FLAT = (235, 240, 250)
B_TEXT = (240, 245, 255)
B_DIM = (150, 175, 230)


def fmt_signed(v):
    s = "{:,.0f}".format(abs(v)) if abs(v) >= 1000 else "{:,.1f}".format(abs(v))
    return ("+" if v > 0 else "−" if v < 0 else "") + s


def render_board(rows, note, title="マーケットボード", sub="終値・前日比", foot="データ: Yahoo Finance（yfinance）の日次終値。遅延データで、投資判断には使えません"):
    """rows: [dict(code, name, price(float), change(float), pct(float))]。戻り: PIL Image BWxBH（RGB）。"""
    S = 2
    img = Image.new("RGB", (BW * S, BH * S), B_BG_BOT)
    d = ImageDraw.Draw(img)
    for y in range(BH * S):                       # 縦のグラデーション
        t = y / (BH * S - 1)
        d.line([(0, y), (BW * S, y)], fill=tuple(int(B_BG_TOP[i] + (B_BG_BOT[i] - B_BG_TOP[i]) * t) for i in range(3)))
    F = lambda px: ImageFont.truetype(FONT, int(px * S), index=FONT_INDEX)
    head_h, colh_h, foot_h = 150, 56, 84
    d.rectangle([0, 0, BW * S, head_h * S], fill=B_HEAD)
    d.rectangle([0, head_h * S, BW * S, (head_h + 4) * S], fill=B_LINE)
    d.text((70 * S, 28 * S), title, font=F(76), fill=B_TEXT)
    tw = d.textlength(title, font=F(76)) / S
    d.text(((70 + tw + 36) * S, 70 * S), sub, font=F(40), fill=B_DIM)
    rw = d.textlength(note, font=F(52)) / S
    d.text(((BW - 70 - rw) * S, 46 * S), note, font=F(52), fill=B_TEXT)
    # 列の位置（px）: コード 左 / 銘柄 左 / 終値・前日比・% は右そろえ
    X_CODE, X_NAME, X_PRICE, X_CHG, X_PCT = 70, 250, 1240, 1590, 1970
    y0 = head_h + 4
    for x, t, right in ((X_CODE, "コード", False), (X_NAME, "銘柄", False), (X_PRICE, "終値", True), (X_CHG, "前日比", True), (X_PCT, "騰落率", True)):
        w = d.textlength(t, font=F(34)) / S
        d.text(((x - w if right else x) * S, (y0 + 12) * S), t, font=F(34), fill=B_DIM)
    y0 += colh_h
    avail = BH - y0 - foot_h
    n = max(len(rows), 1)
    rh = min(112, avail / n)
    fs = int(rh * 0.56)
    for i, r in enumerate(rows):
        y = y0 + i * rh
        if i % 2 == 0:
            d.rectangle([0, y * S, BW * S, (y + rh) * S], fill=tuple(int(c * 0.88) for c in B_BG_BOT))
        d.line([(40 * S, (y + rh) * S), ((BW - 40) * S, (y + rh) * S)], fill=B_LINE, width=S)
        pct = r["pct"]
        col = B_UP if pct > 0 else B_DOWN if pct < 0 else B_FLAT
        arrow = "▲" if pct > 0 else "▼" if pct < 0 else "－"
        cy = y + (rh - fs) / 2 - fs * 0.10
        d.text((X_CODE * S, (cy + fs * 0.12) * S), r["code"], font=F(fs * 0.72), fill=B_DIM)
        d.text((X_NAME * S, cy * S), r["name"], font=F(fs), fill=B_TEXT)
        for x, t, c in ((X_PRICE, fmt_price(r["price"]), B_TEXT), (X_CHG, arrow + " " + fmt_signed(r["change"]).lstrip("+−"), col), (X_PCT, "%s%.2f%%" % ("+" if pct > 0 else "−" if pct < 0 else "", abs(pct)), col)):
            w = d.textlength(t, font=F(fs)) / S
            d.text(((x - w) * S, cy * S), t, font=F(fs), fill=c)
    fy = BH - foot_h
    d.rectangle([0, fy * S, BW * S, BH * S], fill=B_HEAD)
    d.rectangle([0, fy * S, BW * S, (fy + 3) * S], fill=B_LINE)
    ups = sum(1 for r in rows if r["pct"] > 0)
    dns = sum(1 for r in rows if r["pct"] < 0)
    d.text((70 * S, (fy + 20) * S), "▲ %d　▼ %d" % (ups, dns), font=F(40), fill=B_TEXT)
    fw = d.textlength(foot, font=F(30)) / S
    d.text(((BW - 70 - fw) * S, (fy + 28) * S), foot, font=F(30), fill=B_DIM)
    return img.resize((BW, BH), Image.LANCZOS)


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
