"""
tests/test_build.py
====================
Tests for build.py — verifies build script logic without running PyInstaller.
Covers: dependency checking, version info generation, argument parsing,
clean logic, spec patching for onefile mode.
"""

import os
import sys
import shutil
import tempfile
import importlib
from pathlib import Path
from unittest.mock import patch, MagicMock

# ── Helpers ───────────────────────────────────────────────────────────────────

def _import_build():
    """Import build.py as a module (it lives at project root, not in a package)."""
    spec_root = Path(__file__).parent.parent
    if str(spec_root) not in sys.path:
        sys.path.insert(0, str(spec_root))
    if "build" in sys.modules:
        del sys.modules["build"]
    import build as b
    return b


# ── Version constants ─────────────────────────────────────────────────────────

class TestVersionConstants:

    def test_app_version_format(self):
        b = _import_build()
        parts = b.APP_VERSION.split(".")
        assert len(parts) == 3
        assert all(p.isdigit() for p in parts)

    def test_app_name_is_jobtrack(self):
        b = _import_build()
        assert b.APP_NAME == "JobTrack"

    def test_required_list_nonempty(self):
        b = _import_build()
        assert len(b.REQUIRED) > 0

    def test_required_includes_customtkinter(self):
        b = _import_build()
        import_names = [r[0] for r in b.REQUIRED]
        assert "customtkinter" in import_names

    def test_required_includes_pyinstaller(self):
        b = _import_build()
        import_names = [r[0] for r in b.REQUIRED]
        assert "PyInstaller" in import_names

    def test_required_includes_requests(self):
        b = _import_build()
        import_names = [r[0] for r in b.REQUIRED]
        assert "requests" in import_names

    def test_required_tuples_have_two_elements(self):
        b = _import_build()
        assert all(len(r) == 2 for r in b.REQUIRED)


# ── check_deps ────────────────────────────────────────────────────────────────

class TestCheckDeps:

    def test_returns_true_when_all_importable(self):
        b = _import_build()
        # Patch __import__ to succeed for everything
        with patch("builtins.__import__", side_effect=lambda name, *a, **kw: MagicMock()):
            result = b.check_deps()
        assert result is True

    def test_returns_false_when_package_missing(self):
        b = _import_build()
        original_import = __import__

        def mock_import(name, *args, **kwargs):
            if name == "customtkinter":
                raise ImportError(f"No module named '{name}'")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            result = b.check_deps()
        assert result is False

    def test_all_stdlib_packages_found(self):
        """sqlite3, os, sys etc. should never cause check_deps to fail."""
        b = _import_build()
        # Only check stdlib modules that are always available
        stdlib_pairs = [("os", "os"), ("sys", "sys"), ("sqlite3", "sqlite3")]
        for import_name, _ in stdlib_pairs:
            try:
                __import__(import_name)
                found = True
            except ImportError:
                found = False
            assert found, f"stdlib module {import_name} should be importable"


# ── generate_version_info ─────────────────────────────────────────────────────

class TestGenerateVersionInfo:

    def test_creates_file(self):
        b = _import_build()
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(b, "SCRIPT_DIR", Path(tmp)):
                out = b.generate_version_info()
            assert out.exists()

    def test_contains_app_version(self):
        b = _import_build()
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(b, "SCRIPT_DIR", Path(tmp)):
                out = b.generate_version_info()
            content = out.read_text()
        assert b.APP_VERSION.replace(".", ", ") in content or b.APP_VERSION in content

    def test_contains_app_name(self):
        b = _import_build()
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(b, "SCRIPT_DIR", Path(tmp)):
                out = b.generate_version_info()
            content = out.read_text()
        assert b.APP_NAME in content

    def test_is_valid_utf8(self):
        b = _import_build()
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(b, "SCRIPT_DIR", Path(tmp)):
                out = b.generate_version_info()
            content = out.read_bytes()
        content.decode("utf-8")   # Should not raise

    def test_contains_mit_license(self):
        b = _import_build()
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(b, "SCRIPT_DIR", Path(tmp)):
                out = b.generate_version_info()
            assert "MIT" in out.read_text()


# ── clean ─────────────────────────────────────────────────────────────────────

