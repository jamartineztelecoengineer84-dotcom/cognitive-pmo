"""
Tests para llm_provider.py — ARQ-04 F0
Ejecutar: cd /root/cognitive-pmo/backend && python -m pytest tests/test_llm_provider.py -v
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm_provider import (
    ToolCall, LLMResponse,
    anthropic_tools_to_openai, openai_tools_to_anthropic,
    anthropic_tool_result_to_openai, openai_tool_result_to_anthropic,
    translate_messages_to_openai,
    get_provider, list_providers,
    AnthropicProvider, OpenAIProvider, OllamaProvider,
)


# ============================================================
# Test ToolCall y LLMResponse
# ============================================================

class TestNormalizedClasses:
    def test_toolcall_creation(self):
        tc = ToolCall(id="tc_001", name="query_catalogo", input={"filtro": "SAP"})
        assert tc.id == "tc_001"
        assert tc.name == "query_catalogo"
        assert tc.input == {"filtro": "SAP"}

    def test_llmresponse_text(self):
        r = LLMResponse(text_parts=["Hola", "mundo"])
        assert r.text == "Hola\nmundo"
        assert not r.has_tool_calls

    def test_llmresponse_with_tools(self):
        tc = ToolCall(id="tc_001", name="test", input={})
        r = LLMResponse(text_parts=["Analizando..."], tool_calls=[tc])
        assert r.has_tool_calls
        assert r.tool_calls[0].name == "test"

    def test_llmresponse_empty(self):
        r = LLMResponse()
        assert r.text == ""
        assert not r.has_tool_calls
        assert r.stop_reason == "end_turn"


# ============================================================
# Test traducción de tool schemas
# ============================================================

class TestToolSchemaTranslation:
    """Verifica la traducción bidireccional de schemas de herramientas."""

    ANTHROPIC_TOOL = {
        "name": "query_catalogo",
        "description": "Consulta el catálogo de servicios IT",
        "input_schema": {
            "type": "object",
            "properties": {
                "filtro": {"type": "string", "description": "Término de búsqueda"},
                "categoria": {"type": "string", "enum": ["INFRA", "APP", "SEG"]}
            },
            "required": ["filtro"]
        }
    }

    OPENAI_TOOL = {
        "type": "function",
        "function": {
            "name": "query_catalogo",
            "description": "Consulta el catálogo de servicios IT",
            "parameters": {
                "type": "object",
                "properties": {
                    "filtro": {"type": "string", "description": "Término de búsqueda"},
                    "categoria": {"type": "string", "enum": ["INFRA", "APP", "SEG"]}
                },
                "required": ["filtro"]
            }
        }
    }

    def test_anthropic_to_openai(self):
        result = anthropic_tools_to_openai([self.ANTHROPIC_TOOL])
        assert len(result) == 1
        assert result[0]["type"] == "function"
        assert result[0]["function"]["name"] == "query_catalogo"
        assert result[0]["function"]["parameters"] == self.ANTHROPIC_TOOL["input_schema"]

    def test_openai_to_anthropic(self):
        result = openai_tools_to_anthropic([self.OPENAI_TOOL])
        assert len(result) == 1
        assert result[0]["name"] == "query_catalogo"
        assert result[0]["input_schema"] == self.OPENAI_TOOL["function"]["parameters"]

    def test_roundtrip(self):
        """Anthropic → OpenAI → Anthropic debe ser idéntico."""
        openai = anthropic_tools_to_openai([self.ANTHROPIC_TOOL])
        back = openai_tools_to_anthropic(openai)
        assert back[0]["name"] == self.ANTHROPIC_TOOL["name"]
        assert back[0]["input_schema"] == self.ANTHROPIC_TOOL["input_schema"]

    def test_empty_tools(self):
        assert anthropic_tools_to_openai([]) == []
        assert anthropic_tools_to_openai(None) == []
        assert openai_tools_to_anthropic([]) == []

    def test_multiple_tools(self):
        tools = [
            {"name": "tool_a", "description": "A", "input_schema": {"type": "object", "properties": {}}},
            {"name": "tool_b", "description": "B", "input_schema": {"type": "object", "properties": {"x": {"type": "string"}}}},
        ]
        result = anthropic_tools_to_openai(tools)
        assert len(result) == 2
        assert result[0]["function"]["name"] == "tool_a"
        assert result[1]["function"]["name"] == "tool_b"


# ============================================================
# Test traducción de tool results
# ============================================================

class TestToolResultTranslation:

    def test_anthropic_to_openai_tool_result(self):
        msg = {
            "role": "user",
            "content": [{
                "type": "tool_result",
                "tool_use_id": "tc_001",
                "content": '{"resultado": "OK"}'
            }]
        }
        result = anthropic_tool_result_to_openai(msg)
        assert isinstance(result, list)
        assert result[0]["role"] == "tool"
        assert result[0]["tool_call_id"] == "tc_001"

    def test_openai_to_anthropic_tool_result(self):
        msg = {"role": "tool", "tool_call_id": "tc_001", "content": "OK"}
        result = openai_tool_result_to_anthropic(msg)
        assert result["role"] == "user"
        assert result["content"][0]["type"] == "tool_result"
        assert result["content"][0]["tool_use_id"] == "tc_001"

    def test_normal_message_passthrough(self):
        msg = {"role": "user", "content": "Hola"}
        assert anthropic_tool_result_to_openai(msg) == msg
        assert openai_tool_result_to_anthropic(msg) == msg


# ============================================================
# Test traducción de historial completo
# ============================================================

class TestMessageTranslation:

    def test_simple_conversation(self):
        messages = [
            {"role": "user", "content": "Hola"},
            {"role": "assistant", "content": "Buenos días"},
        ]
        result = translate_messages_to_openai(messages)
        assert len(result) == 2
        assert result[0]["content"] == "Hola"
        assert result[1]["content"] == "Buenos días"

    def test_assistant_with_tool_use(self):
        messages = [{
            "role": "assistant",
            "content": [
                {"type": "text", "text": "Voy a consultar..."},
                {"type": "tool_use", "id": "tc_001", "name": "query_catalogo", "input": {"filtro": "SAP"}}
            ]
        }]
        result = translate_messages_to_openai(messages)
        assert result[0]["role"] == "assistant"
        assert result[0]["content"] == "Voy a consultar..."
        assert len(result[0]["tool_calls"]) == 1
        assert result[0]["tool_calls"][0]["function"]["name"] == "query_catalogo"


# ============================================================
# Test factory
# ============================================================

class TestFactory:
    def test_get_anthropic(self):
        provider = get_provider("anthropic", api_key="test-key")
        assert isinstance(provider, AnthropicProvider)

    def test_get_openai(self):
        provider = get_provider("openai", api_key="test-key")
        assert isinstance(provider, OpenAIProvider)

    def test_get_ollama(self):
        provider = get_provider("ollama")
        assert isinstance(provider, OllamaProvider)

    def test_invalid_provider(self):
        with pytest.raises(ValueError, match="no encontrado"):
            get_provider("grok")

    def test_list_providers(self):
        providers = list_providers()
        assert "anthropic" in providers
        assert "openai" in providers
        assert "ollama" in providers


# ============================================================
# Test AnthropicProvider format methods
# ============================================================

class TestAnthropicProviderFormats:
    def test_format_tool_result(self):
        p = AnthropicProvider(api_key="test")
        result = p.format_tool_result("tc_001", '{"ok": true}')
        assert result["type"] == "tool_result"
        assert result["tool_use_id"] == "tc_001"

    def test_format_assistant_tool_use(self):
        p = AnthropicProvider(api_key="test")
        resp = LLMResponse(
            text_parts=["Analizando..."],
            tool_calls=[ToolCall(id="tc_001", name="query_catalogo", input={"filtro": "SAP"})]
        )
        msg = p.format_assistant_tool_use(resp)
        assert msg["role"] == "assistant"
        assert len(msg["content"]) == 2  # text + tool_use
        assert msg["content"][0]["type"] == "text"
        assert msg["content"][1]["type"] == "tool_use"


# ============================================================
# Test OpenAIProvider format methods
# ============================================================

class TestOpenAIProviderFormats:
    def test_format_tool_result(self):
        p = OpenAIProvider(api_key="test")
        result = p.format_tool_result("tc_001", '{"ok": true}')
        assert result["role"] == "tool"
        assert result["tool_call_id"] == "tc_001"

    def test_format_assistant_tool_use(self):
        p = OpenAIProvider(api_key="test")
        resp = LLMResponse(
            text_parts=["Analizando..."],
            tool_calls=[ToolCall(id="tc_001", name="query_catalogo", input={"filtro": "SAP"})]
        )
        msg = p.format_assistant_tool_use(resp)
        assert msg["role"] == "assistant"
        assert msg["tool_calls"][0]["function"]["name"] == "query_catalogo"
        assert msg["tool_calls"][0]["function"]["arguments"] == '{"filtro": "SAP"}'

    def test_model_mapping(self):
        p = OpenAIProvider(api_key="test")
        assert p._map_model("claude-sonnet-4-20250514") == "gpt-4.1"
        assert p._map_model("claude-haiku-4-5-20251001") == "gpt-4o-mini"
        assert p._map_model("custom-model") == "custom-model"


# ============================================================
# Test OllamaProvider format methods
# ============================================================

class TestOllamaProviderFormats:
    def test_model_mapping(self):
        p = OllamaProvider()
        assert p._map_model("claude-sonnet-4-20250514") == "llama3:8b"
        assert p._map_model("claude-haiku-4-5-20251001") == "gemma3:1b"

    def test_format_tool_result(self):
        p = OllamaProvider()
        result = p.format_tool_result("tc_001", "ok")
        assert result["role"] == "tool"  # mismo formato que OpenAI


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
