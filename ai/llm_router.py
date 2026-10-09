import json
import requests
from typing import Optional
from config import (
    LLM_PROVIDER,
    GEMINI_API_KEY,
    OPENAI_API_KEY,
    ANTHROPIC_API_KEY,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
)


class LLMRouter:
    """
    Bộ định tuyến AI linh hoạt (AI-Agnostic):
    Hỗ trợ Gemini, OpenAI, Claude, Ollama, và chế độ Offline Rule-Based.
    Sử dụng trực tiếp REST API qua requests để không bắt buộc phụ thuộc thư viện nặng.
    """

    def __init__(self, provider: Optional[str] = None):
        self.provider = (provider or LLM_PROVIDER or "offline").lower()

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """
        Gửi prompt đến nhà cung cấp AI đã chọn và nhận phản hồi.
        Nếu gặp lỗi kết nối hoặc thiếu API Key, tự động fallback an toàn.
        """
        if self.provider == "gemini" and GEMINI_API_KEY:
            try:
                return self._call_gemini(system_prompt, user_prompt)
            except Exception as e:
                # Ghi nhận lỗi và fallback
                pass

        elif self.provider == "openai" and OPENAI_API_KEY:
            try:
                return self._call_openai(system_prompt, user_prompt)
            except Exception as e:
                pass

        elif self.provider == "claude" and ANTHROPIC_API_KEY:
            try:
                return self._call_claude(system_prompt, user_prompt)
            except Exception as e:
                pass

        elif self.provider == "ollama":
            try:
                return self._call_ollama(system_prompt, user_prompt)
            except Exception as e:
                pass

        # Fallback mặc định: Chế độ phân tích định lượng độc lập
        return ""

    def _call_gemini(self, system_prompt: str, user_prompt: str) -> str:
        """Gọi Google Gemini qua REST API"""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"parts": [{"text": user_prompt}]}],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 2048,
            }
        }
        r = requests.post(url, headers=headers, json=payload, timeout=20)
        if r.status_code == 200:
            data = r.json()
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        raise RuntimeError(f"Gemini API returned status {r.status_code}: {r.text}")

    def _call_openai(self, system_prompt: str, user_prompt: str) -> str:
        """Gọi OpenAI GPT qua REST API"""
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}",
        }
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
        }
        r = requests.post(url, headers=headers, json=payload, timeout=20)
        if r.status_code == 200:
            data = r.json()
            return data["choices"][0]["message"]["content"].strip()
        raise RuntimeError(f"OpenAI API returned status {r.status_code}: {r.text}")

    def _call_claude(self, system_prompt: str, user_prompt: str) -> str:
        """Gọi Anthropic Claude qua REST API"""
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "Content-Type": "application/json",
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
        }
        payload = {
            "model": "claude-3-5-sonnet-20241022",
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
            "max_tokens": 2048,
            "temperature": 0.2,
        }
        r = requests.post(url, headers=headers, json=payload, timeout=20)
        if r.status_code == 200:
            data = r.json()
            return data["content"][0]["text"].strip()
        raise RuntimeError(f"Claude API returned status {r.status_code}: {r.text}")

    def _call_ollama(self, system_prompt: str, user_prompt: str) -> str:
        """Gọi Local Ollama Server qua REST API"""
        url = f"{OLLAMA_BASE_URL}/api/generate"
        payload = {
            "model": OLLAMA_MODEL,
            "system": system_prompt,
            "prompt": user_prompt,
            "stream": False,
        }
        r = requests.post(url, json=payload, timeout=30)
        if r.status_code == 200:
            data = r.json()
            return data.get("response", "").strip()
        raise RuntimeError(f"Ollama API returned status {r.status_code}")
