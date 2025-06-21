from enum import Enum
from datetime import datetime

from beancount.core import flags
from beancount.core.amount import Amount
from beancount.core.data import Transaction, Posting, EMPTY_SET, new_metadata
from beancount.core.number import D

class DealType(Enum):
    INCOME = "Income"
    EXPENSE = "Expense"
    REFUND = "Refund"
    TRANSFER = "Transfer"

class Deal():
    def __init__(self, time: datetime, type: DealType, amount: str, unit: str):
        assert float(amount) >= 0, f"amount must be positive, but got {amount}"
        self.time = time
        self.type = type
        self.amount = amount
        self.unit = unit
        self.category = None
        self.description = ""
        self.category_hint = ""
        self.tags = []
        self.meta = {}
        self.need_confirm = False
    
    def to_transaction(self):
        meta = new_metadata(None, 0)
        txn = Transaction(
            meta=meta,
            date=self.time.date(),
            flag=flags.FLAG_OKAY if not self.need_confirm else flags.FLAG_WARNING,
            payee=self.party,
            narration=self.description,
            tags=EMPTY_SET,
            links=EMPTY_SET,
            postings=self.beancount_postings()
        )
        return txn
    
    def beancount_postings(self):
        return []
    
class ExpenseDeal(Deal):
    def __init__(self, time: datetime, amount: str, unit: str, payee: str, account: str):
        super().__init__(time, DealType.EXPENSE, amount, unit)
        self.payee = payee
        self.account = account

    @property
    def party(self):
        return self.payee
    
    def beancount_postings(self):
        category = self.category or "Expenses:Default"
        return [
            Posting(self.account, -Amount(D(self.amount), self.unit), None, None, None, None),
            Posting(category, Amount(D(self.amount), self.unit), None, None, None, None),
        ]

    def __str__(self):
        return f"{self.time} {self.type} {self.amount} {self.unit} {self.payee} {self.account} | {self.category}"

class IncomeDeal(Deal):
    def __init__(self, time: datetime, amount: str, unit: str, source: str, account: str):
        super().__init__(time, DealType.INCOME, amount, unit)
        self.source = source
        self.account = account
    
    @property
    def party(self):
        return self.source
    
    def beancount_postings(self):
        category = self.category or "Income:Default"
        return [
            Posting(self.account, Amount(D(self.amount), self.unit), None, None, None, None),
            Posting(category, -Amount(D(self.amount), self.unit), None, None, None, None),
        ]
    
    def __str__(self):
        return f"{self.time} {self.type} {self.amount} {self.unit} {self.source} {self.account} | {self.category}"

class RefundDeal(Deal):
    def __init__(self, time: datetime, amount: str, unit: str, payee: str, account: str):
        super().__init__(time, DealType.REFUND, amount, unit)
        self.payee = payee
        self.account = account

    @property
    def party(self):
        return self.payee
    
    def beancount_postings(self):
        category = self.category or "Expenses:Default"
        return [
            Posting(self.account, Amount(D(self.amount), self.unit), None, None, None, None),
            Posting(category, -Amount(D(self.amount), self.unit), None, None, None, None),
        ]
    
    def __str__(self):
        return f"{self.time} {self.type} {self.amount} {self.unit} {self.payee} {self.account} | {self.category}"

class TransferDeal(Deal):
    def __init__(self, time: datetime, amount: str, unit: str, from_account: str, to_account: str):
        super().__init__(time, DealType.TRANSFER, amount, unit)
        self.from_account = from_account
        self.to_account = to_account
        self.to_account_name = ""

    @property
    def party(self):
        return self.to_account_name
    
    def beancount_postings(self):
        return [
            Posting(self.from_account, -Amount(D(self.amount), self.unit), None, None, None, None),
            Posting(self.to_account, Amount(D(self.amount), self.unit), None, None, None, None),
        ]
    
    def __str__(self):
        return f"{self.time} {self.type} {self.amount} {self.unit} {self.from_account} | {self.to_account}"
