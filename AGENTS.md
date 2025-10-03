# Repository Guidelines

## Project Structure & Module Organization

- `client_win-mac-nix/` contains the cross-platform client entry point `main.py` plus OS-specific hotkey and mouse adapters (`hotkey_win_mac.py`, `mouse_nix_uinput.py`, etc.).
- `server_raspberrypi/` hosts the Pi capture pipeline (`main.py`) and helper scripts (`scale_contour.py`, `bashrc`). Keep camera and hardware logic scoped here.
- Use `CLAUDE.md` for extended setup notes so the repository root stays focused on runnable code and high-level docs.

## Build, Test, and Development Commands

- `python3 server_raspberrypi/main.py --verbose --preview` starts the camera server with on-device preview for tuning thresholds and masks.
- `python3 client_win-mac-nix/main.py --verbose --speed 21 --smooth 3` launches the desktop client with the defaults Phil ships; tweak flags to validate new features.
- Use `--x-speed` and `--y-speed` for independent X/Y axis control (default Y is 1.25x faster than X).
- Activate the virtual environment with `source .venv/bin/activate` when present, then log new dependencies in `requirements.txt` before `pip install -r requirements.txt`.

## Coding Style & Naming Conventions

- Follow PEP 8 with 4-space indentation; prefer explicit verbs in function names (`send_udp_packet`, not `sendPkt`).
- Keep module-level constants uppercase (`DEFAULT_SPEED`), runtime flags lowercase with underscores, and platform-specific modules following the `mouse_<platform>.py` / `hotkey_<platform>.py` pattern.
- **CRITICAL**: Always run `pyright` after any code changes to ensure type correctness. The project maintains zero errors and zero warnings across all platforms.
- Run `ruff check .` and `black .` if you introduce them; document new tooling both here and in `CLAUDE.md`.

## Testing Guidelines

- No automated suite exists yet—add pytest modules under `tests/` when you contribute logic that can run without hardware.
- For manual verification, capture server logs with `--verbose --preview` and confirm client cursor motion on at least two targets (e.g., macOS plus Linux `/dev/uinput`). Summarize findings in your pull request.
- Favor deterministic helpers that can be unit-tested without the camera; add sample frames or fixtures only when they improve regression coverage.

## Commit & Pull Request Guidelines

- Use concise, imperative commit messages (`Add rotate option`, `Refine uinput permissions`) consistent with `git log`.
- Limit each pull request to one focused change. Provide a summary, configuration notes, and platform coverage in the description, linking issues with `Fixes #123` when applicable.
- Attach short clips or screenshots when touching tracking, smoothing, or hotkeys. Highlight permission or network changes and update `CLAUDE.md` in the same PR.

## Deployment & Configuration Tips

- Document Raspberry Pi package updates in `server_raspberrypi/bashrc`, and verify any `sudo` steps still succeed on a clean Pi OS image.
- Keep default UDP ports (4245/4246) unless coordinated with downstream clients, and flag port changes in the pull request.
