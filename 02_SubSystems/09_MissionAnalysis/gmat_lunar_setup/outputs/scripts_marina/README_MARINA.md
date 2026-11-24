# Marina — GMAT R2022a copies

All 77 files from `../scripts/` are included. All 17 `.script` files use the paths and shadow-setting change from Marina's supplied working `validation_transfer.script`. The copied transfer script is byte-for-byte identical to that supplied file.

## Run a mission script

Open GMAT on Marina's machine normally, using its own installed startup configuration. Use **File → Open** to select a `.script` from this folder, then run it.

- GMAT installation: `C:\Users\marin\OneDrive\Dokumente\gmat-win-R2022a\GMAT`
- Reports: `C:\Users\marin\OneDrive\Desktop\SMD`
- The transfer test writes `history.txt`, `burns.txt`, and `targeter.txt`, matching the working reference. Every other case prefixes its report filenames with the case name to avoid cross-case overwrites. Rerunning the same case replaces its reports.
- The full `option_a_*.script` files request approximately three years; use the short validation scripts for checkout first.

## Optional: prepare the copied startup files

The copied `.startup.txt` files are path-adjusted **R2026a templates**, not Marina's R2022a plugin configuration. Before explicitly supplying one to GMAT, generate it from her installed configuration. In PowerShell, from this folder:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\prepare_startups_marina.ps1
```

The execution-policy setting applies only to that PowerShell process. The helper reads Marina's own `bin\gmat_startup_file.txt` and replaces this folder's 34 startup templates with matching GUI/console configurations. It preserves her installed data filenames and plugins and sets per-case log filenames. It does not change her GMAT installation or propagate missions. The default paths match the supplied working script; optional `-GmatRoot` / `-OutputRoot` arguments apply to startup generation only, not paths already inside mission scripts.

## Model and evidence status

`ExtraShadowBodies = {Earth}` is commented out in every mission script, exactly as in the supplied working file. Earth gravity remains enabled; the intended extra Earth occultation contribution to SRP is omitted. Other mission values, force settings, durations, targeters and control logic are retained.

The existing JSON manifests, validation results and two log files are copied **historical R2026a evidence** from the original study. Their original paths and hashes describe those original inputs; they do not establish that these copies passed on Marina's machine. `MARINA_MANIFEST.json` separately records the original and adapted file hashes. The supplied transfer script is user-reported working on Marina's machine. The other cases and the PowerShell helper have not been executed on her Windows/R2022a installation. Local parse checks use R2026a with temporary Linux file paths only; see `marina_local_checks.json`.
