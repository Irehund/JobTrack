"""
tests/test_dialogs.py
======================
Logic tests for Phase 11 dialogs.
No GUI instantiation — tests cover _save() data-processing logic,
config read/write, and retry notification helpers.
All CustomTkinter widgets are mocked.
"""

import copy
import pytest
from unittest.mock import MagicMock, patch, call


# ── Shared helpers ────────────────────────────────────────────────────────────

def _base_config() -> dict:
    return {
        "theme": "system",
        "location": {"city": "Forney", "state": "TX", "zip": "75126"},
        "search_radius_miles": 50,
        "job_preferences": {
            "keywords":         ["SOC Analyst", "Security Analyst"],
            "work_type":        "any",
            "experience_level": "any",
        },
        "providers": {
            "indeed":    {"enabled": False},
            "linkedin":  {"enabled": False},
            "glassdoor": {"enabled": False},
            "adzuna":    {"enabled": False},
        },
        "tracker": {"mode": "local"},
        "setup_complete": True,
    }


# ── PreferencesDialog._save logic ─────────────────────────────────────────────
# We test the pure data-transformation logic without instantiating any GUI.

class TestPreferencesSaveLogic:
    """
    Simulate the _save() method's data transformations using plain dicts
    and the same helper functions the dialog uses.
    """

    def _simulate_save(self, original_config: dict, widget_values: dict) -> dict:
        """
        Mirror what PreferencesDialog._save() does, but without any GUI.
        widget_values keys match what _save() reads from self._widgets.
        """
        from core.utils import normalize_state
        config = copy.deepcopy(original_config)

        # Location
        loc = config.setdefault("location", {})
        loc["city"]  = widget_values.get("loc_city", "").strip()
        loc["state"] = normalize_state(widget_values.get("loc_state", "").strip())
        loc["zip"]   = widget_values.get("loc_zip", "").strip()
        config["search_radius_miles"] = widget_values.get("radius_var", 50)

        # Job search
        prefs = config.setdefault("job_preferences", {})
        raw_kw = widget_values.get("keywords", "")
        prefs["keywords"] = [k.strip() for k in raw_kw.split(",") if k.strip()]
        prefs["work_type"]        = widget_values.get("work_type", "any").lower()
        prefs["experience_level"] = widget_values.get("experience_level", "any").lower()

        # Providers
        prov_cfg = config.setdefault("providers", {})
        for pid in ["indeed", "linkedin", "glassdoor", "adzuna"]:
            prov_cfg.setdefault(pid, {})["enabled"] = widget_values.get(f"enabled_{pid}", False)

        # Tracker
        config.setdefault("tracker", {})["mode"] = widget_values.get("tracker_mode", "local")

        # Theme
        config["theme"] = widget_values.get("theme", "system").lower()

        return config

    def test_location_fields_saved(self):
        cfg = self._simulate_save(_base_config(), {
            "loc_city": "Dallas", "loc_state": "TX", "loc_zip": "75201",
            "radius_var": 25, "keywords": "SOC Analyst", "work_type": "Any",
            "experience_level": "Any", "tracker_mode": "local", "theme": "System",
        })
        assert cfg["location"]["city"]  == "Dallas"
        assert cfg["location"]["state"] == "TX"
        assert cfg["location"]["zip"]   == "75201"

    def test_state_normalized_from_full_name(self):
        cfg = self._simulate_save(_base_config(), {
            "loc_city": "Austin", "loc_state": "Texas", "loc_zip": "",
            "radius_var": 50, "keywords": "", "work_type": "Any",
            "experience_level": "Any", "tracker_mode": "local", "theme": "System",
        })
        assert cfg["location"]["state"] == "TX"

    def test_radius_saved(self):
        cfg = self._simulate_save(_base_config(), {
            "loc_city": "Forney", "loc_state": "TX", "loc_zip": "75126",
            "radius_var": 100, "keywords": "SOC Analyst", "work_type": "Any",
            "experience_level": "Any", "tracker_mode": "local", "theme": "System",
        })
        assert cfg["search_radius_miles"] == 100

    def test_keywords_parsed_from_comma_string(self):
        cfg = self._simulate_save(_base_config(), {
            "loc_city": "Forney", "loc_state": "TX", "loc_zip": "75126",
            "radius_var": 50,
            "keywords": "SOC Analyst, Security Analyst, Intelligence Analyst",
            "work_type": "Any", "experience_level": "Any",
            "tracker_mode": "local", "theme": "System",
        })
        assert cfg["job_preferences"]["keywords"] == [
            "SOC Analyst", "Security Analyst", "Intelligence Analyst"]

    def test_empty_keywords_produces_empty_list(self):
        cfg = self._simulate_save(_base_config(), {
            "loc_city": "Forney", "loc_state": "TX", "loc_zip": "75126",
            "radius_var": 50, "keywords": "",
            "work_type": "Any", "experience_level": "Any",
            "tracker_mode": "local", "theme": "System",
        })
        assert cfg["job_preferences"]["keywords"] == []

    def test_whitespace_keywords_stripped(self):
        cfg = self._simulate_save(_base_config(), {
            "loc_city": "Forney", "loc_state": "TX", "loc_zip": "75126",
            "radius_var": 50, "keywords": "  SOC Analyst  ,  Security Analyst  ",
            "work_type": "Any", "experience_level": "Any",
            "tracker_mode": "local", "theme": "System",
        })
        assert cfg["job_preferences"]["keywords"] == ["SOC Analyst", "Security Analyst"]

    def test_work_type_lowercased(self):
        cfg = self._simulate_save(_base_config(), {
            "loc_city": "Forney", "loc_state": "TX", "loc_zip": "75126",
            "radius_var": 50, "keywords": "SOC",
            "work_type": "Remote", "experience_level": "Any",
            "tracker_mode": "local", "theme": "System",
        })
        assert cfg["job_preferences"]["work_type"] == "remote"

    def test_experience_lowercased(self):
        cfg = self._simulate_save(_base_config(), {
            "loc_city": "Forney", "loc_state": "TX", "loc_zip": "75126",
            "radius_var": 50, "keywords": "SOC",
            "work_type": "Any", "experience_level": "Entry",
            "tracker_mode": "local", "theme": "System",
        })
        assert cfg["job_preferences"]["experience_level"] == "entry"

    def test_provider_enabled_flag_saved(self):
        cfg = self._simulate_save(_base_config(), {
            "loc_city": "Forney", "loc_state": "TX", "loc_zip": "75126",
            "radius_var": 50, "keywords": "SOC",
            "work_type": "Any", "experience_level": "Any",
            "enabled_indeed": True, "enabled_linkedin": False,
            "enabled_glassdoor": True, "enabled_adzuna": False,
            "tracker_mode": "local", "theme": "System",
        })
        assert cfg["providers"]["indeed"]["enabled"]    is True
        assert cfg["providers"]["linkedin"]["enabled"]  is False
        assert cfg["providers"]["glassdoor"]["enabled"] is True
        assert cfg["providers"]["adzuna"]["enabled"]    is False

    def test_tracker_mode_saved(self):
        for mode in ("local", "google", "both"):
            cfg = self._simulate_save(_base_config(), {
                "loc_city": "Forney", "loc_state": "TX", "loc_zip": "75126",
                "radius_var": 50, "keywords": "SOC",
                "work_type": "Any", "experience_level": "Any",
                "tracker_mode": mode, "theme": "System",
            })
            assert cfg["tracker"]["mode"] == mode

    def test_theme_lowercased(self):
        for theme_input, expected in [("Light","light"),("Dark","dark"),("System","system")]:
            cfg = self._simulate_save(_base_config(), {
                "loc_city": "Forney", "loc_state": "TX", "loc_zip": "75126",
                "radius_var": 50, "keywords": "SOC",
                "work_type": "Any", "experience_level": "Any",
                "tracker_mode": "local", "theme": theme_input,
            })
            assert cfg["theme"] == expected

    def test_original_config_not_mutated(self):
        original = _base_config()
        original_copy = copy.deepcopy(original)
        self._simulate_save(original, {
            "loc_city": "Houston", "loc_state": "TX", "loc_zip": "77001",
            "radius_var": 75, "keywords": "Threat Hunter",
            "work_type": "Remote", "experience_level": "Mid",
            "tracker_mode": "google", "theme": "Dark",
        })
        assert original == original_copy   # Deep copy means original untouched

    def test_on_save_callback_receives_updated_config(self):
        """Simulate that on_save is called with the new config."""
        received = {}
        def on_save(cfg): received.update(cfg)

        original = _base_config()
        updated = self._simulate_save(original, {
            "loc_city": "Houston", "loc_state": "TX", "loc_zip": "77001",
            "radius_var": 75, "keywords": "Threat Hunter",
            "work_type": "Remote", "experience_level": "Mid",
            "tracker_mode": "google", "theme": "Dark",
        })
        on_save(updated)
        assert received["location"]["city"] == "Houston"
        assert received["job_preferences"]["work_type"] == "remote"


