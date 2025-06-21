from datetime import datetime

from beanflow.common.deal import ExpenseDeal, RefundDeal
from beanflow.common.utils import guess_account_from_name
from beanflow.importer.base.csv import CsvBaseImporter
from beanflow.config import CONFIG

from beangulp.testing import main

class MeituanImporter(CsvBaseImporter):
    def __init__(self):
        super().__init__()
        self.account_root = CONFIG.get("importer.meituan.account_root")
        # file formats
        self.head_keywords = "美团交易账单明细"
        self.headline_keywords = "美团交易账单明细列表"
        self.filename_prefix = "meituan"
    
    def _row_to_deal_(self, row):
        time = datetime.strptime(row["交易成功时间"], "%Y-%m-%d %H:%M:%S")
        party = "美团"
        description = row["订单标题"]
        amount = row["实付金额"].replace("¥", "").strip()
        pay_method = row["支付方式"].strip()
        account = self.account_root

        if pay_method in CONFIG.get("importer.meituan.ignored_pay_methods", []):
            return None
        
        if pay_method == "美团余额":
            account = self.account_root
        else:
            account = guess_account_from_name(pay_method, ["Assets", "Liabilities", "Equity"])

        if account is None:
            account = self.account_root

        deal = None
        if row["收/支"] == "支出":
            deal = ExpenseDeal(time, amount, "CNY", party, account)

        if row["收/支"] == "收入" and row["交易类型"] == "退款":
            deal = RefundDeal(time, amount, "CNY", party, account)
            deal.description = "退款 - "

        if deal is not None:
            deal.description += description

        return deal

if __name__ == "__main__":
    main(MeituanImporter())