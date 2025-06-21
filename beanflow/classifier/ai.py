import os
import json
from typing import List, Dict, Set, Optional

import openai

from beanflow.common.deal import Deal, DealType
from beanflow.common.utils import get_accounts_by_types
from beanflow.config import CONFIG


# Global client variable, initialized on first use
_client = None

def get_client():
    global _client
    if _client is None:
        api_key = CONFIG.get("llm_provider.api_key")
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY environment variable is not set")
        _client = openai.OpenAI(
            api_key=api_key,
            base_url=CONFIG.get("llm_provider.base_url")
        )
    return _client

def peek_next_line(fd) -> Optional[str]:
    """
    Peek at the next line in the file without advancing the file pointer.
    If the next line is not empty, rewind the file pointer to its original position.
    
    Args:
        fd: File descriptor to peek from
        
    Returns:
        The next line if it exists, None if EOF
    """
    pos = fd.tell()
    line = fd.readline()
    if line:  # if not EOF
        fd.seek(pos)  # rewind to original position
    return line.strip() if line else None

def extract_valid_categories() -> Dict[str, Set[str]]:
    """Extract all valid expense and income categories from beancount file."""
    categories = {
        "Expenses": set(get_accounts_by_types(["Expenses"])),
        "Income": set(get_accounts_by_types(["Income"])),
        "Liabilities": set(get_accounts_by_types(["Liabilities"]))
    }
    
    return categories

def prepare_classification_prompt(deals: List[Deal], valid_categories: Dict[str, Set[str]]) -> str:
    """Prepare the prompt for OpenAI API."""
    # Convert deals to a list of dictionaries for JSON serialization
    deals_info = []
    for index, deal in enumerate(deals):
        if deal.category is not None:
            continue
        if deal.type not in [DealType.EXPENSE, DealType.INCOME]:
            continue
        deal_info = {
            "交易序号": index,
            "交易类型": deal.type.value,
            "交易时间": deal.time.strftime("%Y-%m-%d %H:%M:%S"),
            "交易金额": float(deal.amount),
            "交易对方": deal.party,
            "交易描述": deal.description,
            "交易类型提示": deal.category_hint,
        }
        deals_info.append(deal_info)
    
    # Get classification prompts from config
    classify_prompts = CONFIG.get("classifier.classify_prompts", [])
    prompts_text = "\n".join(classify_prompts) if classify_prompts else "无特殊分类偏好"
    
    prompt = f"""
可用的账户类别：
支出类：{', '.join(sorted(valid_categories['Expenses']))}
收入类：{', '.join(sorted(valid_categories['Income']))}
负债类：{', '.join(sorted(valid_categories['Liabilities']))}

分类规则：
1. 只能使用上述提供的账户类别
2. 支出类交易必须使用以 'Expenses:' 或者 'Liabilities:' 开头的类别
3. 收入类交易必须使用以 'Income:' 开头的类别
5. 如果对分类不太确定，支出类使用 'Expenses:FIXME'，收入类使用 'Income:FIXME'
6. 请综合考虑以下信息：
   - 交易时间
   - 交易金额
   - 商户名称（支出方/收入方）
   - 交易描述
   - 交易类型提示（如果有）
7. 返回格式必须是 JSON 格式

我的一些分类习惯如下:
{prompts_text}

需要分类的交易记录：
{json.dumps(deals_info, indent=2, ensure_ascii=False)}

请对每笔交易进行分类，并以 JSON 格式返回结果，其中：
- key 为交易序号(字符串表示)
- value 为对应的账户类别
"""

    return prompt

def classify_by_ai(deals: List[Deal]) -> None:
    """
    Classify multiple deals using OpenAI API in a single request.
    Updates the category field of each deal with the AI's classification.
    
    Args:
        deals: List of Deal objects to classify
        bean_content: Content of the main.bean file
    """
    if not deals:
        return
        
    # Extract valid categories
    valid_categories = extract_valid_categories()
    
    # Prepare the prompt
    prompt = prepare_classification_prompt(deals, valid_categories)
    
    try:
        # Get client (will initialize if needed)
        client = get_client()
        
        # Call OpenAI API
        print("Querying AI classification, total deals: ", len(deals))
        response = client.chat.completions.create(
            model=CONFIG.get("llm_provider.model"),
            messages=[
                {"role": "system", "content": "你是一个专业的财务交易分类助手。你的任务是将以下交易记录分类到合适的账户类别中。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,  # Low temperature for more consistent results
            response_format={"type": "json_object"}
        )
        print("Querying AI classification, total deals: ", len(deals), " ... OK")
        
        # Parse the response
        classifications = json.loads(response.choices[0].message.content)
        
        # Update deal categories
        for idx in classifications:
            deal = deals[int(idx)]
            deal.category = classifications[idx]
                
    except Exception as e:
        # In case of any error, mark all deals as FIXME
        print(f"Error in AI classification: {str(e)}")
        for deal in deals:
            deal.category = f"{deal.type.value}:FIXME"
