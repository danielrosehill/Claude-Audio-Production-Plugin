---
name: install-deps
description: Provision the plugin's tools — system binaries via the host package manager, all Python tools into a plugin-owned uv venv at <data-dir>/venv/. Idempotent doctor — run before onboard or any time a command reports a missing dep. Never touches system Python or fights PEP 668.
disable-model-invocation: true
allowed-tools: Bash(which *), Bash(command *), Bash(apt *), Bash(apt-get *), Bash(sudo *), Bash(uv *), Bash(curl *), Bash(python3 *), Bash(ffmpeg *), Bash(ffprobe *), Bash(sox *), Bash(typst *), Read, Write
---

# Install Dependencies

Two surfaces:

1. **System binaries** — `ffmpeg`, optional `sox` / `typst`. Installed via the host package manager with explicit user approval.
2. **Python tools** — `librosa`, `numpy`, `deepfilternet` (the `deepFilter` binary), optional `parselmouth`, `silero-vad`, `matplotlib`. Installed into a plugin-owned uv venv at `<data-dir>/venv/`.

The plugin's commands always invoke Python via `<data-dir>/venv/bin/python` and `<data-dir>/venv/bin/deepFilter`, so the user's system Python stays untouched and PEP 668 / externally-managed-environment errors never occur.

## Resolve paths

```bash
PLUGIN_DATA_DIR="${CLAUDE_USER_DATA:-${XDG_DATA_HOME:-$HOME/.local/share}/claude-plugins}/audio-production"
VENV_DIR="$PLUGIN_DATA_DIR/venv"
```

## Procedure

### 1. Detect host

```bash
uname -s   # Linux / Darwin
which apt-get apt brew dnf pacman 2>/dev/null
which uv 2>/dev/null
```

Record what's available; this drives which install commands you propose.

### 2. Ensure `uv` is available

`uv` is the only hard prerequisite for the Python side. If missing, propose installing it:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Ask before running. If the user declines, fall back to system pip with `--break-system-packages` or an apt-installed `python3-venv` + manual `python3 -m venv`. Document the fallback path but prefer `uv`.

### 3. Walk the system-binary matrix

| Tool | Detect | Required? | Install (apt) | Install (brew) |
|---|---|---|---|---|
| `ffmpeg` + `ffprobe` | `which ffmpeg && which ffprobe` | required | `sudo apt install ffmpeg` | `brew install ffmpeg` |
| `sox` | `which sox` | optional | `sudo apt install sox` | `brew install sox` |
| `typst` | `which typst` | optional | `cargo install typst-cli` (or download binary) | `brew install typst` |

For each: if missing, stage the install command tagged required/optional.

### 4. Provision the venv

If `<VENV_DIR>` doesn't exist:

```bash
uv venv "$VENV_DIR" --python 3.11
```

Pinning to Python 3.11 avoids the moving target of system Python upgrades. If `uv` selects a different version (e.g. user only has 3.13), accept that — note it in the report.

If `<VENV_DIR>` exists, leave it. The venv is the persistent home for plugin Python tooling.

### 5. Install Python packages into the venv

The canonical install set:

| Package | Required? | Used by |
|---|---|---|
| `librosa` | required | profile-voice, tune-preset |
| `numpy` | required | profile-voice, tune-preset |
| `scipy` | required | profile-voice (peak finding) |
| `deepfilternet` | required | denoise (default engine), polish --mode=noisy |
| `praat-parselmouth` | optional | profile-voice (formants) |
| `silero-vad` | optional | truncate-silence (ML engine) |
| `torch` `torchaudio` | optional | silero-vad backing |
| `matplotlib` | optional | tune-preset (spectrogram rendering) |

Stage:

```bash
uv pip install --python "$VENV_DIR/bin/python" librosa numpy scipy deepfilternet
# optional bundle:
uv pip install --python "$VENV_DIR/bin/python" praat-parselmouth matplotlib
# silero bundle (heavy — only if user wants ML silence detection):
uv pip install --python "$VENV_DIR/bin/python" silero-vad torch torchaudio
```

Or, simpler (uses the venv's interpreter without the explicit `--python` flag):

```bash
source "$VENV_DIR/bin/activate"
uv pip install librosa numpy scipy deepfilternet
```

Either form is fine — pick whichever the user's shell handles cleanly.

### 6. Present the plan and approve

Print a summary block before running anything:

```
Plugin venv: <VENV_DIR> (python 3.11)

System binaries already installed:
  ✓ ffmpeg 6.1.1

Will install (system, required):
  [apt]  sudo apt install ffmpeg                 ← if ffmpeg missing

Will install into venv (required):
  uv pip install librosa numpy scipy deepfilternet

Will install into venv (optional):
  uv pip install praat-parselmouth matplotlib

Skipping unless requested:
  silero-vad torch torchaudio   (large, only needed for ML silence detection)
```

Ask the user three questions:

1. Proceed with required installs? (y/N)
2. Also install the optional bundle? (y/N)
3. Install the silero bundle? (y/N)

### 7. Execute approved installs

Run each approved command, surfacing stdout/stderr. After each:

- For system installs: re-run the detect command to verify.
- For venv installs: `"$VENV_DIR/bin/python" -c "import <pkg>"` to verify importability.
- If verification fails, stop and report — don't proceed to the next install.

### 8. Final verification table

```
Status:
  ✓ ffmpeg
  ✓ uv
  ✓ venv at <VENV_DIR>
  ✓ librosa (in venv)
  ✓ numpy (in venv)
  ✓ scipy (in venv)
  ✓ deepfilternet (deepFilter binary at <VENV_DIR>/bin/deepFilter)
  ✓ matplotlib (in venv, optional)
  ✓ parselmouth (in venv, optional)
  · silero-vad (optional, not installed)
  · sox (optional, not installed)
  · typst (optional, not installed)
```

If any **required** dep is still missing, stop with a clear message — the plugin won't function fully.

## Plugin-side conventions (for other commands and skills)

Other commands in this plugin must invoke Python via the venv interpreter, not system `python3`:

```bash
PYTHON="$PLUGIN_DATA_DIR/venv/bin/python"
DEEPFILTER="$PLUGIN_DATA_DIR/venv/bin/deepFilter"

"$PYTHON" - <<'PY'
import librosa, numpy as np
...
PY

"$DEEPFILTER" "<input>" -o "<out-dir>"
```

If the venv doesn't exist when one of those commands runs, the command should refuse and tell the user to run `/audio-production:install-deps`.

## Idempotence

Running this skill repeatedly is safe — `uv venv` is a no-op if the venv exists, and `uv pip install` skips already-satisfied packages.

To upgrade everything later:

```bash
"$VENV_DIR/bin/python" -m uv pip install -U librosa numpy scipy deepfilternet
```

## Notes

- All Python tooling lives under `<data-dir>/venv/`. Wipe it (`rm -rf "$VENV_DIR"`) and re-run this skill to start fresh.
- System Python is never modified.
- `uv` is preferred over `pip`, `pipx`, or `apt`-installed Python packages because it sidesteps PEP 668, resolves dependencies fast, and produces a self-contained, portable venv.
- No MCPs, no network calls beyond the package managers' own.
