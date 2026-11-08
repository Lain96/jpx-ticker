"""1 日 1 回（東京市場の引け後）に走らせる。yfinance で終値と前日比を取り、帯の画像（rows, 1996x512）と data.json を作る。
使い方: python fetch_and_render.py [出力フォルダ]   （既定: ./out）
  out/ticker.png … VRChat が読む画像   out/data.json … 確認用（市場日・各銘柄の値）
取得に失敗した銘柄は飛ばす。1 件も取れなければ何も書かず異常終了（前回の画像を残す）。
"""
import json
import sys
import datetime
from pathlib import Path
import yfinance as yf
from ticker_lib import render_strip, to_rows, fmt_price

here = Path(__file__).parent
out = Path(sys.argv[1]) if len(sys.argv) > 1 else here / "out"
out.mkdir(parents=True, exist_ok=True)
cfg = json.loads((here / "tickers.json").read_text(encoding="utf-8"))["symbols"]
entries, data, last_date = [], [], None
for c in cfg:
    try:
        cl = yf.Ticker(c["symbol"]).history(period="10d")["Close"].dropna()
        if len(cl) < 2:
            raise ValueError("not enough rows")
        close, prev = float(cl.iloc[-1]), float(cl.iloc[-2])
        d = cl.index[-1].date()
        chg = round((close - prev) / prev * 100, 2)
        entries.append((c["code"], c["name"], fmt_price(close), chg))
        data.append(dict(symbol=c["symbol"], name=c["name"], close=close, prev_close=prev, change_pct=chg, date=str(d)))
        last_date = max(last_date, d) if last_date else d
    except Exception as e:
        print("skip", c["symbol"], e, file=sys.stderr)
if not entries:
    print("no data; keep previous image", file=sys.stderr)
    sys.exit(1)
note = "終値 %d/%02d/%02d" % (last_date.year, last_date.month, last_date.day)
strip, info = render_strip(entries, note)
to_rows(strip).save(out / "ticker.png", optimize=True)
strip.save(out / "ticker_strip_preview.png")
(out / "data.json").write_text(json.dumps(dict(market_date=str(last_date), data_type="daily_close",
                               generated=datetime.datetime.now(datetime.timezone.utc).isoformat(), stocks=data),
                               ensure_ascii=False, indent=1), encoding="utf-8")
print("ok", len(entries), "entries", note, info)
