"""
ARQ-04 — Multi-LLM Provider Abstraction Layer
Cognitive PMO v6.0

Abstrae las llamadas a LLM para soportar múltiples providers:
- AnthropicProvider: SDK anthropic (actual, producción)
- OpenAIProvider: API OpenAI via OAuth/API key
- OllamaProvider: HTTP local contra localhost:11434

Cada provider traduce internamente:
- Tool schemas: Anthropic (input_schema) ↔ OpenAI (parameters + function wrapper)
- Respuestas: formato propietario → LLMResponse normalizado
- Tool results: formato propietario → mensajes del provider

engine.py, tech_copiloto.py y main.py usan SOLO las clases normalizadas.
"""

import json
import os
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import anthropic
import httpx

logger = logging.getLogger(__name__)


# ============================================================
# Clases normalizadas (las que usa todo el backend)
# ============================================================

@dataclass
class ToolCall:
    """Llamada a herramienta normalizada, independiente del provider."""
    id: str
    name: str
    input: dict  # siempre dict, nunca string JSON


@dataclass
class LLMResponse:
    """Respuesta normalizada de cualquier LLM provider."""
    text_parts: List[str] = field(default_factory=list)
    tool_calls: List[ToolCall] = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0
    stop_reason: str = "end_turn"  # "end_turn" | "tool_use" | "max_tokens"
    raw_response: Any = None  # respuesta original para debug

    @property
    def text(self) -> str:
        """Texto completo concatenado (convenience)."""
        return "\n".join(self.text_parts) if self.text_parts else ""

    @property
    def has_tool_calls(self) -> bool:
        return len(self.tool_calls) > 0


# ============================================================
# Funciones de traducción de tool schemas
# ============================================================

def anthropic_tools_to_openai(tools: List[dict]) -> List[dict]:
    """
    Traduce tool schemas de formato Anthropic a formato OpenAI.

    Anthropic:
      {"name": "x", "description": "y", "input_schema": {"type":"object",...}}

    OpenAI:
      {"type": "function", "function": {"name": "x", "description": "y", "parameters": {"type":"object",...}}}
    """
    if not tools:
        return []
    result = []
    for t in tools:
        result.append({
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t.get("description", ""),
                "parameters": t.get("input_schema", {"type": "object", "properties": {}})
            }
        })
    return result


def openai_tools_to_anthropic(tools: List[dict]) -> List[dict]:
    """
    Traduce tool schemas de formato OpenAI a formato Anthropic (inversa).
    Útil si algún día recibimos schemas en formato OpenAI.
    """
    if not tools:
        return []
    result = []
    for t in tools:
        func = t.get("function", t)
        result.append({
            "name": func["name"],
            "description": func.get("description", ""),
            "input_schema": func.get("parameters", {"type": "object", "properties": {}})
        })
    return result


# ============================================================
# Traducción de mensajes con tool_results
# ============================================================

def anthropic_tool_result_to_openai(msg: dict) -> dict:
    """
    Anthropic: {"role":"user","content":[{"type":"tool_result","tool_use_id":"xxx","content":"..."}]}
    OpenAI:    {"role":"tool","tool_call_id":"xxx","content":"..."}
    """
    if msg.get("role") == "user" and isinstance(msg.get("content"), list):
        results = []
        for block in msg["content"]:
            if isinstance(block, dict) and block.get("type") == "tool_result":
                results.append({
                    "role": "tool",
                    "tool_call_id": block["tool_use_id"],
                    "content": block.get("content", "")
                })
        if results:
            return results  # puede ser múltiples tool results
    return msg


def openai_tool_result_to_anthropic(msg: dict) -> dict:
    """
    OpenAI:    {"role":"tool","tool_call_id":"xxx","content":"..."}
    Anthropic: {"role":"user","content":[{"type":"tool_result","tool_use_id":"xxx","content":"..."}]}
    """
    if msg.get("role") == "tool":
        return {
            "role": "user",
            "content": [{
                "type": "tool_result",
                "tool_use_id": msg["tool_call_id"],
                "content": msg.get("content", "")
            }]
        }
    return msg


# ============================================================
# Traducción de mensajes completos (historial de conversación)
# ============================================================