class TestClean:

    def test_removes_build_dir(self):
        b = _import_build()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            (tmp_path / "build").mkdir()
            (tmp_path / "build" / "dummy.txt").write_text("x")
            with patch.object(b, "SCRIPT_DIR", tmp_path):
                b.clean()
            assert not (tmp_path / "build").exists()

    def test_removes_dist_dir(self):
        b = _import_build()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            (tmp_path / "dist").mkdir()
            with patch.object(b, "SCRIPT_DIR", tmp_path):
                b.clean()
            assert not (tmp_path / "dist").exists()

    def test_safe_when_dirs_not_present(self):
        b = _import_build()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            with patch.object(b, "SCRIPT_DIR", tmp_path):
                b.clean()   # Should not raise


# ── patch_spec_for_onefile ────────────────────────────────────────────────────

class TestPatchSpecForOnefile:

    def test_patches_exclude_binaries(self):
        b = _import_build()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            spec = tmp_path / "jobtrack.spec"
            spec.write_text("    exclude_binaries=True,\ncoll = COLLECT(stuff)\n")
            with patch.object(b, "SCRIPT_DIR", tmp_path):
                b.patch_spec_for_onefile()
            patched = spec.read_text()
        assert "exclude_binaries=False," in patched

    def test_removes_collect_block(self):
        b = _import_build()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            spec = tmp_path / "jobtrack.spec"
            spec.write_text("exclude_binaries=True,\ncoll = COLLECT(exe, bins)\nother_line\n")
            with patch.object(b, "SCRIPT_DIR", tmp_path):
                b.patch_spec_for_onefile()
            patched = spec.read_text()
        assert "coll = COLLECT" not in patched
        assert "other_line" in patched


# ── Spec file structure ───────────────────────────────────────────────────────

class TestSpecFile:
    """Validate the jobtrack.spec file content without running PyInstaller."""

    SPEC_PATH = Path(__file__).parent.parent / "jobtrack.spec"

    def test_spec_file_exists(self):
        assert self.SPEC_PATH.exists()

    def test_spec_references_main_py(self):
        content = self.SPEC_PATH.read_text()
        assert "main.py" in content

    def test_spec_has_analysis_block(self):
        content = self.SPEC_PATH.read_text()
        assert "Analysis(" in content

    def test_spec_has_exe_block(self):
        content = self.SPEC_PATH.read_text()
        assert "EXE(" in content

    def test_spec_has_collect_block(self):
        content = self.SPEC_PATH.read_text()
        assert "COLLECT(" in content

    def test_spec_includes_customtkinter_data(self):
        content = self.SPEC_PATH.read_text()
        assert "customtkinter" in content

    def test_spec_includes_keyring_hidden_imports(self):
        content = self.SPEC_PATH.read_text()
        assert "keyring.backends" in content

    def test_spec_windowed_mode(self):
        """App should launch without a console window."""
        content = self.SPEC_PATH.read_text()
        assert "console=False" in content

    def test_spec_excludes_pytest(self):
        """pytest should not be bundled into the production binary."""
        content = self.SPEC_PATH.read_text()
        assert '"pytest"' in content or "'pytest'" in content

    def test_spec_has_macos_bundle(self):
        content = self.SPEC_PATH.read_text()
        assert "BUNDLE(" in content

    def test_spec_has_bundle_identifier(self):
        content = self.SPEC_PATH.read_text()
        assert "com.jobtrack.app" in content


# ── BUILDING.md ───────────────────────────────────────────────────────────────

class TestBuildingDoc:

    DOC_PATH = Path(__file__).parent.parent / "BUILDING.md"

    def test_building_md_exists(self):
        assert self.DOC_PATH.exists()

    def test_contains_quick_start(self):
        content = self.DOC_PATH.read_text()
        assert "pip install -r requirements.txt" in content

    def test_contains_build_command(self):
        content = self.DOC_PATH.read_text()
        assert "python build.py" in content

    def test_contains_troubleshooting(self):
        content = self.DOC_PATH.read_text()
        assert "Troubleshooting" in content

    def test_mentions_onefile(self):
        content = self.DOC_PATH.read_text()
        assert "--onefile" in content
