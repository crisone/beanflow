import akshare as ak
import yfinance as yf
import pandas as pd
from typing import Dict, Any, Optional
from datetime import datetime, timedelta


# akshare symbol -> yfinance symbol 映射
_CURRENCY_MAP = {
    'stock_zh_a': 'CNY',
    'stock_hk': 'HKD',
    'stock_us': 'USD',
}


def _to_date_fmt(d: str) -> str:
    """yyyymmdd -> yyyy-mm-dd"""
    if len(d) == 8:
        return f"{d[:4]}-{d[4:6]}-{d[6:8]}"
    return d


def _akshare_symbol_to_yfinance(symbol: str, commodity_type: str) -> str:
    """将 akshare 的 symbol 转换为 yfinance 格式。"""
    if commodity_type == 'stock_zh_a':
        # 6 开头是上海 .SS，其余是深圳 .SZ
        suffix = '.SS' if symbol.startswith('6') else '.SZ'
        return symbol + suffix
    elif commodity_type == 'stock_hk':
        # 港股: akshare 用 "00700"，yfinance 用 "0700.HK"
        return symbol.lstrip('0').zfill(4) + '.HK'
    elif commodity_type == 'stock_us':
        # 美股: akshare 用 "105.NVDA"，yfinance 用 "NVDA"
        return symbol.split('.')[-1] if '.' in symbol else symbol
    return symbol


def _fetch_via_yfinance(symbol: str, commodity_type: str, from_date: str, to_date: str) -> Dict[str, Any]:
    """使用 yfinance 获取股票历史价格。"""
    result = {}
    yf_symbol = _akshare_symbol_to_yfinance(symbol, commodity_type)
    currency = _CURRENCY_MAP.get(commodity_type, 'USD')
    # yfinance end date 是 exclusive 的，需要 +1 天
    end_dt = datetime.strptime(to_date, '%Y-%m-%d') + timedelta(days=1)
    df = yf.download(yf_symbol, start=from_date, end=end_dt.strftime('%Y-%m-%d'), progress=False, auto_adjust=False)
    if df.empty:
        return result
    for idx, row in df.iterrows():
        date = idx.strftime('%Y-%m-%d')
        raw = row['Close'].iloc[0] if hasattr(row['Close'], 'iloc') else row['Close']
        price = round(float(raw), 2)
        result[date] = (price, currency)
    return result


def fetch_price_history(commodity: str, commodity_type: str, symbol: str, from_date: str, to_date: str, base_currency: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    获取指定 commodity 在 from_date 到 to_date 区间的历史价格。
    返回 {date: (price, quote_currency)} 字典。
    优先使用 akshare，失败时自动 fallback 到 yfinance（仅股票类型）。
    """
    result = {}
    from_date_fmt = _to_date_fmt(from_date)
    to_date_fmt = _to_date_fmt(to_date)

    if commodity_type == 'currency':
        if not api_key or api_key == 'your-api-key':
            print(f"Skipping {commodity}: No valid API key provided")
            return result
        try:
            df = ak.currency_time_series(
                base=commodity,
                start_date=from_date_fmt,
                end_date=to_date_fmt,
                symbols=base_currency,
                api_key=api_key
            )
            for _, row in df.iterrows():
                date = row['date'].strftime('%Y-%m-%d')
                price = row[base_currency]
                result[date] = (price, base_currency)
        except Exception as e:
            print(f"Currency API error for {commodity}: {e}")
            print(f"Please check your API key and try again")
        return result

    # 股票和基金类型：先尝试 akshare，失败则 fallback yfinance
    try:
        if commodity_type == 'stock_zh_a':
            df = ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date=from_date, end_date=to_date, adjust="")
            for _, row in df.iterrows():
                result[row['日期']] = (row['收盘'], 'CNY')
        elif commodity_type == 'stock_hk':
            df = ak.stock_hk_hist(symbol=symbol, period="daily", start_date=from_date, end_date=to_date, adjust="")
            for _, row in df.iterrows():
                result[row['日期']] = (row['收盘'], 'HKD')
        elif commodity_type == 'stock_us':
            df = ak.stock_us_hist(symbol=symbol, period="daily", start_date=from_date, end_date=to_date, adjust="")
            for _, row in df.iterrows():
                result[row['日期']] = (row['收盘'], 'USD')
        elif commodity_type == 'open_fund':
            df = ak.fund_open_fund_info_em(symbol=symbol, indicator="单位净值走势")
            for _, row in df.iterrows():
                date = row['净值日期']
                if isinstance(date, (datetime, pd.Timestamp)):
                    date = date.strftime('%Y-%m-%d')
                elif hasattr(date, 'strftime'):
                    date = date.strftime('%Y-%m-%d')
                else:
                    date = str(date)
                if from_date_fmt <= date <= to_date_fmt:
                    result[date] = (row['单位净值'], 'CNY')
        else:
            raise ValueError(f"Unknown commodity_type: {commodity_type}")
    except Exception as e:
        print(f"akshare failed for {commodity} ({commodity_type}): {e}")
        # fallback 到 yfinance（仅股票类型，基金不支持）
        if commodity_type in _CURRENCY_MAP:
            print(f"Falling back to yfinance for {commodity} ...")
            try:
                result = _fetch_via_yfinance(symbol, commodity_type, from_date_fmt, to_date_fmt)
            except Exception as e2:
                print(f"yfinance also failed for {commodity}: {e2}")

    return result