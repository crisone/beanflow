from os import path
from datetime import datetime
import csv

import beangulp
from beanflow.common.utils import merge_deals_to_transactions
from beanflow.classifier.rule import classify_by_rules, classify_refund_by_match_expense
from beanflow.classifier.ai import classify_by_ai

class CsvBaseImporter(beangulp.Importer):
    def __init__(self):
        self.account_root = "Assets:FIXME"
        self.file_postfix = ".csv"
        self.encoding = "utf-8"
        self.head_keywords = ""
        self.headline_keywords = ""
        self.filename_prefix = ""

    def identify(self, filepath):
        if filepath.endswith(self.file_postfix):
            try:
                with open(filepath, encoding=self.encoding) as fd:
                    head = fd.read(1024)
                    if self.head_keywords in head:
                        return True
            except Exception as e:
                print(f"Error reading file {filepath}: {e}")
                return False
        return False
    
    def filename(self, filepath):
        return self.filename_prefix + "." + path.basename(filepath)
    
    def extract(self, filepath, existing):
        deals = []
        with open(filepath, encoding=self.encoding) as fd:
            # skip header
            headline_found = False
            prev_pos = 0
            while True:
                line = fd.readline()
                if headline_found and line.strip() != "":
                    fd.seek(prev_pos)
                    break
                if self.headline_keywords in line:
                    headline_found = True
                prev_pos = fd.tell()

            # following is a csv format
            dict_reader = csv.DictReader(fd)
            for row in dict_reader:
                deal = self._row_to_deal_(row)
                if deal is not None:
                    deals.append(deal)

        classify_by_rules(deals)
        classify_by_ai(deals)
        classify_refund_by_match_expense(deals)
        transactions = merge_deals_to_transactions(deals)
        return transactions

    def account(self, filepath):
        return self.account_root
    
    def _row_to_deal_(self, row):
        return None
