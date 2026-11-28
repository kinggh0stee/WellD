# hardware/pcb/history — superseded documents

Everything in this folder describes earlier states of the design and is kept only as the decision record. **None of it is current.** The current design is described by the documents one level up, starting with [`../README.md`](../README.md).

| File | What it was |
|------|-------------|
| `design_history.md` | Design changes #1–#17 (2026-07-05 … 07-14), the datasheet-verification blocker list #1–#11 and the old "components still needing resolution" table, moved out of `schematic_connections.md` on 2026-11-28 |
| `senior_review_2026-05-25.md` | First senior hardware review (2S design) — BLOCKED on 4 CRITICAL items, all since fixed |
| `component_selection_review.md` | 2026-07-05 charger/regulator selection review (TP5100 → IP2326, CN3722, AP63203WU) |
| `senior_review_2026-07-06.md` | Second senior review (2S design) |
| `component_verification_2026-07-14.md` | Datasheet sweep of the 2S BOM (LCSC numbers, footprints, leakage of the old SMAJ3.3CA) |
| `alternatives_review_2026-07-15.md` | "Better options" review of every BOM position; its applied swaps (AO3400A, HRO USB-C, …) live on in the current BOM, and its 1S-vs-2S analysis preceded the 1S conversion |
| `kicad_guide_eli5_2026-07.md` | KiCad setup guide written when the sheets had symbols but no wiring; replaced by the layout procedure in `../README.md` |

The 2S → 1S conversion (2026-07-19) replaced the IP2326 USB boost charger with a TP4056, the CN3722 solar controller with a CN3791, the AP63203WU buck with an HT7333-A LDO and the XT30 pack connector with an on-board 18650 carrier plus DW01A/FS8205A protection. Part numbers, voltages (8.4 V pack, 12 V panels, 12 V VLOOP) and LCSC numbers in these files refer to that older design.
