AGENTS.md
This file gives AI coding agents (and new team members) the context needed to work in this repository.

What this repository is
LETO (Lunar Event-camera Transient Observatory) is a student space-mission design project for the Space Mission Design course at the Chair of Spacecraft Systems, TUM (AY 2026-2027). The team is taking the mission from ECSS Phase A (feasibility) into Phase B (preliminary definition). The System Requirements Review (SRR) was submitted on 20.11.2026.

This is a document and engineering-analysis repository, not a software product. There is no build system, test suite, or package manager yet. Work here is mostly reports, budgets, trade studies and, as subsystems mature, analysis scripts (e.g. Python/MATLAB) and models.

Mission in brief
Goal: build a sample of verified lunar impact flash to fresh crater pairs, to fit the empirical relation between emitted flash light energy (600-900 nm) and crater diameter (MO-001: at least 30 pairs minimum, 80 pairs full success).
Two phases, one spacecraft:
Flash observation (2.5 years) from a high lunar orbit (about 3000-7000 km) with 6-15 event-camera heads (Sony IMX636 sensor) watching the night side of the whole Moon, every 10° latitude band including the poles.
Crater imaging (about 6 months) after an orbit-lowering manoeuvre to about 160-350 km, imaging flash sites at 1 m pixel scale or better (TriScape200-class camera) and comparing against archived before-images.
Baseline platform: single micro/mini-class spacecraft, about 120 kg dry (141.7 kg with ESA 20 % system margin), about 230 kg launch mass, under 100 W peak, delta-v 1400-1600 m/s (biprop about 300 s Isp or hydrazine about 220 s), reaction wheels plus star trackers, X-band TT&C (Ka-band optional), rideshare launch to a trans-lunar injection.
Key technical challenge: event cameras report relative log-intensity changes, not absolute radiance, so calibrated flash energy needs a separate calibration path. Flash localisation (at most 1.3 km, 95 %) drives attitude-knowledge requirements.
Added value claimed vs. state of the art: whole-Moon coverage (ground networks such as NASA MEO and NELIOTA see only the near side; ESA's LUMIO at Earth-Moon L2 sees only the far side at about 6 km GSD), and locating flashes precisely enough to match craters.
The authoritative source for requirements is the SRR PDF. Do not change requirement values in other documents without tracing them back to it.

Repository layout
00_OrganizationalMatters/
  LETO_ProjectDescription/       Course concept proposal ("Lunar Impact Flash Monitoring with Event Camera")
  LETO_SystemRequirementsReport/ LETO__SRR.pdf: mission statement, stakeholders, objectives,
                                 mission and system requirements, concept baseline, mass and power budgets
01_ExternalResources/
  AA_Lectures/                   Course lectures (Mission Design Process, parts 1 and 2)
  AB_SupervisorSelectedResources/ Reference papers (LUMIO, NELIOTA, Suggs et al. impact flux,
                                 event-based vision survey)
02_SubSystems/                   One folder per subsystem; currently empty placeholders (.gitkeep)
  01_Payload  02_Thermal  03_Power  04_Propulsion  05_Structure  06_Adcs  07_Telecom
  08_OnBoardDataHandling  09_MissionAnalysis  10_LaunchAndDeployment
  11_GroundSegmentAndOperations  12_ConOps  13_CostAndSchedule
Conventions
Numbered prefixes order folders (00_, 01_, 02_, and AA_, AB_ inside resources). Keep this scheme when adding folders, and append rather than renumber.
Folder names use PascalCase with no spaces (e.g. OnBoardDataHandling). Files from external sources keep their original titles.
Subsystem work goes in its matching 02_SubSystems/NN_* folder. Remove the .gitkeep once a folder has real content.
Requirement IDs follow the SRR: STK-NNN (stakeholders, with letter suffixes for sub-stakeholders), MO-NNN (mission objectives), MSC-NNN (success criteria), MR-NNN (mission requirements), SYS-NNN (system requirements). New subsystem requirements should get their own prefix (for example PL-, TH-, PWR-, PROP-, STR-, ADCS-, COM-, OBDH-) and trace to a parent SYS- or MR- ID.
Verification methods use ECSS letters: A = analysis (incl. simulation), T = test, R = review of design, I = inspection. The SRR also uses S = simulation in the system-requirement table.
Unconfirmed values are tagged [TBR] (to be reviewed) or [TBD] (to be determined). Keep the tag on any value copied from the SRR until the team closes it.
Margins: follow ESA practice used in the SRR: maturity margins per equipment (20 % for new payload items, 10 % for bus items in the current budget), plus a 20 % system margin on dry mass and a 20 % margin on power.
Units: SI throughout. State the margin policy and the source (datasheet, analogy, SMAD scaling) for every budget line.
References: IEEE style with DOIs, as in the SRR.
Working with this repo as an agent
Many inputs are PDFs. Extract text with pdftotext -layout <file> - before reasoning about them. Do not commit extracted text unless asked.
Large binary deliverables (PDF reports, slides) are committed as final versions. Prefer committing editable sources (LaTeX, Markdown, spreadsheets, scripts) next to the exported PDF when they exist.
When adding analysis code, keep it inside the relevant subsystem folder, include a short README explaining inputs, outputs and how to run it, and pin any dependencies (e.g. requirements.txt).
Do not overwrite or reformat the reference papers and lectures in 01_ExternalResources/.
main holds the agreed baseline. Do work on a branch and open a pull request for team review.
The project is licensed under GPL-3.0 (see LICENSE); third-party papers and lecture slides in 01_ExternalResources/ remain under their own copyright.
Next milestones (Phase B)
The SRR lists these open items, which map to the subsystem folders:

Size the OBC, thermal control and structure (currently rough estimates only).
Close the event-camera head count, focal length and monitoring altitude trade (6-15 heads, 16-27 mm, 3000-7000 km).
Define the in-flight calibration approach for flash energy (MR-008).
Close the ADCS architecture for the localisation budget (MR-006, MR-007).
Choose biprop vs. hydrazine and confirm the delta-v and propellant budget.
Complete link budgets (X vs. Ka band) driven by crater-image volume in the imaging phase.
Build the mode diagram (SYS-005) and ConOps for both mission phases.
