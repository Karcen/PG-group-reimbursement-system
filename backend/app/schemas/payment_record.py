"""
付款凭证相关 Pydantic Schema
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.payment_record import PaymentType, PAYMENT_TYPE_LABEL


class PaymentRecordOut(BaseModel):
    """付款凭证响应"""
    id: int
    uuid: str
    reimbursement_id: int
    original_filename: str
    file_size: int
    mime_type: str
    payment_type: PaymentType
    payment_type_label: str = ""   # 中文名称，由 model_validator 填充
    description: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}

    def model_post_init(self, __context) -> None:
        # 自动填充中文标签
        self.payment_type_label = PAYMENT_TYPE_LABEL.get(self.payment_type, self.payment_type)


class PaymentRecordCreate(BaseModel):
    """上传付款凭证时的附加信息（随 multipart form 提交）"""
    payment_type: PaymentType = Field(default=PaymentType.OTHER, description="付款方式")
    description: Optional[str] = Field(default=None, max_length=200, description="备注说明")
