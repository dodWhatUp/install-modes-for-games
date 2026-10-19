# P0 implementation and current conclusions

This source preview implements the shared read-only core and human views for MCI-01 through MCI-05. It reuses existing source, archive, journal, approval and UI owners. Codex and the installed toolkit were not reinstalled or configured.

| Stage | Deliverable | Current acceptance boundary |
|---|---|---|
| [MCI-01](MCI-01-CONCLUSIONS.md) | Exact-source reuse inventory and capability/unknown matrix | Inventory complete for selected sources; other device unknown |
| [MCI-02](MCI-02-CONCLUSIONS.md) | Versioned context/handoff contracts and bounded source checks | Read-only contract core; future operational services remain separate |
| [MCI-03](MCI-03-CONCLUSIONS.md) | Human source/instruction explorer and dependency graph/list | Source/Tk preview implemented; native accessibility and Windows GUI pending |
| [MCI-04](MCI-04-CONCLUSIONS.md) | Static request checks and conservative optional reduction | Source/Tk preview implemented; human usability acceptance pending |
| [MCI-05](MCI-05-CONCLUSIONS.md) | Device/event/activity overview and selected details | Authored fixtures and existing-journal adapter; real transport/chat adapters pending |

Use [the source preview](../../scripts/GameToolSystemControl.pyw), [usage](../../examples/system-control/README.md) and [validation record](P0-VALIDATION.json). Each stage conclusion explains the decision, evidence and next boundary. The [all-stage status file](STAGE-STATUS.json) records all 18 work packages without claiming unstarted work. Task tracking distinguishes completed inventory/contracts from partial broad product acceptance; a source preview does not complete native history transfer, remote operation or all 36 GT requirements.

Execution order was MCI-01 → MCI-02 → MCI-03's source model → MCI-04 → MCI-05. The pending native-accessibility gate does not invalidate the tested source model consumed by preflight. Independent next source work is MCI-07 vault, MCI-12 policy and MCI-13 enrollment, following the full dependency map. Future source migration, transport enrollment, remote effects and actual-device acceptance need their declared gates. No automatic background continuation or schedule is installed.

Known limits: scope/routing estimates are static and incomplete; only explicitly selected sources are read. The source viewer cannot inspect inaccessible platform instructions or memory. Loaded-state assertions are contextual reports. Device freshness is last-reported, never proof of a live connection. No-store means this view persists nothing; it does not delete upstream originals. Detail reads currently support selected UTF-8 references, not arbitrary binary native-chat attachments. Tk keyboard behavior passed guest tests; the lab AT-SPI adapter did not expose its semantic tree.

Recovery: close the preview; its session state is discarded. Original sources and journals are unchanged. Revert the additive source change through Git if necessary; never replace Codex home or native databases to roll back this view.
