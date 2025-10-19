from datetime import datetime

from beanflow.common.deal import IncomeDeal, ExpenseDeal, RefundDeal, TransferDeal
from beanflow.common.utils import guess_account_from_name
from beanflow.importer.base.csv import CsvBaseImporter
from beanflow.config import CONFIG

from beangulp.testing import main

class AlipayImporter(CsvBaseImporter):
    def __init__(self):
        super().__init__()
        self.account_root = CONFIG.get("importer.alipay.account_root")
        self.liability_root = CONFIG.get("importer.alipay.liability_root")
        self.temp_account = CONFIG.get("importer.alipay.temp_account")
        # file formats
        self.encoding = "gb18030"
        self.head_keywords = "支付宝"
        self.headline_keywords = "电子客户回单"
        self.filename_prefix = "alipay"
    
    def _row_to_deal_(self, row):
        time = datetime.strptime(row["交易时间"], "%Y-%m-%d %H:%M:%S")
        party = row["交易对方"].strip()
        description = row["商品说明"]
        category_hint = row["交易分类"]
        amount = row["金额"]
        pay_method = row["收/付款方式"].strip()
        deal_status = row["交易状态"].strip()
        if pay_method == "" or pay_method == "账户余额":
            account = self.temp_account
        elif pay_method == "余额宝":
            account = self.account_root
        else:
            account = guess_account_from_name(pay_method, ["Assets", "Liabilities"])
        
        if account is None:
            account = self.account_root

        deal = None
        if row["收/支"] == "支出":
            deal = ExpenseDeal(time, amount, "CNY", party, account)
            if "极速退款买家主动还款" in description:
                deal.description = "先退款后取消 "
                deal.need_confirm = True

        if row["收/支"] == "收入" and row["交易状态"] == "交易成功":
            deal = IncomeDeal(time, amount, "CNY", party, account)

        if row["收/支"] == "不计收支":
            if deal_status == "交易关闭":
                deal = None
            elif deal_status == "退款成功":
                deal = RefundDeal(time, amount, "CNY", party, account)
            elif "余额宝" in description and "收益发放" in description:
                deal = IncomeDeal(time, amount, "CNY", party, account)
                deal.category = "Income:Investment:Alipay"
            elif "余额宝" in description and "入" in description:
                deal = TransferDeal(time, amount, "CNY", account, self.account_root)
            elif "还款" in description:
                from_account = guess_account_from_name(pay_method, ["Assets"]) or "Assets:FIXME"
                to_account = guess_account_from_name(party, ["Liabilities"]) or "Liabilities:FIXME"
                deal = TransferDeal(time, amount, "CNY", from_account, to_account)    
                if "FIXME" in from_account or "FIXME" in to_account:
                    deal.need_confirm = True
            elif account != self.temp_account:
                to_account = guess_account_from_name(party, ["Assets"]) or "Assets:FIXME"
                deal = TransferDeal(time, amount, "CNY", self.account_root, to_account)
            else:
                to_account = "Assets:FIXME"
                deal = TransferDeal(time, amount, "CNY", account, to_account)
                deal.need_confirm = True

        if deal is not None:
            deal.description += description
            deal.category_hint = category_hint

        return deal

if __name__ == "__main__":
    main(AlipayImporter())