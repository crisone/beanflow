# Beanflow
Beanflow 是一个使得使用 beancount 进行记账的体验更加高效流畅的软件。其中主要包含多种账单的导入器、分类器以及商品价格获取工具。

## 安装

```bash
pip install -e .
```

## 功能

### 账单导入

支持以下平台的账单导入：

- 支付宝（Alipay）
- 微信支付（WeChat Pay）
- 京东（JD）
- 美团（Meituan）

```bash
beanflow import -e alipay extract /path/to/alipay.csv
beanflow import -e wechat extract /path/to/wechat.csv
beanflow import -e meituan extract /path/to/meituan.csv
```

### 商品价格获取

自动获取股票、基金、外汇的历史价格并写入 beancount 格式文件。

支持的商品类型：

| commodity_type | 说明 | 数据源 |
|---|---|---|
| `stock_zh_a` | A 股 | akshare / yfinance |
| `stock_hk` | 港股 | akshare / yfinance |
| `stock_us` | 美股 | akshare / yfinance |
| `open_fund` | 开放式基金 | akshare |
| `currency` | 外汇 | akshare（需 API key） |

当 akshare 数据源不可用时（如东方财富 API 限流或网络限制），股票类型会自动 fallback 到 yfinance。

```bash
# 获取今天的价格
beanflow price

# 指定日期范围
beanflow price --from 20250615 --to 20250622

# 覆盖已有数据
beanflow price --from 20250101 --to 20250601 --overwrite
```

## 配置

在项目目录下创建 `.beanflow/config.yaml`：

```yaml
common:
  beancount_main: main.bean

price:
  data_dir: commodity_price
  currency_api_key: your-api-key  # 仅外汇需要
```

商品需要在 beancount 文件中通过 metadata 声明类型和代码：

```beancount
2020-01-01 commodity BIYADI
  commodity_type: "stock_zh_a"
  symbol: "002594"

2020-01-01 commodity NVDA
  commodity_type: "stock_us"
  symbol: "105.NVDA"
```
