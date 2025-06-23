import os
from typing import Dict, Tuple

def read_existing_prices(filepath: str) -> Dict[str, Tuple[float, str]]:
    prices = {}
    if not os.path.exists(filepath):
        return prices
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or not line.startswith('20'):
                continue
            parts = line.split()
            if len(parts) >= 5 and parts[2] == 'price':
                date, _, _, price, currency = parts[0], parts[2], parts[3], parts[4], parts[5]
                prices[date] = (float(price), currency)
    return prices

def write_price_file(commodity: str, price_dict: Dict[str, Tuple[float, str]], data_dir: str, overwrite: bool = False):
    """
    写入/合并价格到 data_dir/{commodity}.bean
    """
    os.makedirs(data_dir, exist_ok=True)
    filepath = os.path.join(data_dir, f"{commodity}.bean")
    
    if not overwrite:
        existing = read_existing_prices(filepath)
        existing.update(price_dict)
        price_dict = existing
    elif not price_dict:
        # 如果覆盖模式且没有新数据，保持原文件不变
        return
    
    # 按日期排序
    lines = []
    for date in sorted(price_dict.keys()):
        price, currency = price_dict[date]
        lines.append(f"{date} price {commodity}   {price} {currency}")
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n') 