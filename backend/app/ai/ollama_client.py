"""
Ollama API 客户端
封装对本地 Ollama 服务的 HTTP 调用，提供同步和异步接口。
支持从应用配置读取 base_url 和默认模型，调用失败时抛出 AIException。
"""

import json
from typing import Optional

import httpx
from loguru import logger

from app.core.config import settings
from app.core.exceptions import AIException


class OllamaClient:
    """
    Ollama 本地 AI 客户端
    通过 Ollama HTTP API 调用本地 LLM（默认 Qwen3）。
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> None:
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL
        self.timeout = timeout or settings.OLLAMA_TIMEOUT

    async def generate(self, prompt: str) -> str:
        """
        调用 Ollama /api/generate 接口，返回模型的完整响应文本。

        :param prompt: 提示词
        :return: 模型响应文本
        :raises AIException: Ollama 服务不可用或返回错误时
        """
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,          # 不使用流式，等待完整响应
            "options": {
                "temperature": 0.1,   # 低温度，提高输出确定性（适合信息提取）
                "num_predict": 1024,  # 最大输出 token 数
            },
        }

        logger.debug(f"调用 Ollama [{self.model}]，提示词长度：{len(prompt)} 字符")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                result = data.get("response", "").strip()
                logger.debug(f"Ollama 响应长度：{len(result)} 字符")
                return result
        except httpx.ConnectError:
            raise AIException(
                f"无法连接到 Ollama 服务（{self.base_url}），请确认 Ollama 已启动"
            )
        except httpx.TimeoutException:
            raise AIException(f"Ollama 请求超时（{self.timeout}s），请检查服务状态或增大超时时间")
        except httpx.HTTPStatusError as e:
            raise AIException(f"Ollama 返回错误：{e.response.status_code} {e.response.text}")
        except Exception as e:
            raise AIException(f"调用 Ollama 时发生未知错误：{e}")

    async def extract_json(self, prompt: str) -> dict:
        """
        调用 Ollama 并将响应解析为 JSON 字典。
        自动清理模型可能输出的 Markdown 代码块标记。

        :raises AIException: Ollama 调用失败或响应不是合法 JSON
        """
        raw = await self.generate(prompt)

        # 清理 Markdown 代码块（如 ```json ... ``` 或 ``` ... ```）
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            # 去掉首行 ```json 或 ``` 和末行 ```
            inner_lines = []
            in_code = False
            for line in lines:
                if line.strip().startswith("```") and not in_code:
                    in_code = True
                    continue
                if line.strip() == "```" and in_code:
                    break
                if in_code:
                    inner_lines.append(line)
            cleaned = "\n".join(inner_lines).strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.warning(f"Ollama 响应无法解析为 JSON：{e}\n原始响应：{raw[:200]}")
            raise AIException(f"AI 响应格式错误，无法解析为 JSON。原始内容：{raw[:100]}...")

    async def check_health(self) -> bool:
        """检查 Ollama 服务是否可用"""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                return resp.status_code == 200
        except Exception:
            return False


# 模块级快捷访问
_default_client: Optional[OllamaClient] = None


def get_ollama_client() -> OllamaClient:
    """获取默认 Ollama 客户端实例（单例）"""
    global _default_client
    if _default_client is None:
        _default_client = OllamaClient()
    return _default_client
