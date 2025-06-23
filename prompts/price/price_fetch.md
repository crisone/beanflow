# 需求概述
我希望你为beanflow 实现一个功能，完成对账本内所有 commodity 的历史价格的查询和记录，详细需求如下:

## 账本内 commodity 信息获取
通过 beancount python 库本身的接口读取 beancount 账本（入口位于 config 的 common.beancount_main 之下），获取到所有 commodity 声明以及其附加的 meta 信息，
对于 meta 信息，我们指定了key 为 "commodity_type" 来进行标识，其中 value 包括：
- currency: 货币
- stock_zh_a: 中国A股
- stock_hk: 香港股市
- stock_us: 美国股市
- open_fund: 中国登记的合法公募基金

## 账本内基准货币获取
一种获取beancount 账本内基准货币的方法如下所示：
```python
from beancount.loader import load_file

entries, errors, options = load_file("your_ledger.beancount")
operating_currencies = options["operating_currency"]
```

## 配置文件说明
```yaml
common:
  beancount_main: prompts/price/example.bean
price:
  data_dir: commodity_price
  currency_api_key: Dtt3V5jxmXuFNHq97BpWKd14r30KhGao
```
其中 
- beancount_main 定义了 beancount 账本的入口文件
- data_dir 定义了写入价格文件的文件夹
- currency_api_key 定义了查询货币汇率时使用的 api_key

## 命令行功能
```bash
 beanflow price --from 20250615 --to 20250622 --overwrite
```
其中：
- 如果不加 to 参数，默认为当日时间
- 如果不加 from 参数，默认和to参数保持一致
- --overwrite 为可选参数，表示是否要覆盖已有的价格数据

运行命令行之后应该将查询到的价格更新到 price.data_dir 下的指定文件中

## 文件更新规则
每一种 commodity 在 price.data_dir 之下有自己的一个单独的.bean文件用于记录历史价格数据。其中内容符合 beancount 对于 price 声明的定义格式，如:
```
2014-05-25 price IBM   182.27 USD
```

当通过beanflow查询历史价格数据时，按照以下规则进行更新：
- 如果文件不存在，则新建文件，并将查询到的所有历史价格数据写入
- 如果文件存在，则读取文件中的内容，根据命令行参数选择是否覆盖已有日期的历史数据，最后重新排序并按照时间排序输出到文件中。

## commodity 价格获取接口
commodity的价格均使用 akshare 这个库进行获取
### currency
接口调用示例（获取 USD 相对于 CNY 的价格）
```
currency_time_series_df = ak.currency_time_series(base="USD", start_date="2023-02-03", end_date="2023-03-04", symbols="", api_key="your-api-key")
```
接口文档链接：https://akshare.akfamily.xyz/data/currency/currency.html#id2

对于查询每一种货币的价格，需要将该货币设置为 base，将 基准货币 设置为 symbols

### stock_zh_a
示例
```
stock_zh_a_hist_df = ak.stock_zh_a_hist(symbol="000001", period="daily", start_date="20170301", end_date='20240528', adjust="")
```
接口文档链接：https://akshare.akfamily.xyz/data/stock/stock.html#id22

其中 symbol 可以在 commodity 的 meta 信息中找到
查询出来的数据以当日的收盘价为准，单位货币为 CNY

### stock_hk

示例
```
stock_hk_hist_df = ak.stock_hk_hist(symbol="00593", period="daily", start_date="19700101", end_date="22220101", adjust="")
```
接口文档链接：https://akshare.akfamily.xyz/data/stock/stock.html#id70

其中 symbol 可以在 commodity 的 meta 信息中找到
查询出来的数据以当日的收盘价为准，单位货币为 HKD

### stock_us
示例
```
stock_us_hist_df = ak.stock_us_hist(symbol='106.TTE', period="daily", start_date="20200101", end_date="20240214", adjust="")
```
接口文档链接：https://akshare.akfamily.xyz/data/stock/stock.html#id58

其中 symbol 可以在 commodity 的 meta 信息中找到
查询出来的数据以当日的收盘价为准，单位货币为 USD

### open_fund
示例
```
fund_open_fund_info_em_df = ak.fund_open_fund_info_em(symbol="710001", indicator="单位净值走势")
```
接口文档链接：https://akshare.akfamily.xyz/data/fund/fund_public.html#id15

其中 symbol 可以在 commodity 的 meta 信息中找到
查询出来的数据以单位净值为准，单位货币为 CNY


## 其他开发要求
- 不要使用 venv，需要运行 pip 时，直接安装即可
- 不要修改 .beanflow/config.yaml，我已修改好
- 记得更新配置管理 python 文件中的默认配置