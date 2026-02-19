"""
integrations/claude_assistant.py
==================================
Wraps the Anthropic Claude API for the in-app AI assistant.

The assistant is context-aware — it knows the user is job searching,
what their preferences are, and what stage of the app they're in.
It answers plain-English questions like:
    "What's an API key and where do I get one for Indeed?"
    "What does 'hybrid' mean for a job listing?"
    "Help me write a cover letter for this job."
    "Why am I not seeing any results?"

Conversation history is maintained per session so follow-up questions work.
"""

from typing import Optional
import anthropic

SYSTEM_PROMPT = """You are JobTrack's built-in assistant. You help job seekers — 
especially those who are less familiar with technology — use the JobTrack application 
and navigate their job search.

Keep your answers clear, friendly, and jargon-free. When explaining technical concepts 
(like API keys), use simple analogies. When users seem frustrated, be patient and 
reassuring.

You have access to context about the user's current session when it's provided to you.
Never make up job listings or company information. If you're unsure, say so honestly."""


class ClaudeAssistant:
    """Manages the Claude AI assistant chat session."""

    def __init__(self, api_key: str):
        """
        Args:
            api_key: Anthropic API key from keyring_manager.get_key("anthropic")
        """
        self.client = anthropic.Anthropic(api_key=api_key)
        self._history: list[dict] = []  # Conversation history for this session
        self._context: dict = {}        # Current app context (page, recent results, etc.)

    def send_message(
        self,
        user_message: str,
        context: Optional[dict] = None,
    ) -> str:
        """
        Send a message and return the assistant's reply.
        Conversation history is maintained automatically.

        Args:
            user_message: The user's typed message
            context:      Optional dict with current app state to inject
                          (e.g., {"page": "map_view", "result_count": 42})

        Returns:
            The assistant's response as a plain string.
        """
        # TODO: Implement message sending
        # 1. If context provided, update self._context
        # 2. Build system prompt with context injected
        # 3. Append user_message to self._history
        # 4. Call self.client.messages.create() with full history
        # 5. Append assistant response to self._history
        # 6. Return response text
        raise NotImplementedError

    def clear_history(self) -> None:
        """Reset the conversation. Called when user clicks 'New Conversation'."""
        self._history.clear()

    def _build_system_prompt(self) -> str:
        """
        Build the system prompt with any current context injected.
        Returns the base SYSTEM_PROMPT if no context is set.
        """
        # TODO: Append context details to SYSTEM_PROMPT if self._context is not empty
        raise NotImplementedError
