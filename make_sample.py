"""サンプル（架空データ）版。Unity に最初から入れておく画像（ダウンロードに失敗したときの表示）。
→ ticker_rows_sample.png（1996x512）, ticker_strip_sample.png（確認用の 1 本）"""
from pathlib import Path
from ticker_lib import render_strip, to_rows

ENTRIES = [
    ("4001", "東和精機", "2,845", +1.43), ("5102", "日昇化学", "1,236", -0.82), ("6203", "大洋海運", "3,910", +0.35),
    ("7304", "北辰食品", "987", -2.10), ("8405", "青空HD", "5,120", +3.02), ("9506", "みなと電力", "1,764", 0.00),
    ("3607", "蒼天ソフト", "2,208", +0.77),
]
here = Path(__file__).parent
strip, info = render_strip(ENTRIES, "※サンプル表示（架空データ）")
to_rows(strip).save(here / "ticker_rows_sample.png")
strip.save(here / "ticker_strip_sample.png")
print("ok", info)
