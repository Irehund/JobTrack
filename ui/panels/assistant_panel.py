"""
ui/panels/assistant_panel.py
==============================
AI assistant panel — chat interface backed by the Anthropic API.
Includes job context so Claude can answer questions about current results.
"""

import threading
import customtkinter as ctk
from core import keyring_manager


class AssistantPanel(ctk.CTkFrame):
    """Chat interface for the built-in Claude AI assistant."""

    SYSTEM_PROMPT = (
        "You are JobTrack's built-in job search assistant. "
        "You help the user find relevant jobs, understand job descriptions, "
        "prepare for interviews, and make sense of their search results. "
        "Be concise, practical, and encouraging. "
        "The user is actively job hunting and needs actionable advice."
    )

    def __init__(self, parent, config: dict, main_window, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.config = config
        self.main_window = main_window
        self._history: list[dict] = []
        self._build()

    def _build(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_columnconfigure(0, weight=1)

        # ── Chat history ──────────────────────────────────────────────────────
        self._chat_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._chat_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=(20, 0))
        self._chat_frame.grid_columnconfigure(0, weight=1)

        # Welcome message
        self._add_message(
            "assistant",
            "Hi! I'm your JobTrack assistant. I can help you:\n\n"
            "• Understand job descriptions and required qualifications\n"
            "• Tailor your resume and cover letter to specific postings\n"
            "• Prepare for interviews with common questions\n"
            "• Explain cybersecurity certifications and career paths\n\n"
            "What would you like to know?",
        )

        # ── Input area ────────────────────────────────────────────────────────
        input_frame = ctk.CTkFrame(self, fg_color=("gray90", "gray20"), corner_radius=0)
        input_frame.grid(row=1, column=0, sticky="ew", padx=0, pady=0)
        input_frame.grid_columnconfigure(0, weight=1)

        self._input = ctk.CTkTextbox(input_frame, height=72, wrap="word",
                                     font=ctk.CTkFont(size=13))
        self._input.grid(row=0, column=0, sticky="ew", padx=(16, 8), pady=12)
        self._input.bind("<Return>", self._on_enter)
        self._input.bind("<Shift-Return>", lambda e: None)  # Allow newlines

        self._send_btn = ctk.CTkButton(
            input_frame, text="Send", width=80, height=72,
            command=self._send, corner_radius=0,
        )
        self._send_btn.grid(row=0, column=1, padx=(0, 0), pady=0, sticky="ns")

        # API key warning if not set
        if not keyring_manager.has_key("anthropic"):
            self._add_message(
                "system",
                "⚠️  No Anthropic API key found. Add one in Preferences → API Keys "
                "to enable the AI assistant. Get a free key at console.anthropic.com.",
            )

    def _on_enter(self, event):
        """Send on Enter, newline on Shift+Enter."""
        if not event.state & 0x1:  # Shift not held
            self._send()
            return "break"

    def _send(self):
        message = self._input.get("1.0", "end").strip()
        if not message:
            return

        self._input.delete("1.0", "end")
        self._add_message("user", message)
        self._send_btn.configure(state="disabled", text="⟳")

        def _call_api():
            try:
                from integrations.claude_assistant import ClaudeAssistant
                assistant = ClaudeAssistant(
                    api_key=keyring_manager.get_key("anthropic"),
                    system_prompt=self._build_system_prompt(),
                )
                response = assistant.chat(self._history)
                self._add_message("assistant", response)
            except Exception as e:
                self._add_message("system", f"Error: {str(e)[:120]}")
            finally:
                self._send_btn.configure(state="normal", text="Send")

        threading.Thread(target=_call_api, daemon=True).start()

    def _build_system_prompt(self) -> str:
        """Inject current search context into the system prompt."""
        results = self.main_window.get_job_results()
        context = ""
        if results:
            titles = list({j.title for j in results[:10]})
            context = (
                f"\n\nThe user currently has {len(results)} job results loaded. "
                f"Recent job titles include: {', '.join(titles[:5])}."
            )
        return self.SYSTEM_PROMPT + context

    def _add_message(self, role: str, text: str):
        """Add a message bubble to the chat history."""
        if role == "user":
            self._history.append({"role": "user", "content": text})

        is_user = role == "user"
        bubble_color = ("gray75", "gray30") if is_user else ("gray90", "gray20")
        anchor = "e" if is_user else "w"

        bubble = ctk.CTkFrame(self._chat_frame,
                              fg_color=bubble_color, corner_radius=12)
        bubble.grid(sticky=anchor, pady=4,
                    padx=(80, 8) if is_user else (8, 80))

        ctk.CTkLabel(
            bubble, text=text, wraplength=520,
            font=ctk.CTkFont(size=13), justify="left", anchor="w",
        ).pack(padx=14, pady=10)

        if role == "assistant":
            self._history.append({"role": "assistant", "content": text})

        # Auto-scroll to bottom
        self._chat_frame._parent_canvas.yview_moveto(1.0)

    def on_results_updated(self, results: list):
        pass
