# Building JobTrack

## Quick start

```bash
# Install dependencies
pip install -r requirements.txt

# Build (folder distribution — recommended)
python build.py

# Build single-file .exe (slower first launch, easier to distribute)
python build.py --onefile

# Check deps without building
python build.py --check
```

## Output

| Mode | Output | Notes |
|------|--------|-------|
| Default (folder) | `dist/JobTrack/JobTrack.exe` | Faster launch, easier to debug |
| `--onefile` | `dist/JobTrack.exe` | One file, ~5s slower first launch |
| macOS | `dist/JobTrack.app` | Double-click to run |

## Prerequisites

- Python 3.11 or 3.12 (3.10 may work, 3.13 not yet tested)
- All packages in `requirements.txt`
- **Windows:** No extra setup needed — keyring uses Windows Credential Manager
- **macOS:** `pip install pyobjc-framework-Security` if keyring errors appear

## Troubleshooting

### "No module named X" at runtime
Add the module to `hiddenimports` in `jobtrack.spec`.

### App opens then immediately closes (Windows)
Run from terminal to see the traceback:
```
dist\JobTrack\JobTrack.exe
```
Or temporarily set `console=True` in the spec to see the error window.

### customtkinter assets missing (buttons look wrong)
Ensure `collect_data_files("customtkinter")` is in the spec's `datas` list.
This copies customtkinter's built-in themes and images into the bundle.

### keyring errors on first launch
On Windows, keyring uses the Windows Credential Manager — no setup needed.
On macOS, it uses the system Keychain — may prompt for permission on first use.
On Linux, install `secretstorage`: `pip install secretstorage`.

### Google OAuth browser window doesn't open (packaged app)
The OAuth flow calls `webbrowser.open()` — this works in packaged apps.
If it fails, ensure the user's default browser is set.

### Map doesn't load (packaged app)
The map is written to a temp file and opened in the system browser via
`webbrowser.open(f"file://{path}")`. This works without network access.

## macOS code signing (optional, for distribution)

```bash
# Sign the app
codesign --deep --force --verify --verbose \
  --sign "Developer ID Application: Your Name (TEAMID)" \
  dist/JobTrack.app

# Notarize (requires Apple Developer account)
xcrun notarytool submit dist/JobTrack.zip \
  --apple-id you@example.com \
  --team-id YOURTEAMID \
  --password "@keychain:AC_PASSWORD"
```

## Windows installer (optional, using Inno Setup)

After building with PyInstaller, use the provided `installer.iss` with
[Inno Setup](https://jrsoftware.org/isinfo.php) to create a proper installer:

```
iscc installer.iss
```

This creates `dist/JobTrack_Setup_1.0.0.exe`.

## File size targets

| Component | Expected contribution |
|-----------|----------------------|
| Python runtime | ~8 MB |
| customtkinter + tkinter | ~5 MB |
| Requests + urllib3 | ~2 MB |
| Anthropic SDK + httpx | ~8 MB |
| gspread + google-auth | ~5 MB |
| folium + branca | ~3 MB |
| Your app code | ~1 MB |
| **Total (approx)** | **~32–40 MB** |

UPX compression (enabled in spec) reduces this by ~30%.
