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

        Raises:
            anthropic.AuthenticationError: If the API key is invalid
            anthropic.RateLimitError:      If the rate limit is exceeded
            anthropic.APIError:            On other API failures
        """
        if context:
            self._context.update(context)

        self._history.append({"role": "user", "content": user_message})

        response = self.client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            system=self._build_system_prompt(),
            messages=self._history,
        )

        reply = response.content[0].text
        self._history.append({"role": "assistant", "content": reply})
        return reply

    def chat(self, history: list[dict]) -> str:
        """
        Stateless variant called by the assistant_panel.
        Accepts a pre-built history list and returns just the response text.
        Does not mutate self._history.

        Args:
            history: List of {"role": "user"|"assistant", "content": "..."} dicts

        Returns:
            The assistant's response as a plain string.
        """
        response = self.client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            system=self._build_system_prompt(),
            messages=history,
        )
        return response.content[0].text

    def clear_history(self) -> None:
        """Reset the conversation. Called when user clicks 'New Conversation'."""
        self._history.clear()

    def set_context(self, context: dict) -> None:
        """
        Update the session context injected into every system prompt.
        Called by the UI when the user navigates to a new panel or
        a new search completes.

        Args:
            context: Dict of context keys, e.g.:
                {
                    "current_panel":  "job_results",
                    "result_count":   42,
                    "location":       "Forney, TX",
                    "radius_miles":   50,
                    "top_job_titles": ["SOC Analyst", "Security Analyst"],
                }
        """
        self._context.update(context)

    def _build_system_prompt(self) -> str:
        """
        Build the system prompt with any current context injected.
        Returns the base SYSTEM_PROMPT if no context is set.
        """
        if not self._context:
            return SYSTEM_PROMPT

        context_lines = ["\n\n--- Current Session Context ---"]

        if "current_panel" in self._context:
            panel_labels = {
                "dashboard":  "Dashboard (home screen)",
                "jobs":       "Job Results (browsing search results)",
                "map":        "Map View (viewing jobs on a map)",
                "tracker":    "Application Tracker",
                "assistant":  "AI Assistant panel",
            }
            label = panel_labels.get(self._context["current_panel"],
                                     self._context["current_panel"])
            context_lines.append(f"The user is currently on: {label}")

        if "result_count" in self._context:
            context_lines.append(
                f"Current search has {self._context['result_count']} job listings loaded.")

        if "location" in self._context:
            context_lines.append(
                f"User's home location: {self._context['location']}")

        if "radius_miles" in self._context:
            context_lines.append(
                f"Search radius: {self._context['radius_miles']} miles")

        if "top_job_titles" in self._context:
            titles = ", ".join(self._context["top_job_titles"][:5])
            context_lines.append(f"Recent job titles in results: {titles}")

        if "keywords" in self._context:
            kw = ", ".join(self._context["keywords"]) if self._context["keywords"] else "none set"
            context_lines.append(f"User's keyword filters: {kw}")

        if "failed_providers" in self._context and self._context["failed_providers"]:
            failed = ", ".join(self._context["failed_providers"])
            context_lines.append(
                f"Note: These providers failed during the last search: {failed}")

        context_lines.append("--- End Context ---")
        return SYSTEM_PROMPT + "\n".join(context_lines)
