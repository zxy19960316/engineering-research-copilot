# Project Status

## Active milestone

`M1 — Two-round paper calibration and evidence map`

Status: `IN_PROGRESS`

## M1 checklist

- [x] M0 baseline confirmed clean at root commit `5a5bcba`.
- [x] M1 implementation plan created outside the installable Skill.
- [x] Local work branch created: `codex/m1-paper-calibration`.
- [ ] Adaptive research brief and query-plan contract implemented.
- [ ] Verified 15–20-paper candidate-pool workflow implemented.
- [ ] Eight-paper round-one evidence map and equivalent text fallback implemented.
- [ ] Visible feedback delta and changed second-round search plan implemented.
- [ ] Five-to-six-paper round-two output and disposition log implemented.
- [ ] Offline validator and adversarial fixtures pass.
- [ ] Fresh-context real-search forward tests pass with current authoritative citation checks.
- [ ] Standard Skill validation and final M1 scope audit pass.

## M0 checklist

- [x] D-drive project root created.
- [x] Local Git repository initialized on `main`.
- [x] Standard Skill scaffold generated.
- [x] Repository governance and product specification reviewed.
- [x] Thin root router and four core protocol references completed.
- [x] Standard Skill validation passed in UTF-8 mode: `Skill is valid!`.
- [x] Root references, placeholder count, and Skill length checks passed.
- [x] Initialization baseline prepared for one local root commit.

## Later milestones

- M2: `NOT_STARTED`
- M3: `NOT_STARTED`
- M4: `NOT_STARTED`
- M5: `NOT_STARTED`

## External state

- Git remote: `https://github.com/zxy19960316/engineering-research-copilot.git`
- Active local branch: `codex/m1-paper-calibration`
- External APIs/services configured: none
- RRC integration: not started
- Platform integration: not required for the local Skill competition track

## M0 result

Status: `COMPLETE`

Validated with:

```powershell
python -X utf8 C:\Users\94310\.codex\skills\.system\skill-creator\scripts\quick_validate.py D:\engineering-research-copilot\skills\engineering-research-copilot
```

The first validator attempt without UTF-8 mode did not reach Skill validation because the Windows GBK default could not decode Chinese trigger text. No Skill content was weakened; the same validator passed under Python UTF-8 mode.
