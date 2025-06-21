import re

from datetime import datetime

from beanflow.common.deal import ExpenseDeal, RefundDeal, TransferDeal
from beanflow.common.utils import guess_account_from_name
from beanflow.importer.base.csv import CsvBaseImporter
from beanflow.config import CONFIG

from beangulp.testing import main

class JdImporter(CsvBaseImporter):
    def __init__(self):
        super().__init__()
        self.account_root = CONFIG.get("importer.jd.account_root")
        self.liability_root = CONFIG.get("importer.jd.liability_root")
        # file formats
        self.head_keywords = "京东账号名"
        self.headline_keywords = "本明细仅供个人对账使用"
        self.filename_prefix = "jd"
    
    def _row_to_deal_(self, row):
        time = datetime.strptime(row["交易时间"].strip(), "%Y-%m-%d %H:%M:%S")
        party = row["商户名称"].strip()
        description = row["交易说明"]
        amount = re.search(r"\d+\.\d+", row["金额"]).group(0)
        deal_status = row["交易状态"].strip()
        category_hint = row["交易分类"]
        pay_method = row["收/付款方式"].strip()
        if pay_method in CONFIG.get("importer.jd.ignored_pay_methods", []):
            return None

        account = self.account_root
        if pay_method == "钱包余额":
            account = self.account_root
        elif pay_method == "京东白条":
            account = self.liability_root
        else:
            account = guess_account_from_name(pay_method, ["Assets", "Liabilities", "Equity"])

        if account is None:
            account = self.account_root

        deal = None
        if deal_status == "交易成功":
            deal = ExpenseDeal(time, amount, "CNY", party, account)

        if deal_status == "退款成功":
            deal = RefundDeal(time, amount, "CNY", party, account)

        if deal_status == "还款成功":
            deal = TransferDeal(time, amount, "CNY", account, self.liability_root)
        
        if deal is not None:
            deal.description += description
            deal.category_hint = category_hint
            deal.meta["order_id"] = row["交易订单号"]

        return deal

    def account(self, filepath):
        return self.account_root

if __name__ == "__main__":
    main(JdImporter())