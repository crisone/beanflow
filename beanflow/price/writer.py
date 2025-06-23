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

def add_include_to_main_file(price_file_path: str, main_file_path: str):
    """
    在主入口文件中添加 include 语句
    """
    try:
        # 计算相对路径
        main_dir = os.path.dirname(main_file_path)
        relative_path = os.path.relpath(price_file_path, main_dir)
        
        # 读取主文件内容
        with open(main_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否已经包含该文件
        include_line = f'include "{relative_path}"'
        if include_line in content:
            return  # 已经包含，不需要重复添加
        
        # 在文件末尾添加 include 语句
        with open(main_file_path, 'a', encoding='utf-8') as f:
            f.write(f'{include_line}\n')
    except Exception as e:
        print(f"Warning: Failed to add include statement to main file: {e}")

def write_price_file(commodity: str, price_dict: Dict[str, Tuple[float, str]], data_dir: str, overwrite: bool = False, main_file_path: str = None):
    """
    写入/合并价格到 data_dir/{commodity}.bean
    如果是新创建的文件，会在主入口文件中添加 include 语句
    """
    os.makedirs(data_dir, exist_ok=True)
    filepath = os.path.join(data_dir, f"{commodity}.bean")
    
    # 检查文件是否已存在
    file_existed = os.path.exists(filepath)
    
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
    
    # 如果是新创建的文件且提供了主文件路径，添加 include 语句
    if not file_existed and main_file_path and os.path.exists(main_file_path):
        add_include_to_main_file(filepath, main_file_path)
        print(f"Added include statement for {commodity}.bean to main file") 