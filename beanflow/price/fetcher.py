import akshare as ak
import pandas as pd
from typing import Dict, Any, Optional
from datetime import datetime

def fetch_price_history(commodity: str, commodity_type: str, symbol: str, from_date: str, to_date: str, base_currency: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    获取指定 commodity 在 from_date 到 to_date 区间的历史价格。
    返回 {date: (price, quote_currency)} 字典。
    """
    result = {}
    try:
        # 统一日期格式：将 yyyymmdd 转换为 yyyy-mm-dd
        if len(from_date) == 8:
            from_date_fmt = f"{from_date[:4]}-{from_date[4:6]}-{from_date[6:8]}"
        else:
            from_date_fmt = from_date
        if len(to_date) == 8:
            to_date_fmt = f"{to_date[:4]}-{to_date[4:6]}-{to_date[6:8]}"
        else:
            to_date_fmt = to_date
            
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
        elif commodity_type == 'stock_zh_a':
            df = ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date=from_date, end_date=to_date, adjust="")
            for _, row in df.iterrows():
                date = row['日期']
                price = row['收盘']
                result[date] = (price, 'CNY')
        elif commodity_type == 'stock_hk':
            df = ak.stock_hk_hist(symbol=symbol, period="daily", start_date=from_date, end_date=to_date, adjust="")
            for _, row in df.iterrows():
                date = row['日期']
                price = row['收盘']
                result[date] = (price, 'HKD')
        elif commodity_type == 'stock_us':
            df = ak.stock_us_hist(symbol=symbol, period="daily", start_date=from_date, end_date=to_date, adjust="")
            for _, row in df.iterrows():
                date = row['日期']
                price = row['收盘']
                result[date] = (price, 'USD')
        elif commodity_type == 'open_fund':
            df = ak.fund_open_fund_info_em(symbol=symbol, indicator="单位净值走势")
            for _, row in df.iterrows():
                date = row['净值日期']
                price = row['单位净值']
                # 确保日期是字符串格式
                if isinstance(date, (datetime, pd.Timestamp)):
                    date = date.strftime('%Y-%m-%d')
                elif hasattr(date, 'strftime'):  # 处理 datetime.date 对象
                    date = date.strftime('%Y-%m-%d')
                else:
                    date = str(date)  # 其他情况直接转字符串
                # 使用转换后的日期格式进行比较
                if from_date_fmt <= date <= to_date_fmt:
                    result[date] = (price, 'CNY')
        else:
            raise ValueError(f"Unknown commodity_type: {commodity_type}")
    except Exception as e:
        print(f"Error fetching {commodity} ({commodity_type}): {e}")
    return result 