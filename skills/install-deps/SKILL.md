---
name: install-deps
description: Verify and (with user approval) install the system tools and Python packages this plugin depends on. Required tools — ffmpeg, librosa, numpy, deepfilternet. Optional — parselmouth (formants), silero-vad (better silence detection), sox, typst. Run before onboard or any time a command reports a missing dependency.
disable-model-invocation: true
allowed-tools: Bash(which *), Bash(command *), Bash(apt *), Bash(apt-get *), Bash(sudo *), Bash(pip *), Bash(pip3 *), Bash(uv *), Bash(pipx *), Bash(python3 *), Bash(ffmpeg *), Bash(ffprobe *), Bash(deepFilter *), Bash(sox *), Bash(typst *), Read, Write
---

# Install Dependencies

Check the plugin's runtime dependencies and offer to install any that are missing.

## Approach

This skill never installs silently. For each missing dependency it:

1. Detects the package manager available on the host (apt for Debian/Ubuntu, brew for macOS, pacman for Arch, dnf for Fedora).
2. Detects whether `uv`, `pipx`, or plain `pip` is available for Python packages.
3. Surfaces the exact command(s) it would run.
4. Asks the user to approve before executing.

If multiple install paths are valid (e.g. `uv tool install` vs `pipx install` vs `pip install --user`), prefer the one already present on the system; otherwise prefer in the order: `uv` → `pipx` → `pip --user`.

## Dependency matrix

### Required

| Tool | Used by | Detect | Install (Linux apt) | Install (macOS brew) |
|---|---|---|---|---|
| `ffmpeg` + `ffprobe` | every audio command | `which ffmpeg && which ffprobe` | `sudo apt install ffmpeg` | `brew install ffmpeg` |
| Python 3.10+ | profile-voice, denoise | `python3 --version` | `sudo apt install python3` | preinstalled or `brew install python` |
| `librosa` (Python) | profile-voice | `python3 -c "import librosa"` | `pip install --user librosa numpy` | same |
| `numpy` (Python) | profile-voice | `python3 -c "import numpy"` | covered by librosa install | same |
| `deepfilternet` (binary `deepFilter`) | denoise (default engine) | `which deepFilter` | `uv tool install deepfilternet` or `pipx install deepfilternet` | same |

### Optional

| Tool | Used by | Detect | Install |
|---|---|---|---|
| `praat-parselmouth` (Python) | profile-voice (formants) | `python3 -c "import parselmouth"` | `pip install --user praat-parselmouth` |
| `silero-vad` (Python) | truncate-silence (ML engine) | `python3 -c "import silero_vad"` | `pip install --user silero-vad torch torchaudio` |
| `sox` | some `trim-silence` paths | `which sox` | `sudo apt install sox` / `brew install sox` |
| `typst` | export paths | `which typst` | `cargo install typst-cli` or download binary release |

## Procedure

### 1. Detect host

```bash
uname -s   # Linux / Darwin
which apt-get apt brew dnf pacman 2>/dev/null
which uv pipx pip3 2>/dev/null
```

Record what's available; this drives which install commands you propose.

### 2. Walk the matrix

For each row in **Required**:

- Run the detect command.
- If present: report `✓ <tool>` with version where readily available.
- If missing: stage an install command for that tool, tagged `[required]`.

Then for each row in **Optional**:

- Run the detect command.
- If present: report `✓ <tool> (optional)`.
- If missing: stage an install command tagged `[optional]`. These will be presented but not required.

### 3. Present the plan

Print a summary block:

```
Already installed:
  ✓ ffmpeg 6.1.1
  ✓ python3 3.13
  ✓ librosa 0.11.0
  ✓ numpy 2.0.0

Will install (required):
  [apt]   sudo apt install ffmpeg
  [pipx]  pipx install deepfilternet

Will install (optional, can skip):
  [pip]   pip install --user praat-parselmouth
  [pip]   pip install --user silero-vad torch torchaudio
```

Then ask the user three questions:

1. Proceed with required installs? (y/N)
2. Also install optional packages? (y/N)
3. If apt commands are present and the user is on Linux: confirm sudo is OK.

### 4. Execute approved installs

Run each approved command, one at a time, surfacing stdout/stderr. After each:

- Re-run the detect command to verify.
- If still missing, stop and report — don't proceed to the next install.

### 5. Final verification

After installs complete, re-run every detect command and print a clean status table:

```
Status:
  ✓ ffmpeg
  ✓ python3
  ✓ librosa
  ✓ numpy
  ✓ deepfilternet
  ✓ parselmouth (optional)
  · silero-vad (optional, not installed)
  · sox (optional, not installed)
  · typst (optional, not installed)
```

If any **required** dep is still missing, tell the user the plugin won't function fully and stop with a non-zero exit indication.

## Idempotence

Running this skill repeatedly is safe — it only installs what's missing. Use it as a "doctor" command at any time.

## Notes

- This skill is the canonical place to teach users how to install the plugin's deps. Other skills/commands that detect a missing dep should point users back here: "Run `/audio-production:install-deps` to install missing tools."
- Never bypass the user's approval — even on a dev machine, surprise installs break trust.
- For Python packages, default to user-scope installs (`--user`, `pipx`, `uv tool`) — never global system Python.
- No MCPs, no network calls beyond the package managers' own.