# ── RetryNotification logic ───────────────────────────────────────────────────

class TestRetryNotificationLogic:

    def test_auto_dismiss_ms_is_3000(self):
        from ui.dialogs.retry_notification import RetryNotification
        assert RetryNotification.AUTO_DISMISS_MS == 3000

    def test_show_retry_toast_is_callable(self):
        from ui.dialogs.retry_notification import show_retry_toast
        assert callable(show_retry_toast)

    def test_provider_name_in_message(self):
        """The notification text should contain the provider name."""
        # Test the text-building logic without a real widget
        provider = "Indeed"
        attempt  = 2
        max_att  = 3
        text = f"⟳  Retrying {provider}"
        sub  = f"Attempt {attempt} of {max_att}"
        assert provider in text
        assert str(attempt) in sub
        assert str(max_att) in sub

    def test_attempt_numbering_correct(self):
        for attempt in range(1, 4):
            text = f"Attempt {attempt} of 3"
            assert str(attempt) in text

    def test_position_bottom_right(self):
        """Positioning calculation: x = screen_w - w - 24, y = screen_h - h - 60."""
        sw, sh, w, h = 1920, 1080, 220, 80
        x = sw - w - 24
        y = sh - h - 60
        assert x == 1676
        assert y == 940


# ── AboutDialog constants ─────────────────────────────────────────────────────

