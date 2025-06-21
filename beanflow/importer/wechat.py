from datetime import datetime

from beanflow.common.deal import IncomeDeal, ExpenseDeal, RefundDeal, TransferDeal
from beanflow.common.utils import guess_account_from_name
from beanflow.importer.base.csv import CsvBaseImporter
from beanflow.config import CONFIG

from beangulp.testing import main

class WechatImporter(CsvBaseImporter):
    def __init__(self):
        super().__init__()
        self.account_root = CONFIG.get("importer.wechat.account_root")
        # file formats
        self.head_keywords = "微信支付账单明细"
        self.headline_keywords = "微信支付账单明细列表"
        self.filename_prefix = "wechat"
    
    def _row_to_deal_(self, row):
        time = datetime.strptime(row["交易时间"], "%Y-%m-%d %H:%M:%S")
        party = row["交易对方"].strip()
        description = row["商品"]
        amount = row["金额(元)"].replace("¥", "").strip()
        pay_method = row["支付方式"].strip()
        if pay_method == "零钱" or pay_method == "/":
            account = self.account_root
        else:
            account = guess_account_from_name(pay_method, ["Assets", "Liabilities"])

        if account is None:
            account = self.account_root

        deal = None
        if row["收/支"] == "支出":
            deal = ExpenseDeal(time, amount, "CNY", party, account)

        if row["收/支"] == "收入":
            if "退款" in row["交易类型"]:
                deal = RefundDeal(time, amount, "CNY", party, account)
                deal.description = "退款 - "
            else:
                deal = IncomeDeal(time, amount, "CNY", party, account)
        
        if row["收/支"] == "/":
            deal = TransferDeal(time, amount, "CNY", self.account_root, account)

        if deal is not None:
            deal.description += description

        return deal

if __name__ == "__main__":
    main(WechatImporter())