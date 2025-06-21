# rule based classifier

from beanflow.common.deal import DealType

PAYEE_TO_EXPENSE_CATEGORY = {
    "杭州闲鱼信息技术有限公司": "Expenses:Fee:Xianyu",
    "国网北京市电力公司": "Expenses:Housing:Electric",
}

SOURCE_TO_INCOME_CATEGORY = {
}

def classify_by_rules(deals):
    for deal in deals:
        if deal.type == DealType.EXPENSE:
            if deal.payee in PAYEE_TO_EXPENSE_CATEGORY:
                deal.category = PAYEE_TO_EXPENSE_CATEGORY[deal.payee]
        elif deal.type == DealType.INCOME:
            if deal.source in SOURCE_TO_INCOME_CATEGORY:
                deal.category = SOURCE_TO_INCOME_CATEGORY[deal.source]

def filter_expense_deals_by_payee(deals, payee):
    return [deal for deal in deals if deal.type == DealType.EXPENSE and deal.payee == payee]

def classify_refund_by_match_expense(deals):
    for deal in deals:
        if deal.type != DealType.REFUND:
            continue
        expense_deals = filter_expense_deals_by_payee(deals, deal.payee)
        if len(expense_deals) == 0:
            continue
        # check order_id equal
        if deal.meta.get("order_id") is not None:
            for expense_deal in expense_deals:
                if expense_deal.meta.get("order_id") == deal.meta.get("order_id"):
                    deal.category = expense_deal.category
            continue

        # check description similarity
        descirption_similarity_found = False
        for expense_deal in expense_deals:
            if expense_deal.description in deal.description:
                deal.category = expense_deal.category
                descirption_similarity_found = True
                break
        if descirption_similarity_found:
            continue

        # check amount similarity
        expense_deals.sort(key=lambda x: abs(float(x.amount) - float(deal.amount)))
                    
        # sort expense deals by amount diff, if amount diff > 0.1, sort by time diff
        expense_deals.sort(key=lambda x: abs(float(x.amount) - float(deal.amount)))
        if abs(float(expense_deals[0].amount) - float(deal.amount)) < 0.1:
            deal.category = expense_deals[0].category
        else:
            expense_deals.sort(key=lambda x:  (x.time - deal.time).total_seconds())
            deal.category = expense_deals[0].category