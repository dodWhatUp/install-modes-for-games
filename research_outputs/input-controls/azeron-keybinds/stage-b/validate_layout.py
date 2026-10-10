#!/usr/bin/env python3
"""Static access audit. No input injection, device access, network, or telemetry.
Usage: python3 validate_layout.py [folder_containing_json]
The model assumes one independent concurrent output per hypothesized finger.
A conflict is not proof a person cannot press two real switches with one finger.
"""
import itertools
import json
import re
import sys
from collections import Counter
from pathlib import Path

LAYERS = ("BASIC", "NUMBERS", "LETTERS", "TOOLS")

def load(path):
    return json.loads(path.read_text(encoding="utf-8"))

def group(position):
    match = re.fullmatch(r"R([1-5])C([1-4])", position)
    if match:
        return ("little", "ring", "middle", "index")[int(match[2])-1]
    if position == "L3":
        return "little"
    if position == "R3":
        return "index"
    if position.startswith(("TH_", "ST_")):
        return "thumb"
    raise ValueError("Unknown visual position: " + position)

def candidates(bank, keys):
    return [[p for p, v in bank.items() if v == k] for k in keys]

def route_for(bank, layer, keys, movement):
    options = candidates(bank, keys)
    if not all(options):
        return None
    busy = ([] if layer == "BASIC" else ["little"]) + (["thumb"] if movement else [])
    for route in itertools.product(*options):
        groups = [group(p) for p in route]
        together = busy + groups
        if len(set(route)) == len(route) and len(set(together)) == len(together):
            return [{"key": k, "position": p, "finger_hypothesis": group(p)}
                    for k, p in zip(keys, route)]
    return None

def audit_case(maps, c):
    bank = maps[c["bank"]]
    missing = [k for k in c["keys"] if k not in bank.values()]
    base = {"case_id": c["id"], "bank": c["bank"], "keys": c["keys"],
            "movement_required": c["movement_required"],
            "requirement_origin": c["requirement_origin"],
            "source_id": c["source_id"], "runtime_verified": False}
    if missing:
        return dict(base, status="NOT_IN_BANK", reason="Missing: " + ", ".join(missing), route=None)
    route = route_for(bank, c["bank"], c["keys"], c["movement_required"])
    if route is not None:
        return dict(base, status="MODEL_ROUTE",
                    reason="Different hypothesized fingers; physical reach and runtime remain unverified.",
                    route=route)
    without_move = route_for(bank, c["bank"], c["keys"], False)
    reason = ("THUMB_MOVEMENT_CONFLICT" if c["movement_required"] and without_move is not None
              else "SAME_FINGER_OR_SELECTOR_CONFLICT")
    return dict(base, status="MODEL_CONFLICT", reason=reason, route=None)

def structural_checks(doc):
    maps = doc["maps"]
    expected = {f"R{r}C{c}" for r in range(1, 6) for c in range(1, 5)}
    expected.update(["L3", "R3", "TH_U", "TH_L", "TH_C", "TH_R", "TH_D", "ST_RU", "ST_RD", "ST_D"])
    assert set(maps) == set(LAYERS)
    for layer, bank in maps.items():
        assert set(bank) == expected, layer
        assert all(isinstance(k, str) for k in bank.values())
        for p, key in bank.items():
            if key.startswith("LAYER:"):
                assert key[6:] in maps, (layer, p, key)
        for p, key in doc["common_positions"].items():
            assert bank[p] == key, (layer, p)
        if layer != "BASIC":
            assert all(bank[p] == "UNASSIGNED" for p in doc["intentionally_empty_secondary_positions"])
    outputs = {"W", "A", "S", "D"}
    for bank in maps.values():
        outputs.update(v for v in bank.values() if v != "UNASSIGNED" and not v.startswith("LAYER:"))
    assert outputs == set(doc["target_keys"]), (outputs - set(doc["target_keys"]), set(doc["target_keys"]) - outputs)
    for digit in "123456789":
        np = next(p for p, v in maps["NUMBERS"].items() if v == digit)
        assert maps["TOOLS"][np] == "F" + digit
    return {"layout_cells_checked": 120, "unique_target_outputs_including_WASD": len(outputs),
            "same_position_common_outputs": {k: v for k, v in doc["common_positions"].items() if not v.startswith("LAYER:")},
            "selector_locations_checked": 12, "aligned_number_function_positions": 9,
            "intentionally_unassigned_secondary_cells": 9,
            "runtime_verified": False}

def main(directory):
    doc = load(directory / "layout_candidate.json")
    baseline_path = directory / "baseline_r2_for_comparison.json"
    if not baseline_path.exists():
        baseline_path = directory.parent / "extensions/2026-10-10-r2/STAGE_B_DRAFT_R2.json"
    baseline = load(baseline_path)
    cases = load(directory / "cases.json")["cases"]
    assert len({c["id"] for c in cases}) == len(cases)
    structure = structural_checks(doc)
    old = {c["id"]: audit_case(baseline["maps"], c) for c in cases}
    new = {c["id"]: audit_case(doc["maps"], c) for c in cases}
    comparisons = [{"case_id": c["id"], "r2": old[c["id"]]["status"], "r3": new[c["id"]]["status"],
                    "r2_reason": old[c["id"]]["reason"], "r3_reason": new[c["id"]]["reason"]}
                   for c in cases if old[c["id"]]["status"] != new[c["id"]]["status"]]
    improvements = [x for x in comparisons if x["r3"] == "MODEL_ROUTE"]
    regressions = [x for x in comparisons if x["r2"] == "MODEL_ROUTE" and x["r3"] != "MODEL_ROUTE"]
    changes = [{"bank": l, "position": p, "before": baseline["maps"][l][p], "after": doc["maps"][l][p]}
               for l in LAYERS for p in doc["maps"][l] if baseline["maps"][l][p] != doc["maps"][l][p]]
    report = {"schema_version": "1.0", "status": "STATIC_AUDIT_ONLY", "structural_checks": structure,
              "case_count": len(cases), "r2_status_counts": dict(Counter(x["status"] for x in old.values())),
              "r3_status_counts": dict(Counter(x["status"] for x in new.values())),
              "new_model_routes": improvements, "lost_model_routes": regressions,
              "per_case": [{"id": c["id"], "r2": old[c["id"]], "r3": new[c["id"]]} for c in cases],
              "mapping_changes": changes,
              "not_claimed": ["Physical ergonomics measured", "Native Software v2 configuration verified",
                              "Gameplay verified", "Latency measured", "Game coverage percentage",
                              "Globally optimal layout", "Raw source defaults re-verified for all 94 records"]}
    (directory / "validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ["status", "case_count", "r2_status_counts", "r3_status_counts"]}))
    print("New model routes:", len(improvements), "Lost model routes:", len(regressions))
    return report

if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent)
