import os
from datetime import datetime
from beancount.loader import load_file
from beanflow.config.config_manager import ConfigManager
from beanflow.price.fetcher import fetch_price_history
from beanflow.price.writer import write_price_file

def run_price_fetch(from_date: str = None, to_date: str = None, overwrite: bool = False):
    config = ConfigManager()
    beancount_main = config.get('common.beancount_main')
    data_dir = config.get('price.data_dir', 'commodity_price')
    api_key = config.get('price.currency_api_key')

    entries, errors, options = load_file(beancount_main)
    operating_currencies = options.get('operating_currency', ['CNY'])
    base_currency = operating_currencies[0] if operating_currencies else 'CNY'

    # 日期处理
    today = datetime.today().strftime('%Y-%m-%d')
    if not to_date:
        to_date = today
    if not from_date:
        from_date = to_date
    # 统一格式 yyyy-mm-dd -> yyyymmdd
    from_date_fmt = from_date.replace('-', '')
    to_date_fmt = to_date.replace('-', '')

    # 遍历 commodity
    for entry in entries:
        if entry.__class__.__name__ == 'Commodity':
            meta = entry.meta or {}
            commodity = entry.currency
            commodity_type = meta.get('commodity_type')
            symbol = meta.get('symbol', commodity)
            if not commodity_type:
                continue
            print(f"Fetching {commodity} ({commodity_type}) ...")
            try:
                price_dict = fetch_price_history(
                    commodity=commodity,
                    commodity_type=commodity_type,
                    symbol=symbol,
                    from_date=from_date_fmt,
                    to_date=to_date_fmt,
                    base_currency=base_currency,
                    api_key=api_key
                )
                write_price_file(commodity, price_dict, data_dir, overwrite=overwrite, main_file_path=beancount_main)
            except Exception as e:
                print(f"Failed to fetch {commodity}: {e}") 