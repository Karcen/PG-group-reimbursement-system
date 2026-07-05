"""
核心配置模块
使用 pydantic-settings 从环境变量 / .env 文件读取配置。
所有业务模块通过 `from app.core.config import settings` 获取配置实例。
"""

from functools import lru_cache
from pathlib import Path
from typing import Any, List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用全局配置"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ─── 应用基础 ──────────────────────────────────────────
    APP_ENV: str = "development"
    APP_NAME: str = "实验室报销管理系统"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    DEBUG: bool = False

    # ─── 安全 ──────────────────────────────────────────────
    SECRET_KEY: str = "dev-secret-key-change-in-production-minimum-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480   # 8 小时
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ─── 数据库 ────────────────────────────────────────────
    DATABASE_URL: str = "sqlite:///./database/reimbursement.db"

    # ─── 文件存储 ──────────────────────────────────────────
    STORAGE_ROOT: str = "./storage"
    MAX_UPLOAD_SIZE_MB: int = 50
    ALLOWED_MIME_TYPES: List[str] = ["application/pdf", "image/jpeg", "image/png", "image/tiff"]

    # ─── OCR ───────────────────────────────────────────────
    OCR_LANG: str = "ch"
    OCR_CONFIDENCE_THRESHOLD: float = 0.6

    # ─── AI（Ollama） ──────────────────────────────────────
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen3"
    OLLAMA_TIMEOUT: int = 120

    # ─── 业务规则 ──────────────────────────────────────────
    AMOUNT_DIFF_THRESHOLD: float = 1.0          # 金额差值容忍阈值（元）
    APPROVAL_REMINDER_INTERVAL_HOURS: int = 24  # 催办提醒间隔（小时）
    APPROVAL_TIMEOUT_HOURS: int = 72            # 超时阈值（小时）
    # 付款凭证金额门槛：报销金额超过此值时强制附上付款截图
    PAYMENT_RECORD_THRESHOLD: float = 200.0

    # ─── 日志 ──────────────────────────────────────────────
    LOG_DIR: str = "./logs"
    LOG_LEVEL: str = "INFO"

    # ─── CORS ──────────────────────────────────────────────
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:80"]

    # ─── 初始管理员 ────────────────────────────────────────
    INIT_ADMIN_USERNAME: str = "admin"
    INIT_ADMIN_PASSWORD: str = "Admin@123456"
    INIT_ADMIN_EMAIL: str = "admin@lab.edu.cn"

    # ─── List 字段解析 validator ──────────────────────────
    # pydantic-settings v2 从 .env 读 List 时需要 JSON 数组格式，
    # 此 validator 兼容逗号分隔字符串和 JSON 数组两种写法。

    @field_validator("CORS_ORIGINS", "ALLOWED_MIME_TYPES", mode="before")
    @classmethod
    def _parse_list_field(cls, v: Any) -> Any:
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("["):          # JSON 数组
                import json
                return json.loads(v)
            # 逗号分隔字符串
            return [item.strip() for item in v.split(",") if item.strip()]
        return v

    # ─── 派生属性（从配置计算得出） ────────────────────────
    @property
    def storage_original(self) -> Path:
        """原始 PDF 存储目录"""
        return Path(self.STORAGE_ROOT) / "original"

    @property
    def storage_ocr(self) -> Path:
        """OCR 结果 JSON 存储目录"""
        return Path(self.STORAGE_ROOT) / "ocr"

    @property
    def storage_preview(self) -> Path:
        """PDF 页面预览图存储目录"""
        return Path(self.STORAGE_ROOT) / "preview"

    @property
    def storage_thumbnails(self) -> Path:
        """缩略图存储目录"""
        return Path(self.STORAGE_ROOT) / "thumbnails"

    @property
    def storage_payment_records(self) -> Path:
        """付款凭证存储目录（银行/支付宝/微信转账截图）"""
        return Path(self.STORAGE_ROOT) / "payment_records"

    @property
    def max_upload_bytes(self) -> int:
        """上传文件最大字节数"""
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    @property
    def is_development(self) -> bool:
        return self.APP_ENV == "development"


@lru_cache()
def get_settings() -> Settings:
    """
    返回全局配置单例。
    使用 lru_cache 确保全生命周期只实例化一次，避免重复读取 .env 文件。
    """
    return Settings()


# 模块级别的快捷引用，方便 `from app.core.config import settings` 直接使用
settings: Settings = get_settings()
