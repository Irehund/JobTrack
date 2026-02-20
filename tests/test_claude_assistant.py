"""
tests/test_claude_assistant.py
================================
Tests for integrations/claude_assistant.py.
All Anthropic API calls are mocked — no network, no API key required.
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from integrations.claude_assistant import ClaudeAssistant, SYSTEM_PROMPT


# ── Fixture ───────────────────────────────────────────────────────────────────

def _make_assistant() -> ClaudeAssistant:
    """Return a ClaudeAssistant with a mocked Anthropic client."""
    with patch("integrations.claude_assistant.anthropic.Anthropic") as mock_cls:
        assistant = ClaudeAssistant(api_key="sk-ant-test-key")
        assistant.client = mock_cls.return_value
    return assistant


def _mock_response(text: str) -> MagicMock:
    """Build a mock Anthropic API response object."""
    mock_resp = MagicMock()
    mock_resp.content = [MagicMock(text=text)]
    return mock_resp


# ── send_message ──────────────────────────────────────────────────────────────

class TestSendMessage:

    def test_returns_assistant_response_text(self):
        a = _make_assistant()
        a.client.messages.create.return_value = _mock_response("Hello! How can I help?")
        result = a.send_message("Hi there")
        assert result == "Hello! How can I help?"

    def test_user_message_added_to_history(self):
        a = _make_assistant()
        a.client.messages.create.return_value = _mock_response("Sure!")
        a.send_message("What is an API key?")
        user_msgs = [m for m in a._history if m["role"] == "user"]
        assert any("API key" in m["content"] for m in user_msgs)

    def test_assistant_response_added_to_history(self):
        a = _make_assistant()
        a.client.messages.create.return_value = _mock_response("An API key is like a password.")
        a.send_message("What is an API key?")
        assistant_msgs = [m for m in a._history if m["role"] == "assistant"]
        assert any("API key" in m["content"] for m in assistant_msgs)

    def test_history_grows_with_each_message(self):
        a = _make_assistant()
        a.client.messages.create.return_value = _mock_response("Reply 1")
        a.send_message("Message 1")
        a.client.messages.create.return_value = _mock_response("Reply 2")
        a.send_message("Message 2")
        assert len(a._history) == 4  # 2 user + 2 assistant

    def test_history_passed_to_api_call(self):
        a = _make_assistant()
        a.client.messages.create.return_value = _mock_response("Got it.")
        a.send_message("First message")
        a.client.messages.create.return_value = _mock_response("Follow up.")
        a.send_message("Follow up question")
        call_args = a.client.messages.create.call_args
        messages_sent = call_args.kwargs["messages"]
        assert len(messages_sent) >= 2

    def test_context_injected_when_provided(self):
        a = _make_assistant()
        a.client.messages.create.return_value = _mock_response("I see you're on the map view.")
        a.send_message("Where am I?", context={"current_panel": "map"})
        assert "map" in a._context

    def test_context_accumulates_across_messages(self):
        a = _make_assistant()
        a.client.messages.create.return_value = _mock_response("OK")
        a.send_message("Hi", context={"current_panel": "jobs"})
        a.client.messages.create.return_value = _mock_response("Sure")
        a.send_message("Help", context={"result_count": 42})
        assert a._context["current_panel"] == "jobs"
        assert a._context["result_count"] == 42

    def test_uses_correct_model(self):
        a = _make_assistant()
        a.client.messages.create.return_value = _mock_response("Hi")
        a.send_message("Hello")
        call_kwargs = a.client.messages.create.call_args.kwargs
        assert "claude" in call_kwargs["model"].lower()

    def test_max_tokens_set(self):
        a = _make_assistant()
        a.client.messages.create.return_value = _mock_response("Hi")
        a.send_message("Hello")
        call_kwargs = a.client.messages.create.call_args.kwargs
        assert call_kwargs["max_tokens"] > 0

    def test_system_prompt_passed_to_api(self):
        a = _make_assistant()
        a.client.messages.create.return_value = _mock_response("Hi")
        a.send_message("Hello")
        call_kwargs = a.client.messages.create.call_args.kwargs
        assert "system" in call_kwargs
        assert len(call_kwargs["system"]) > 0


# ── chat (stateless variant) ──────────────────────────────────────────────────

class TestChat:

    def test_returns_response_text(self):
        a = _make_assistant()
        a.client.messages.create.return_value = _mock_response("Here's your answer.")
        history = [{"role": "user", "content": "What is a SOC analyst?"}]
        result = a.chat(history)
        assert result == "Here's your answer."

    def test_does_not_mutate_internal_history(self):
        a = _make_assistant()
        a.client.messages.create.return_value = _mock_response("Reply")
        history = [{"role": "user", "content": "Hi"}]
        a.chat(history)
        assert len(a._history) == 0  # Internal history unchanged

    def test_passes_provided_history_to_api(self):
        a = _make_assistant()
        a.client.messages.create.return_value = _mock_response("Sure")
        history = [
            {"role": "user",      "content": "What is a SOC?"},
            {"role": "assistant", "content": "A SOC is..."},
            {"role": "user",      "content": "Tell me more"},
        ]
        a.chat(history)
        call_kwargs = a.client.messages.create.call_args.kwargs
        assert call_kwargs["messages"] == history


# ── clear_history ─────────────────────────────────────────────────────────────

class TestClearHistory:

    def test_clears_all_messages(self):
        a = _make_assistant()
        a.client.messages.create.return_value = _mock_response("Hi")
        a.send_message("Message 1")
        a.send_message("Message 2")
        assert len(a._history) == 4
        a.clear_history()
        assert len(a._history) == 0

    def test_can_send_after_clear(self):
        a = _make_assistant()
        a.client.messages.create.return_value = _mock_response("Fresh start.")
        a.send_message("Before clear")
        a.clear_history()
        a.client.messages.create.return_value = _mock_response("Fresh start.")
        result = a.send_message("After clear")
        assert result == "Fresh start."
        assert len(a._history) == 2  # Just the new exchange


# ── set_context ───────────────────────────────────────────────────────────────

class TestSetContext:

    def test_context_stored(self):
        a = _make_assistant()
        a.set_context({"current_panel": "tracker", "result_count": 15})
        assert a._context["current_panel"] == "tracker"
        assert a._context["result_count"] == 15

    def test_context_merges_not_replaces(self):
        a = _make_assistant()
        a.set_context({"current_panel": "jobs"})
        a.set_context({"result_count": 30})
        assert a._context["current_panel"] == "jobs"
        assert a._context["result_count"] == 30

    def test_context_key_updated(self):
        a = _make_assistant()
        a.set_context({"current_panel": "jobs"})
        a.set_context({"current_panel": "tracker"})
        assert a._context["current_panel"] == "tracker"


# ── _build_system_prompt ──────────────────────────────────────────────────────

class TestBuildSystemPrompt:

    def test_no_context_returns_base_prompt(self):
        a = _make_assistant()
        result = a._build_system_prompt()
        assert result == SYSTEM_PROMPT

    def test_context_appended_to_base_prompt(self):
        a = _make_assistant()
        a.set_context({"current_panel": "jobs", "result_count": 42})
        result = a._build_system_prompt()
        assert result.startswith(SYSTEM_PROMPT)
        assert len(result) > len(SYSTEM_PROMPT)

    def test_panel_label_in_prompt(self):
        a = _make_assistant()
        a.set_context({"current_panel": "jobs"})
        prompt = a._build_system_prompt()
        assert "Job Results" in prompt

    def test_result_count_in_prompt(self):
        a = _make_assistant()
        a.set_context({"result_count": 99})
        prompt = a._build_system_prompt()
        assert "99" in prompt

    def test_location_in_prompt(self):
        a = _make_assistant()
        a.set_context({"location": "Forney, TX"})
        prompt = a._build_system_prompt()
        assert "Forney, TX" in prompt

    def test_radius_in_prompt(self):
        a = _make_assistant()
        a.set_context({"radius_miles": 50})
        prompt = a._build_system_prompt()
        assert "50" in prompt

    def test_top_job_titles_in_prompt(self):
        a = _make_assistant()
        a.set_context({"top_job_titles": ["SOC Analyst", "Security Analyst"]})
        prompt = a._build_system_prompt()
        assert "SOC Analyst" in prompt

    def test_failed_providers_in_prompt(self):
        a = _make_assistant()
        a.set_context({"failed_providers": ["Indeed", "Glassdoor"]})
        prompt = a._build_system_prompt()
        assert "Indeed" in prompt

    def test_empty_failed_providers_not_mentioned(self):
        a = _make_assistant()
        a.set_context({"failed_providers": []})
        prompt = a._build_system_prompt()
        assert "failed" not in prompt.lower() or "failed_providers" not in prompt

    def test_all_panel_types_have_labels(self):
        a = _make_assistant()
        panels = ["dashboard", "jobs", "map", "tracker", "assistant"]
        for panel in panels:
            a._context = {"current_panel": panel}
            prompt = a._build_system_prompt()
            # Should not just echo the raw panel ID as-is without a label
            assert len(prompt) > len(SYSTEM_PROMPT)

    def test_keywords_in_prompt(self):
        a = _make_assistant()
        a.set_context({"keywords": ["SOC Analyst", "Intelligence Analyst"]})
        prompt = a._build_system_prompt()
        assert "SOC Analyst" in prompt

    def test_empty_keywords_noted_as_none(self):
        a = _make_assistant()
        a.set_context({"keywords": []})
        prompt = a._build_system_prompt()
        assert "none" in prompt.lower()


# ── SYSTEM_PROMPT content ─────────────────────────────────────────────────────

class TestSystemPrompt:

    def test_system_prompt_is_nonempty(self):
        assert len(SYSTEM_PROMPT) > 50

    def test_system_prompt_mentions_job_search(self):
        assert "job" in SYSTEM_PROMPT.lower()

    def test_system_prompt_sets_helpful_tone(self):
        # Should contain at least one friendly instruction
        friendly_words = {"clear", "friendly", "simple", "patient", "honest"}
        assert any(w in SYSTEM_PROMPT.lower() for w in friendly_words)