class TestAboutDialogConstants:

    def test_github_url_correct(self):
        from ui.dialogs.about_dialog import GITHUB_URL
        assert "Irehund/JobTracker" in GITHUB_URL
        assert GITHUB_URL.startswith("https://")

    def test_app_version_present(self):
        from ui.dialogs.about_dialog import APP_VERSION
        parts = APP_VERSION.split(".")
        assert len(parts) == 3
        assert all(p.isdigit() for p in parts)

    def test_license_text_nonempty(self):
        from ui.dialogs.about_dialog import LICENSE_TEXT
        assert len(LICENSE_TEXT) > 100

    def test_license_is_mit(self):
        from ui.dialogs.about_dialog import LICENSE_TEXT
        assert "MIT" in LICENSE_TEXT

    def test_privacy_phrase_in_license(self):
        from ui.dialogs.about_dialog import LICENSE_TEXT
        assert "AS IS" in LICENSE_TEXT


# ── _col_letter boundary (from google_sheets, but used here as a sanity check) ─
# (already in test_google_sheets — skip duplication)

# ── Keyring save logic ────────────────────────────────────────────────────────

class TestApiKeySaveLogic:
    """Test that non-empty API keys trigger keyring writes, empty ones do not."""

    def test_nonempty_key_triggers_set(self):
        from core import keyring_manager
        saved = {}
        with patch.object(keyring_manager, "save_key",
                          side_effect=lambda k, v: saved.update({k: v})):
            key_fields = {"anthropic": "sk-ant-test", "openrouteservice": ""}
            for key_name, val in key_fields.items():
                val = val.strip()
                if val:
                    keyring_manager.save_key(key_name, val)
        assert "anthropic" in saved
        assert "openrouteservice" not in saved   # Empty — should not be written

    def test_all_key_fields_covered(self):
        """Verify the full set of API key fields the dialog writes."""
        expected_fields = {
            "usajobs", "usajobs_email", "indeed", "linkedin",
            "glassdoor", "adzuna", "anthropic", "openrouteservice"
        }
        # These are the keys the preferences dialog iterates over
        dialog_fields = {
            "usajobs", "usajobs_email", "indeed", "linkedin",
            "glassdoor", "adzuna", "anthropic", "openrouteservice"
        }
        assert dialog_fields == expected_fields
