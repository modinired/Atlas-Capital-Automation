
from typing import Dict as _Dict5, Any as _Any5
import datetime as _dt
import yfinance as _yf

class DataBrain:
    def pull_financial_timeseries(self, ticker: str, start: str, end: str, interval: str = "1d") -> _Dict5[str, _Any5]:
        s = _dt.datetime.fromisoformat(start)
        e = _dt.datetime.fromisoformat(end)
        data = _yf.download(ticker, start=s, end=e, interval=interval, progress=False)
        if data is None or data.empty:
            raise ValueError(f"No data for {ticker} {start}->{end}")
        data = data.rename(columns={c: c.lower() for c in data.columns})
        return {
            "ticker": ticker,
            "start": start,
            "end": end,
            "interval": interval,
            "rows": [
                {
                    "ts": idx.isoformat(),
                    "open": float(row.get("open", 0)),
                    "high": float(row.get("high", 0)),
                    "low": float(row.get("low", 0)),
                    "close": float(row.get("close", 0)),
                    "volume": float(row.get("volume", 0)),
                }
                for idx, row in data.iterrows()
            ],
        }