def translate_messages_to_openai(messages: List[dict]) -> List[dict]:
    """
    Traduce un historial de mensajes de formato Anthropic a formato OpenAI.
    Maneja:
    - Mensajes normales (role: user/assistant) → pasan tal cual
    - Mensajes assistant con tool_use blocks → añade tool_calls
    - Mensajes user con tool_result blocks → convierte a role: tool
    """
    result = []
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")

        # Mensaje assistant con tool_use blocks (Anthropic format)
        if role == "assistant" and isinstance(content, list):
            text_parts = []
            tool_calls = []
            for block in content:
                if isinstance(block, dict):
                    if block.get("type") == "text":
                        text_parts.append(block.get("text", ""))
                    elif block.get("type") == "tool_use":
                        tool_calls.append({
                            "id": block["id"],
                            "type": "function",
                            "function": {
                                "name": block["name"],
                                "arguments": json.dumps(block.get("input", {}))
                            }
                        })
            openai_msg = {
                "role": "assistant",
                "content": "\n".join(text_parts) if text_parts else None,
            }
            if tool_calls:
                openai_msg["tool_calls"] = tool_calls
            result.append(openai_msg)

        # Mensaje user con tool_result blocks
        elif role == "user" and isinstance(content, list):
            converted = anthropic_tool_result_to_openai(msg)
            if isinstance(converted, list):
                result.extend(converted)
            else:
                result.append(converted)

        # Mensajes normales (string content)
        else:
            result.append({"role": role, "content": content if isinstance(content, str) else str(content)})

    return result


# ============================================================
# Provider base (ABC)
# ============================================================

class LLMProvider(ABC):
    """Clase base abstracta para providers LLM."""

    @abstractmethod
    async def create_message(
        self,
        model: str,
        system: str,
        messages: list,
        tools: Optional[list] = None,
        max_tokens: int = 2048,
        temperature: float = 0.3
    ) -> LLMResponse:
        """
        Envía un mensaje al LLM y devuelve respuesta normalizada.

        Args:
            model: nombre del modelo (se traduce internamente si es necesario)
            system: system prompt
            messages: historial en formato Anthropic (el backend siempre trabaja así)
            tools: lista de tool schemas en formato Anthropic (input_schema)
            max_tokens: máximo de tokens de respuesta
            temperature: temperatura de generación

        Returns:
            LLMResponse normalizada
        """
        ...

    @abstractmethod
    def format_tool_result(self, tool_call_id: str, result: str) -> dict:
        """
        Formatea el resultado de una herramienta para enviarlo de vuelta al LLM.
        Cada provider tiene su formato propio.

        Returns:
            dict en el formato que espera el provider
        """
        ...

    @abstractmethod
    def format_assistant_tool_use(self, response: LLMResponse) -> dict:
        """
        Formatea el mensaje del assistant que contiene tool_use para el historial.
        Necesario para el bucle de tool_use en engine.py.

        Returns:
            dict con role=assistant y el contenido de tool_use en formato del provider
        """
        ...


# ============================================================
# AnthropicProvider — wrapper del SDK actual
# ============================================================

