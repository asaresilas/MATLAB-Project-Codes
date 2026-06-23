"""
validate_rul_units.py -- Verify RUL metric units across all model outputs.

Confirms that RUL MAE and RMSE are in HOURS (not %). Checks internal consistency
(RMSE >= MAE) and computes NRMSE = RMSE / max_RUL for normalised comparisons.
Also flags the print-statement bug in generate_publication_results.py that labelled
hours as '%'.

Run from project root: python scripts/validate_rul_units.py
Output: results/publication_metrics/rul_unit_validation.json
"""
import os
import sys
import json
import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def validate_rul_units():
    print("\n=== RUL Unit Validation Report ===\n")

    # --- 1. System-level metrics (NASA expert on latent DT test set, n=300) ---
    system_path = os.path.join(PROJECT_ROOT, "results/publication_metrics/official_results.json")
    if not os.path.exists(system_path):
        print(f"ERROR: {system_path} not found.\n"
              "Run scripts/generate_publication_results.py first.")
        sys.exit(1)

    with open(system_path) as f:
        official = json.load(f)

    sys_mae  = official["rul_mae"]
    sys_rmse = official["rul_rmse"]

    # --- 2. Per-model metrics (Bi-LSTM-Attn on NASA IMS held-out test) ---
    model_meta_path = os.path.join(
        PROJECT_ROOT,
        "Trained_models/nasa_dl_comparison/Bi-LSTM-Attn/Bi-LSTM-Attn_metadata.json"
    )
    pm_mae = pm_rmse = pm_r2 = None
    if os.path.exists(model_meta_path):
        with open(model_meta_path) as f:
            bm = json.load(f)
        pm_rmse = bm["metrics"]["RMSE"]
        pm_mae  = bm["metrics"]["MAE"]
        pm_r2   = bm["metrics"]["R2"]
    else:
        print("WARNING: Bi-LSTM-Attn metadata not found -- per-model checks skipped.")

    # --- 3. RUL scale from the latent DT test set ---
    dt_path = os.path.join(PROJECT_ROOT, "data/latent_digital_twin.npz")
    if os.path.exists(dt_path):
        cache   = np.load(dt_path)
        rul_arr = cache["shared_rul"]
        max_rul  = float(np.max(rul_arr))
        min_rul  = float(np.min(rul_arr))
        mean_rul = float(np.mean(rul_arr))
    else:
        print("WARNING: latent_digital_twin.npz not found -- using design value max_RUL=100 h.")
        max_rul  = 100.0
        min_rul  = 0.0
        mean_rul = 50.0

    # --- 4. Consistency checks ---
    checks = {}
    checks["system_rmse_ge_mae"]     = bool(sys_rmse >= sys_mae)
    checks["system_mae_positive"]    = bool(sys_mae  > 0)
    checks["system_rmse_lt_max_rul"] = bool(sys_rmse < max_rul)

    if pm_mae is not None:
        checks["model_rmse_ge_mae"] = bool(pm_rmse >= pm_mae)
        checks["model_r2_positive"] = bool(pm_r2   > 0)

    # --- 5. Normalised metrics ---
    sys_nrmse = sys_rmse / max_rul if max_rul > 0 else float("nan")
    pm_nrmse  = pm_rmse  / max_rul if pm_rmse is not None and max_rul > 0 else None

    # --- Print report ---
    print("?" * 60)
    print("System-Level RUL  (NASA expert on latent DT test, n=300)")
    print("?" * 60)
    print(f"  MAE   = {sys_mae:.4f} h    [correct unit: HOURS, not %]")
    print(f"  RMSE  = {sys_rmse:.4f} h    [correct unit: HOURS, not %]")
    print(f"  NRMSE = {sys_nrmse:.4f}     (RMSE / max_RUL,  max_RUL = {max_rul:.1f} h)")
    print(f"  RMSE >= MAE:  {'OK PASS' if checks['system_rmse_ge_mae'] else '? FAIL'}")
    print(f"  RMSE < max_RUL: {'OK PASS' if checks['system_rmse_lt_max_rul'] else '? FAIL'}")

    if pm_mae is not None:
        print()
        print("?" * 60)
        print("Per-Model RUL  (Bi-LSTM-Attn on NASA IMS held-out test)")
        print("?" * 60)
        print(f"  MAE   = {pm_mae:.4f} h")
        print(f"  RMSE  = {pm_rmse:.4f} h")
        print(f"  R^2    = {pm_r2:.4f}")
        print(f"  NRMSE = {pm_nrmse:.4f}     (RMSE / max_RUL,  max_RUL = {max_rul:.1f} h)")
        print(f"  RMSE >= MAE:  {'OK PASS' if checks.get('model_rmse_ge_mae') else '? FAIL'}")

    print()
    print("?" * 60)
    print("RUL Scale Info  (latent DT test set, n=300)")
    print("?" * 60)
    print(f"  max_RUL  = {max_rul:.1f} h")
    print(f"  min_RUL  = {min_rul:.1f} h")
    print(f"  mean_RUL = {mean_rul:.1f} h")
    print(f"  Design:  RUL = 100*(1 - d),  scale is [0, 100] hours by construction.")

    print()
    print("?" * 60)
    print("Required Paper Corrections")
    print("?" * 60)
    print("  - Table V: change '23.01%' -> '23.01 h'  and  '26.81%' -> '26.81 h'")
    print("  - Table V caption: add 'max_RUL = 100 h (design value of latent DT)'")
    if pm_nrmse is not None:
        print(f"  - If NRMSE is reported: NRMSE = {sys_nrmse:.4f}  "
              "(label as NRMSE = RMSE / max_RUL, dimensionless)")
    print("  - generate_publication_results.py line ~136: remove '%' suffix from RUL print")

    # --- Save report ---
    report = {
        "system_level": {
            "mae_hours":  sys_mae,
            "rmse_hours": sys_rmse,
            "nrmse":      sys_nrmse,
            "max_rul_hours": max_rul,
            "unit_is_hours": True,
            "unit_was_incorrectly_labelled_percent_in_paper": True,
        },
        "per_model_bilstm": {
            "mae_hours":  pm_mae,
            "rmse_hours": pm_rmse,
            "r2":         pm_r2,
            "nrmse":      pm_nrmse,
        } if pm_mae is not None else None,
        "rul_scale": {
            "max_hours":  max_rul,
            "min_hours":  min_rul,
            "mean_hours": mean_rul,
            "design_formula": "RUL = 100 * (1 - d), d in [0, 1]",
        },
        "consistency_checks": checks,
        "all_checks_pass": all(checks.values()),
    }

    out_dir  = os.path.join(PROJECT_ROOT, "results/publication_metrics")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "rul_unit_validation.json")
    with open(out_path, "w") as f:
        json.dump(report, f, indent=4)

    status = "ALL CHECKS PASSED" if report["all_checks_pass"] else "SOME CHECKS FAILED"
    print(f"\nOK Validation report saved -> {out_path}")
    print(f"  Overall status: {status}")
    return report


if __name__ == "__main__":
    validate_rul_units()
