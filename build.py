#!/usr/bin/env python3
"""
build.py
=========
Cross-platform build script for JobTrack.

Usage:
    python build.py              # Build release (folder dist)
    python build.py --onefile    # Build single-file .exe (slower first launch)
    python build.py --clean      # Clean previous build artifacts
    python build.py --check      # Verify deps are installed, no build
    python build.py --version    # Show version and exit

What it does:
    1. Checks all required dependencies are installed
    2. Generates version_info.txt (Windows only)
    3. Runs pyinstaller with jobtrack.spec
    4. Prints the output path and file size
"""

import os
import sys
import shutil
import subprocess
import argparse
from pathlib import Path

# ── Version ───────────────────────────────────────────────────────────────────
APP_VERSION   = "1.0.0"
APP_NAME      = "JobTrack"
COMPANY_NAME  = "JobTrack Contributors"
FILE_DESCR    = "JobTrack — Job Search Manager"
SCRIPT_DIR    = Path(__file__).parent.resolve()

# ── Required packages (import names, not pip names) ───────────────────────────
REQUIRED = [
    ("customtkinter",          "customtkinter"),
    ("PIL",                    "Pillow"),
    ("folium",                 "folium"),
    ("requests",               "requests"),
    ("anthropic",              "anthropic"),
    ("gspread",                "gspread"),
    ("google.oauth2",          "google-auth"),
    ("google_auth_oauthlib",   "google-auth-oauthlib"),
    ("keyring",                "keyring"),
    ("PyInstaller",            "pyinstaller"),
]


def check_deps() -> bool:
    """Return True if all required packages are importable."""
    missing = []
    for import_name, pip_name in REQUIRED:
        try:
            __import__(import_name)
        except ImportError:
            missing.append(pip_name)

    if missing:
        print(f"\n❌  Missing packages: {', '.join(missing)}")
        print(f"    Run: pip install {' '.join(missing)}")
        return False

    print("✅  All dependencies found.")
    return True


def clean():
    """Remove build/ and dist/ directories."""
    for d in ["build", "dist"]:
        path = SCRIPT_DIR / d
        if path.exists():
            shutil.rmtree(path)
            print(f"🗑️   Removed {d}/")
    pycache = list(SCRIPT_DIR.rglob("__pycache__"))
    for d in pycache:
        shutil.rmtree(d)
    print("✅  Clean complete.")


def generate_version_info() -> Path:
    """Generate Windows version_info.txt for the EXE metadata."""
    major, minor, patch_ = APP_VERSION.split(".")
    content = f"""# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({major}, {minor}, {patch_}, 0),
    prodvers=({major}, {minor}, {patch_}, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'{COMPANY_NAME}'),
         StringStruct(u'FileDescription', u'{FILE_DESCR}'),
         StringStruct(u'FileVersion', u'{APP_VERSION}.0'),
         StringStruct(u'InternalName', u'{APP_NAME}'),
         StringStruct(u'LegalCopyright', u'MIT License'),
         StringStruct(u'OriginalFilename', u'{APP_NAME}.exe'),
         StringStruct(u'ProductName', u'{APP_NAME}'),
         StringStruct(u'ProductVersion', u'{APP_VERSION}.0')])
    ]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
"""
    out = SCRIPT_DIR / "version_info.txt"
    out.write_text(content, encoding="utf-8")
    print(f"📝  Generated {out.name}")
    return out


def patch_spec_for_onefile():
    """Rewrite spec to produce a single-file executable."""
    spec_path = SCRIPT_DIR / "jobtrack.spec"
    content   = spec_path.read_text()

    # Swap folder-mode EXE for single-file EXE
    content = content.replace(
        "exclude_binaries=True,",
        "exclude_binaries=False,",
    )
    # Remove COLLECT block so PyInstaller builds one file
    lines    = content.splitlines()
    filtered = [l for l in lines if not l.strip().startswith("coll = COLLECT")]
    spec_path.write_text("\n".join(filtered))
    print("🔧  Spec patched for single-file build.")


def build(onefile: bool = False) -> bool:
    """Run PyInstaller. Returns True on success."""
    if sys.platform == "win32":
        generate_version_info()

    if onefile:
        patch_spec_for_onefile()

    print(f"\n🔨  Building JobTrack v{APP_VERSION}...")
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        str(SCRIPT_DIR / "jobtrack.spec"),
    ]

    result = subprocess.run(cmd, cwd=SCRIPT_DIR)

    if result.returncode != 0:
        print("\n❌  Build failed. Check PyInstaller output above.")
        return False

    # ── Report output ─────────────────────────────────────────────────────────
    if onefile:
        suffix = ".exe" if sys.platform == "win32" else ""
        output = SCRIPT_DIR / "dist" / f"{APP_NAME}{suffix}"
    else:
        output = SCRIPT_DIR / "dist" / APP_NAME

    if output.exists():
        if output.is_file():
            size_mb = output.stat().st_size / (1024 * 1024)
            print(f"\n✅  Build complete: {output}")
            print(f"    Size: {size_mb:.1f} MB")
        else:
            # Count files in folder dist
            files = list(output.rglob("*"))
            exe = output / (APP_NAME + (".exe" if sys.platform == "win32" else ""))
            size_mb = sum(f.stat().st_size for f in files if f.is_file()) / (1024 * 1024)
            print(f"\n✅  Build complete: {output}/")
            print(f"    Total size: {size_mb:.1f} MB  ({len(files)} files)")
            if exe.exists():
                print(f"    Launch: {exe}")
    else:
        print(f"\n⚠️   Build may have succeeded but output not found at: {output}")

    return True


def main():
    parser = argparse.ArgumentParser(description=f"Build {APP_NAME}")
    parser.add_argument("--onefile", action="store_true",
                        help="Build single-file executable (slower first launch)")
    parser.add_argument("--clean",   action="store_true",
                        help="Remove build/ and dist/ before building")
    parser.add_argument("--check",   action="store_true",
                        help="Check dependencies only, no build")
    parser.add_argument("--version", action="store_true",
                        help="Print version and exit")
    args = parser.parse_args()

    if args.version:
        print(f"{APP_NAME} v{APP_VERSION}")
        return

    if args.check:
        ok = check_deps()
        sys.exit(0 if ok else 1)

    if args.clean:
        clean()
        if len(sys.argv) == 2:   # --clean only, no build
            return

    if not check_deps():
        sys.exit(1)

    success = build(onefile=args.onefile)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