class AnthropicProvider(LLMProvider):
    """
    Provider para Claude API via SDK anthropic.
    Es el provider actual de producción — todo engine.py funciona con él.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.client = anthropic.AsyncAnthropic(
            api_key=api_key or os.environ.get("ANTHROPIC_API_KEY")
        )

    async def create_message(
        self,
        model: str,
        system: str,
        messages: list,
        tools: Optional[list] = None,
        max_tokens: int = 2048,
        temperature: float = 0.3
    ) -> LLMResponse:
        kwargs = {
            "model": model,
            "system": system,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if tools:
            kwargs["tools"] = tools  # ya están en formato Anthropic

        resp = await self.client.messages.create(**kwargs)

        # Normalizar respuesta
        text_parts = []
        tool_calls = []
        for block in resp.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                tool_calls.append(ToolCall(
                    id=block.id,
                    name=block.name,
                    input=block.input  # ya es dict
                ))

        return LLMResponse(
            text_parts=text_parts,
            tool_calls=tool_calls,
            input_tokens=resp.usage.input_tokens,
            output_tokens=resp.usage.output_tokens,
            stop_reason=resp.stop_reason,  # "end_turn" | "tool_use" | "max_tokens"
            raw_response=resp
        )

    def format_tool_result(self, tool_call_id: str, result: str) -> dict:
        """Formato Anthropic: va dentro de content[] de un mensaje user."""
        return {
            "type": "tool_result",
            "tool_use_id": tool_call_id,
            "content": result
        }

    def format_assistant_tool_use(self, response: LLMResponse) -> dict:
        """Reconstruye el mensaje assistant con bloques text + tool_use para Anthropic."""
        content = []
        for text in response.text_parts:
            if text:
                content.append({"type": "text", "text": text})
        for tc in response.tool_calls:
            content.append({
                "type": "tool_use",
                "id": tc.id,
                "name": tc.name,
                "input": tc.input
            })
        return {"role": "assistant", "content": content}


# ============================================================
# OpenAIProvider — API OpenAI via OAuth o API key
# ============================================================

class OpenAIProvider(LLMProvider):
    """
    Provider para OpenAI API.
    Soporta autenticación via:
    - API key directa (OPENAI_API_KEY)
    - OAuth token (desde OpenClaw, ChatGPT Plus)

    Traduce tool schemas de Anthropic → OpenAI automáticamente.
    """

    # Mapeo de modelos Anthropic → OpenAI equivalente
    MODEL_MAP = {
        "claude-sonnet-4-20250514": "gpt-4.1",
        "claude-haiku-4-5-20251001": "gpt-4o-mini",
    }

    def __init__(self, api_key: Optional[str] = None, oauth_token: Optional[str] = None,
                 base_url: str = "https://api.openai.com/v1"):
        self.base_url = base_url
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.oauth_token = oauth_token  # JWT de OpenClaw OAuth

    def _get_headers(self) -> dict:
        """Construye headers de autenticación."""
        token = self.oauth_token or self.api_key
        if not token:
            raise ValueError("OpenAIProvider: ni api_key ni oauth_token configurados")
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    def _map_model(self, model: str) -> str:
        """Traduce nombre de modelo Anthropic a OpenAI."""
        return self.MODEL_MAP.get(model, model)

    async def create_message(
        self,
        model: str,
        system: str,
        messages: list,
        tools: Optional[list] = None,
        max_tokens: int = 2048,
        temperature: float = 0.3
    ) -> LLMResponse:
        # Traducir modelo
        openai_model = self._map_model(model)

        # Traducir mensajes (Anthropic → OpenAI)
        openai_messages = [{"role": "system", "content": system}]
        openai_messages.extend(translate_messages_to_openai(messages))

        # Traducir tool schemas
        openai_tools = anthropic_tools_to_openai(tools) if tools else None

        # Construir payload
        payload = {
            "model": openai_model,
            "messages": openai_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if openai_tools:
            payload["tools"] = openai_tools

        # Llamar a OpenAI API
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers=self._get_headers(),
                json=payload
            )
            resp.raise_for_status()
            data = resp.json()

        # Normalizar respuesta
        choice = data["choices"][0]
        message = choice["message"]

        text_parts = [message.get("content", "")] if message.get("content") else []

        tool_calls = []
        for tc in message.get("tool_calls", []):
            args = tc["function"]["arguments"]
            tool_calls.append(ToolCall(
                id=tc["id"],
                name=tc["function"]["name"],
                input=json.loads(args) if isinstance(args, str) else args
            ))

        usage = data.get("usage", {})

        # Mapear stop_reason de OpenAI a normalizado
        finish_reason = choice.get("finish_reason", "stop")
        stop_reason_map = {
            "stop": "end_turn",
            "tool_calls": "tool_use",
            "length": "max_tokens",
        }

        return LLMResponse(
            text_parts=text_parts,
            tool_calls=tool_calls,
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
            stop_reason=stop_reason_map.get(finish_reason, finish_reason),
            raw_response=data
        )

    def format_tool_result(self, tool_call_id: str, result: str) -> dict:
        """Formato OpenAI: mensaje independiente con role=tool."""
        return {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": result
        }

    def format_assistant_tool_use(self, response: LLMResponse) -> dict:
        """Reconstruye el mensaje assistant con tool_calls para OpenAI."""
        msg = {
            "role": "assistant",
            "content": response.text if response.text_parts else None,
        }
        if response.tool_calls:
            msg["tool_calls"] = [{
                "id": tc.id,
                "type": "function",
                "function": {
                    "name": tc.name,
                    "arguments": json.dumps(tc.input)
                }
            } for tc in response.tool_calls]
        return msg


# ============================================================
# OllamaProvider — HTTP local, zero data exposure
# ============================================================

class OllamaProvider(LLMProvider):
    """
    Provider para Ollama local.
    API compatible con OpenAI en /v1/chat/completions.

    Modelos disponibles en VPS:
    - gemma3:1b (815MB) → sin tool_use, solo chat
    - llama3:8b (si se descarga) → con tool_use

    Zero data exposure: los datos nunca salen del servidor.
    """

    MODEL_MAP = {
        "claude-sonnet-4-20250514": "llama3:8b",
        "claude-haiku-4-5-20251001": "gemma3:1b",
    }

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url

    def _map_model(self, model: str) -> str:
        return self.MODEL_MAP.get(model, model)

    async def create_message(
        self,
        model: str,
        system: str,
        messages: list,
        tools: Optional[list] = None,
        max_tokens: int = 2048,
        temperature: float = 0.3
    ) -> LLMResponse:
        ollama_model = self._map_model(model)

        # Ollama usa formato OpenAI en /v1/chat/completions
        ollama_messages = [{"role": "system", "content": system}]
        ollama_messages.extend(translate_messages_to_openai(messages))

        payload = {
            "model": ollama_model,
            "messages": ollama_messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }

        # Tool_use solo si el modelo lo soporta y hay tools
        openai_tools = anthropic_tools_to_openai(tools) if tools else None
        if openai_tools:
            payload["tools"] = openai_tools

        async with httpx.AsyncClient(timeout=300.0) as client:
            resp = await client.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload
            )
            resp.raise_for_status()
            data = resp.json()

        # Normalizar (mismo formato que OpenAI)
        choice = data["choices"][0]
        message = choice["message"]

        text_parts = [message.get("content", "")] if message.get("content") else []

        tool_calls = []
        for tc in message.get("tool_calls", []):
            args = tc["function"]["arguments"]
            tool_calls.append(ToolCall(
                id=tc.get("id", f"ollama-{tc['function']['name']}"),
                name=tc["function"]["name"],
                input=json.loads(args) if isinstance(args, str) else args
            ))

        usage = data.get("usage", {})
        finish_reason = choice.get("finish_reason", "stop")
        stop_reason_map = {
            "stop": "end_turn",
            "tool_calls": "tool_use",
            "length": "max_tokens",
        }

        return LLMResponse(
            text_parts=text_parts,
            tool_calls=tool_calls,
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
            stop_reason=stop_reason_map.get(finish_reason, finish_reason),
            raw_response=data
        )

    def format_tool_result(self, tool_call_id: str, result: str) -> dict:
        """Mismo formato que OpenAI."""
        return {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": result
        }

    def format_assistant_tool_use(self, response: LLMResponse) -> dict:
        """Mismo formato que OpenAI."""
        msg = {
            "role": "assistant",
            "content": response.text if response.text_parts else None,
        }
        if response.tool_calls:
            msg["tool_calls"] = [{
                "id": tc.id,
                "type": "function",
                "function": {
                    "name": tc.name,
                    "arguments": json.dumps(tc.input)
                }
            } for tc in response.tool_calls]
        return msg


# ============================================================
# Factory — obtener provider por nombre
# ============================================================

# Registry de providers disponibles
_PROVIDER_REGISTRY = {
    "anthropic": AnthropicProvider,
    "openai": OpenAIProvider,
    "ollama": OllamaProvider,
}


def get_provider(name: str = "anthropic", **kwargs) -> LLMProvider:
    """
    Factory para obtener una instancia de LLMProvider.

    Args:
        name: "anthropic", "openai", "ollama"
        **kwargs: argumentos específicos del provider (api_key, oauth_token, base_url, etc.)

    Returns:
        Instancia del provider solicitado

    Raises:
        ValueError si el provider no existe
    """
    provider_class = _PROVIDER_REGISTRY.get(name)
    if not provider_class:
        available = ", ".join(_PROVIDER_REGISTRY.keys())
        raise ValueError(f"Provider '{name}' no encontrado. Disponibles: {available}")

    return provider_class(**kwargs)


def list_providers() -> List[str]:
    """Lista los providers registrados."""
    return list(_PROVIDER_REGISTRY.keys())


# ============================================================
# Utilidad: detectar qué providers están disponibles
# ============================================================

async def check_provider_availability() -> Dict[str, dict]:
    """
    Comprueba qué providers están configurados y accesibles.
    Útil para el frontend (selector de provider).

    Returns:
        Dict con estado de cada provider:
        {"anthropic": {"available": True, "reason": "API key configured"},
         "openai": {"available": False, "reason": "No API key or OAuth token"},
         "ollama": {"available": True, "reason": "Running on localhost:11434", "models": [...]}}
    """
    status = {}

    # Anthropic
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    status["anthropic"] = {
        "available": bool(api_key),
        "reason": "API key configured" if api_key else "ANTHROPIC_API_KEY not set",
        "auth_type": "api_key"
    }

    # OpenAI
    openai_key = os.environ.get("OPENAI_API_KEY", "")
    status["openai"] = {
        "available": bool(openai_key),
        "reason": "API key configured" if openai_key else "No API key or OAuth token",
        "auth_type": "api_key" if openai_key else "none"
    }

    # Ollama
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get("http://localhost:11434/api/tags")
            if resp.status_code == 200:
                models = [m["name"] for m in resp.json().get("models", [])]
                status["ollama"] = {
                    "available": True,
                    "reason": f"Running on localhost:11434 ({len(models)} models)",
                    "auth_type": "none",
                    "models": models
                }
            else:
                status["ollama"] = {"available": False, "reason": f"HTTP {resp.status_code}"}
    except Exception as e:
        status["ollama"] = {"available": False, "reason": f"Not reachable: {str(e)}"}

    return status
