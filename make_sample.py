"""サンプル（架空データ）版。Unity に最初から入れておく画像（ダウンロードに失敗したときの表示）。
→ ticker_rows_sample.png（1996x512, 円柱の帯）, ticker_strip_sample.png（確認用の 1 本）, board_sample.png（2048x1144, 壁のモニター）"""
from pathlib import Path
from ticker_lib import render_strip, to_rows, render_board

ENTRIES = [
    ("4001", "東和精機", "2,845", +1.43), ("5102", "日昇化学", "1,236", -0.82), ("6203", "大洋海運", "3,910", +0.35),
    ("7304", "北辰食品", "987", -2.10), ("8405", "青空HD", "5,120", +3.02), ("9506", "みなと電力", "1,764", 0.00),
    ("3607", "蒼天ソフト", "2,208", +0.77),
]
BOARD = [  # 架空の銘柄（code, name, 終値, 前日比, 騰落率%）
    ("4001", "東和精機", 2845.0, +40.0, +1.43), ("5102", "日昇化学", 1236.0, -10.2, -0.82), ("6203", "大洋海運", 3910.0, +13.7, +0.35),
    ("7304", "北辰食品", 987.0, -21.2, -2.10), ("8405", "青空HD", 5120.0, +150.0, +3.02), ("9506", "みなと電力", 1764.0, 0.0, 0.00),
    ("3607", "蒼天ソフト", 2208.0, +16.8, +0.77),
]
here = Path(__file__).parent
strip, info = render_strip(ENTRIES, "※サンプル表示（架空データ）")
to_rows(strip).save(here / "ticker_rows_sample.png")
strip.save(here / "ticker_strip_sample.png")
rows = [dict(code=c, name=n, price=p, change=ch, pct=pc) for c, n, p, ch, pc in BOARD]
render_board(rows, "※サンプル表示（架空データ）", foot="架空のデータです。実際の株価ではありません").save(here / "board_sample.png", optimize=True)
print("ok", info)
