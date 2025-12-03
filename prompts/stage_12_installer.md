# Stage 12 - Installer and Distribution
## Objective
- Package ai_scalper_bot with installer and run scripts for operators.

## Current State
- Root contains ai_scalper_bot.iss, build_installer.bat, build_runbot_exe.ps1, run_bot.exe.spec, setup_bot.ps1, run_bot.cmd/start_bot.cmd, requirements.txt; README is empty.
- Installer not updated to include new prompts, monitoring, GUI, or configs.

## Missing Modules
- Updated installer config including settings.yaml defaults, storage folders, GUI launcher, prompts, and monitoring assets.
- Documentation on installation steps, prerequisites, and verification.
- Checksums/signing or validation steps for distributed artifacts.

## Modules To Update
- ai_scalper_bot.iss, build_installer.bat, build_runbot_exe.ps1, run_bot.exe.spec, setup_bot.ps1.
- README.md with installation/run instructions and stage summaries.
- requirements.txt alignment with new dependencies (GUI, monitoring, LLM client).

## Tasks
1) Create/update:
- Refresh installer scripts to include prompts directory, monitoring, GUI, storage directories, and config templates with safe defaults.
- Ensure run_bot.exe spec includes data files/icons; update build scripts for packaging.
- Add README covering setup, env vars, and how to run run_bot/offline_loop/GUI.
- Provide optional portable zip build instructions.
2) Implement logic:
- Validate installer respects security hardening (no secrets packaged); include sample .env only.
- Add post-install smoke tests or shortcuts to run GUI launcher and offline loop.
- Document upgrade path and rollback steps.
3) Config:
- Confirm settings.yaml bundled with safe defaults (app.mode=paper, websocket=mock) and placeholders for keys.

## Tests
Run:
```
pip install -r requirements.txt
python -m bot.sandbox.offline_loop --ticks-path data/ticks/BTCUSDT_synthetic.csv
python -m bot.run_bot
```
If build tools available:
```
powershell ./build_runbot_exe.ps1
```

## Verification Tasks
- Installer/build scripts run without missing file errors; produced artifacts launch bot.
- README shows clear steps; prompts directory included in package.
- git status clean except expected build artifacts (if committed intentionally).

## Expected Output
- Updated installers/executables containing latest code and prompts.
- Documentation enabling operators to install and launch easily.
- Verified startup commands post-install.

## Acceptance Criteria
- Build scripts succeed or report actionable errors.
- Packaged app starts run_bot/offline_loop/GUI with default config.
- Commit includes prompt suite and installer updates.

## Post-patch Commands
```
python -m bot.sandbox.offline_loop --ticks-path data/ticks/BTCUSDT_synthetic.csv
python -m bot.run_bot
```

## Commit
```
git add .
git commit -m "Stage 12 completed"
git push origin main
```
