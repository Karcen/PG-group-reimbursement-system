"""
Ollama AI 提示词模板
针对不同票据类型设计提取提示，强制输出 JSON 格式，禁止输出 Markdown。
"""

# ─── 主提取提示词 ──────────────────────────────────────────────────────────

INVOICE_EXTRACTION_PROMPT = """你是一名专业的财务票据信息提取专家。
请从以下 OCR 识别文本中提取发票/票据信息，并严格按照 JSON 格式输出。

OCR 文本：
{ocr_text}

请提取以下字段（无法识别的字段填 null）：
- document_type: 票据类型，只能是以下之一：
  vat_electronic（增值税电子发票）
  vat_paper（增值税纸质发票）
  railway_ticket（铁路电子客票）
  airline（航空电子行程单）
  hotel（酒店发票）
  taxi（出租车发票）
  parking（停车收据）
  toll（过路费收据）
  receipt（通用收据）
  unknown（无法识别）
- invoice_number: 发票号码（增值税发票专用）
- invoice_code: 发票代码（增值税发票专用）
- amount: 金额（数字，单位元，不含货币符号）
- tax: 税额（数字，单位元，仅增值税发票）
- date: 开票日期（格式 YYYY-MM-DD）
- seller: 销售方/开票方名称
- buyer: 购买方/报销人单位名称
- passenger: 乘客姓名（仅铁路客票/航空行程单）
- departure: 出发地（仅铁路客票/航空行程单）
- destination: 目的地（仅铁路客票/航空行程单）
- ticket_number: 票号（铁路客票/航空行程单专用）
- confidence: 识别置信度（0到1之间的小数，你对识别结果的把握程度）

要求：
1. 只输出 JSON，不要输出任何其他内容
2. 不要输出 Markdown 代码块（```）
3. 所有字符串值使用双引号
4. 数字类型字段不要加引号
5. 无法确定的字段填 null

示例输出：
{"document_type":"vat_electronic","invoice_number":"12345678","invoice_code":"3100192130","amount":1500.00,"tax":195.00,"date":"2024-03-15","seller":"上海某某科技有限公司","buyer":"复旦大学","passenger":null,"departure":null,"destination":null,"ticket_number":null,"confidence":0.92}
"""

# ─── 批量票据判断提示词（处理混合 PDF 时辅助分割） ────────────────────────────

DOCUMENT_TYPE_DETECTION_PROMPT = """请判断以下 OCR 文本属于什么类型的票据：
{ocr_text}

只输出一个单词（document_type），可能的值：
vat_electronic, vat_paper, railway_ticket, airline, hotel, taxi, parking, toll, receipt, unknown

只输出类型字符串，不要任何其他内容。
"""


def build_extraction_prompt(ocr_text: str) -> str:
    """构造发票信息提取提示词"""
    # 截断过长文本，避免超过 Ollama 上下文限制
    truncated = ocr_text[:3000] if len(ocr_text) > 3000 else ocr_text
    return INVOICE_EXTRACTION_PROMPT.format(ocr_text=truncated)


def build_type_detection_prompt(ocr_text: str) -> str:
    """构造票据类型判断提示词"""
    truncated = ocr_text[:1000] if len(ocr_text) > 1000 else ocr_text
    return DOCUMENT_TYPE_DETECTION_PROMPT.format(ocr_text=truncated)
