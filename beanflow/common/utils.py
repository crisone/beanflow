import re
import json
import os
from typing import List

from collections import defaultdict
from dotenv import load_dotenv
from beanflow.common.deal import Deal, DealType

import openai

from beancount.core import flags
from beancount.core.amount import Amount
from beancount.core.data import Transaction, Posting, Open, new_metadata, EMPTY_SET
from beancount.core.number import D
from beancount.loader import load_file

from beanflow.config import CONFIG

GUESS_CACHE = {}

def get_accounts_by_types(types: List[str]) -> List[str]:
    main_beanfile = CONFIG.get("common.beancount_main")
    entries, errors, options = load_file(main_beanfile)
    if errors:
        print(f"Warning: Errors loading {main_beanfile}: {errors}")
    accounts = []
    for entry in entries:
        if isinstance(entry, Open):
            if any(type in entry.account for type in types):
                accounts.append(entry.account)
    return accounts

def find_account_by_tail_no(tail_no: str) -> List[str]:
    main_beanfile = CONFIG.get("common.beancount_main")
    entries, errors, options = load_file(main_beanfile)
    if errors:
        print(f"Warning: Errors loading {main_beanfile}: {errors}")
    for entry in entries:
        if isinstance(entry, Open):
            if(entry.account.endswith(tail_no)):
                return entry.account
    return None

def guess_account_by_ai(description: str, account_types: List[str]) -> str:
    """
    Use AI to guess the most appropriate account based on input string and account types.
    
    Args:
        description: String description to help identify the account
        account_types: List of account types to consider (e.g. ["Liabilities"])
        
    Returns:
        The guessed account name, or None if no good match is found
    """
    if description in GUESS_CACHE:
        return GUESS_CACHE[description]
    
    # Get valid accounts of the specified types
    valid_accounts = get_accounts_by_types(account_types)
    if not valid_accounts:
        return None
        
    prompt = f"""
请根据以下描述，从给定的账户列表中选择最合适的账户。如果找不到合适的账户，请返回 "None"。

描述: {description}
可选的账户列表:
{json.dumps(valid_accounts, indent=2, ensure_ascii=False)}

请只返回账户名称或 "None"，不要包含任何其他解释。
"""
    
    try:
        client = openai.OpenAI(
                api_key=CONFIG.get("llm_provider.api_key"),
                base_url=CONFIG.get("llm_provider.base_url")
            )
        print("Querying AI guessing account: ", description, " ...")
        response = client.chat.completions.create(
            model=CONFIG.get("llm_provider.model"),
            messages=[
                {"role": "system", "content": "你是一个专业的财务账户识别助手。你的任务是根据描述找到最匹配的账户名称。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,  # Low temperature for more consistent results
        )

        result = response.choices[0].message.content.strip()
        
        print("Querying AI guessing account: ", description, " : ", result)

        if result == "None":
            return None
            
        # Verify the result is actually in our valid accounts list
        if result in valid_accounts:
            GUESS_CACHE[description] = result
            return result
        return None
            
    except Exception as e:
        print(f"Error in AI account guessing: {str(e)}")
        return None

def guess_account_from_name(name: str, account_types: List[str]) -> str:
    # match last four digits from deal_party_name, match from the end of the string
    match = re.search(r'.*(\d{4}).*$', name)
    if match:
        tail_no = match.group(1)
        return find_account_by_tail_no(tail_no)
    else:
        return guess_account_by_ai(name, account_types)

def filter_deals_by_types(deals: List[Deal], types: List[DealType]) -> List[Deal]:
    return [deal for deal in deals if deal.type in types]


def merge_deals_to_transactions(deals: List[Deal]) -> List[Transaction]:
    transactions = []
    deals.sort(key=lambda x: x.time)
    deals_by_time = defaultdict(list)
    for deal in deals:
        deals_by_time[deal.time].append(deal)
    for time, deals in deals_by_time.items():
        meta = new_metadata(None, 0)
        if len(deals) > 1: 
            narration = "多笔交易合并"
            postings = []
            amount_total_dict = {}
            need_confirm = False
            for deal in deals:
                if deal.need_confirm:
                    need_confirm = True
                if deal.account not in amount_total_dict:
                    amount_total_dict[deal.account] = 0
                amount_total_dict[deal.account] += float(deal.amount)
                postings.append(Posting(
                    account=deal.category or "Expenses:Default",
                    units=Amount(D(deal.amount), deals[0].unit),
                    cost=None,
                    price=None,
                    flag=None,
                    meta={"payee": deal.payee, "description": deal.description}
                ))
            for account, amount in amount_total_dict.items():
                postings.append(Posting(
                    account=account,
                    units=-Amount(D(str(round(amount, 2))), deals[0].unit),
                    cost=None,
                    price=None,
                    flag=None,
                    meta=None
                ))
            txn = Transaction(
                meta=meta,
                date=time.date(),
                flag=flags.FLAG_OKAY if not need_confirm else flags.FLAG_WARNING,
                payee= None,
                narration=narration,
                tags=EMPTY_SET,
                links=EMPTY_SET,
                postings=postings
            )
            
        else:
            txn = deals[0].to_transaction()
        print(txn)
        transactions.append(txn)
    return transactions

def filter_duplicated_transactions(transactions: List[Transaction], beanfiles: List[str]) -> List[Transaction]:
    """
    过滤掉已经在 bean 文件中存在的交易记录。
    判断重复的逻辑是：
    1. 交易日期发生在同一天
    2. Transaction 中含有同一个 Assets 或者 Liability 类型的账户，产生了相同金额的变动
    3. Assets 和 Liability 类型通过 Posting.account 前缀判断
    
    Args:
        transactions: 需要过滤的交易记录列表
        beanfiles: bean 文件路径列表，用于加载已存在的交易记录
    
    Returns:
        过滤后的交易记录列表
    """
    # 加载所有 bean 文件中的交易记录
    existing_entries = []
    for beanfile in beanfiles:
        entries, errors, options = load_file(beanfile)
        if errors:
            print(f"Warning: Errors loading {beanfile}: {errors}")
        existing_entries.extend(entries)
    
    # 按日期分组已存在的交易记录
    existing_txns_by_date = defaultdict(list)
    for entry in existing_entries:
        if isinstance(entry, Transaction):
            existing_txns_by_date[entry.date].append(entry)
    
    # 过滤交易记录
    filtered_txns = []
    for txn in transactions:
        # 获取同一天的已存在交易记录
        existing_txns = existing_txns_by_date[txn.date]
        
        # 检查是否有重复
        is_duplicate = False
        for existing_txn in existing_txns:
            # 检查每个 posting 是否匹配
            for posting in txn.postings:
                # 只检查 Assets 和 Liabilities 类型的账户
                if not (posting.account.startswith("Assets:") or posting.account.startswith("Liabilities:")):
                    continue
                
                # 在已存在的交易中查找匹配的 posting
                for existing_posting in existing_txn.postings:
                    if (existing_posting.account == posting.account and 
                        existing_posting.units.number == posting.units.number and
                        existing_posting.units.currency == posting.units.currency):
                        is_duplicate = True
                        break
                
                if is_duplicate:
                    break
            
            if is_duplicate:
                break
        
        if not is_duplicate:
            filtered_txns.append(txn)
    
    return filtered_txns
