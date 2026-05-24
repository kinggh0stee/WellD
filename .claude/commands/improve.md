---
description: Full improvement cycle for WellD. Runs all agents in the correct order based on what changed.
---

You are orchestrating a full WellD improvement cycle. Follow this exact sequence:

## Step 1 — Understand the change scope
Ask the user: "What are you changing — hardware, firmware, or both?"

Then based on the answer, follow the appropriate track below.

---

## Track A: Hardware change (PCB or case)

### Phase 1 — PCB (sequential, must finish first)
Delegate to pcb-engineer:
- Review and implement the requested PCB changes in hardware/pcb/
- Output: updated GPIO map, board dimensions, BOM diff, any constraints for downstream agents

### Phase 2 — Parallel (wait for Phase 1)
Spawn these three agents simultaneously:
- firmware-engineer: update pin assignments and any driver changes based on PCB agent output
- case-engineer: verify board fit, update enclosure if dimensions changed
- z2m-converter: update converter if new sensors or payload fields were added

### Phase 3 — Sequential (wait for Phase 2)
- test-engineer: run all tests, fix regressions, report results
- docs-writer: update README tables (GPIO map, BOM, config options, MQTT payload)
- ci-engineer: check if any new CI steps are needed for the changes

---

## Track B: Firmware-only change

### Phase 1
Delegate to firmware-engineer:
- Implement the requested firmware changes
- Output: summary of what changed, any new config options, any payload changes

### Phase 2 — Parallel (wait for Phase 1)
Spawn simultaneously:
- test-engineer: run host tests and Z2M tests, fix regressions
- z2m-converter: update converter if payload fields changed

### Phase 3
- docs-writer: update README config table, payload example, HA entity table
- ci-engineer: flag if new CI steps needed

---

## Track C: Both hardware and firmware

Run Track A in full. Firmware changes are handled in Phase 2 of Track A.

---

## Final Phase — Senior review (all tracks)

After all other phases complete, always spawn `senior-reviewer` as the last step:
- It diffs `main...HEAD` scoped to `hardware/pcb/`, `main/`, and `components/`
- If none of those paths changed in this cycle, it self-skips and the cycle completes normally
- If **CRITICAL** issues are found, **stop immediately** — surface the full report to the user and do not mark the cycle complete
- Include the full review report in the end-of-cycle summary regardless of verdict

---

## Rules for all tracks
- Never run pcb-engineer and case-engineer on the same files simultaneously
- Always run test-engineer before docs-writer — docs should reflect passing state only
- Always run senior-reviewer last — after test-engineer and docs-writer, before declaring the cycle complete
- If any agent reports a failure, stop and surface it to the user before continuing
- If senior-reviewer returns BLOCKED, do not complete the cycle — report the CRITICAL findings to the user
- At the end, summarize: what changed, what tests passed, what docs were updated, senior-reviewer verdict, any open issues flagged
