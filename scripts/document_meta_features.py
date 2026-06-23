"""
document_meta_features.py -- Prints the exact 32-dim meta-feature breakdown for Eq. (5).

Reviewer ?III.C comment:
  "Eq. (5) defines a 32-D vector but the count does not add up:
   5 probability vectors x 3 entries = 15, plus 5 entropies + 5 margins = 25;
   the remaining 7 dimensions of sigma are unspecified."

The reviewer's count is partially wrong -- they counted correctly to 25 but missed
the 7 global statistics that are appended by extract_meta_features_from_predictions().
This script documents the EXACT breakdown and generates the corrected equation text
for the paper.

Run from project root: python scripts/document_meta_features.py
Output: results/publication_metrics/meta_feature_documentation.json
"""
import os
import sys
import json
import numpy as np
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.features.meta_fusion_features import (
    get_rich_features,
    extract_meta_features_from_predictions,
)


def build_feature_manifest():
    """Build the ordered feature manifest with names, indices, and descriptions."""
    manifest = []
    idx = 0

    experts = ["CWRU", "Induction", "NASA", "Current", "Thermal"]
    for exp in experts:
        # Per-expert block: [p0, p1, p2, entropy, margin] = 5 dims
        manifest.append({
            "index": idx,     "name": f"{exp}_p_Normal",    "group": f"{exp}_probs",
            "description": f"P({exp} -> Normal/Healthy)", "source": "softmax output"})
        manifest.append({
            "index": idx+1,   "name": f"{exp}_p_Warning",   "group": f"{exp}_probs",
            "description": f"P({exp} -> Warning/Intermediate)", "source": "softmax output"})
        manifest.append({
            "index": idx+2,   "name": f"{exp}_p_Critical",  "group": f"{exp}_probs",
            "description": f"P({exp} -> Critical/Severe)", "source": "softmax output"})
        manifest.append({
            "index": idx+3,   "name": f"{exp}_entropy",     "group": f"{exp}_uncertainty",
            "description": f"Shannon entropy H(p) = -Sigma p_i ln(p_i) for {exp}", "source": "get_rich_features"})
        manifest.append({
            "index": idx+4,   "name": f"{exp}_margin",      "group": f"{exp}_uncertainty",
            "description": f"Decision margin = max_prob - 2nd_max_prob for {exp}", "source": "get_rich_features"})
        idx += 5   # 5 dims per expert x 5 experts = 25

    # Global statistics appended by extract_meta_features_from_predictions
    for cls in ["Normal", "Warning", "Critical"]:
        manifest.append({
            "index": idx,   "name": f"global_mean_p_{cls}", "group": "global_stats",
            "description": f"Mean of P->{cls} across all 5 experts", "source": "np.mean"})
        idx += 1   # 3 dims for mean_p

    for cls in ["Normal", "Warning", "Critical"]:
        manifest.append({
            "index": idx,   "name": f"global_var_p_{cls}", "group": "global_stats",
            "description": f"Variance of P->{cls} across all 5 experts (expert disagreement)", "source": "np.var"})
        idx += 1   # 3 dims for var_p

    manifest.append({
        "index": idx,   "name": "global_entropy",   "group": "global_stats",
        "description": "Shannon entropy of the mean probability vector across all experts",
        "source": "extract_meta_features_from_predictions"})
    idx += 1   # 1 dim for global_ent

    return manifest, idx


def verify_with_dummy_data(manifest, total_dims):
    """Verify the manifest against actual extract_meta_features_from_predictions output."""
    np.random.seed(42)
    dummy_preds = {
        exp: np.random.dirichlet([1, 1, 1], size=10).astype(np.float32)
        for exp in ["CWRU", "Induction", "NASA", "Current", "Thermal"]
    }
    x_meta = extract_meta_features_from_predictions(dummy_preds)
    actual_dims = x_meta.shape[1]
    match = (actual_dims == total_dims)
    return actual_dims, match, x_meta


def run_documentation():
    print("\n=== Meta-Feature Dimensionality Documentation ===\n")

    manifest, total_dims = build_feature_manifest()
    actual_dims, dims_match, sample = verify_with_dummy_data(manifest, total_dims)

    # Print breakdown table
    print(f"{'Idx':>4}  {'Feature Name':<30}  {'Group':<22}  Description")
    print("-" * 110)
    current_group = None
    for entry in manifest:
        if entry["group"] != current_group:
            if current_group is not None:
                print()
            current_group = entry["group"]
        print(f"{entry['index']:>4}  {entry['name']:<30}  {entry['group']:<22}  {entry['description']}")

    print(f"\n{'?'*60}")
    print(f"  Declared total:  {total_dims} dimensions")
    print(f"  Actual output:   {actual_dims} dimensions")
    print(f"  Match:           {'OK VERIFIED' if dims_match else '? MISMATCH'}")

    # Corrected equation text for the paper
    eq_text = (
        "The meta-feature vector phi in ?^32 is constructed as:\n\n"
        "  phi = [phi_CWRU, phi_Ind, phi_NASA, phi_Curr, phi_Therm, mu_p, sigma^2_p, H_g]\n\n"
        "where for each expert e in {CWRU, Induction, NASA, Current, Thermal}:\n"
        "  phi_e = [p_e^(0), p_e^(1), p_e^(2), H(p_e), m_e]  in ?^5\n"
        "  p_e^(k): softmax probability for class k in {Normal, Warning, Critical}\n"
        "  H(p_e) = -Sigma_k p_e^(k) ln(p_e^(k)):  Shannon entropy (uncertainty)\n"
        "  m_e = p_e^(argmax) - p_e^(2nd argmax):  decision margin\n\n"
        "Global statistics (7 additional dimensions):\n"
        "  mu_p = (1/5) Sigma_e p_e  in ?^3:  mean class probability across experts\n"
        "  sigma^2_p = Var_e(p_e)    in ?^3:  expert disagreement per class\n"
        "  H_g = H(mu_p)         in ?^1:  global entropy of the consensus distribution\n\n"
        "Dimension count: 5 experts x 5 = 25, plus 3 + 3 + 1 = 7 global = 32 total. OK"
    )
    print(f"\n{'?'*60}")
    print("  Corrected Eq. (5) text for the paper:")
    print(f"{'?'*60}")
    print(eq_text)

    # Reviewer clarification
    reviewer_response = (
        "Reviewer ?III.C notes: 'the remaining 7 dimensions of sigma are unspecified.' "
        "These 7 dimensions ARE specified in the code (src/features/meta_fusion_features.py, "
        "extract_meta_features_from_predictions()): "
        "mean_p (3 dims, mu_p), var_p (3 dims, sigma^2_p), global_ent (1 dim, H_g). "
        "The paper's Eq. (5) needs to be expanded to show all three components. "
        "The reviewer's count of 25 is correct for the expert blocks; the remaining "
        "7 are the global cross-expert statistics appended in the same function."
    )

    out_path = os.path.join(PROJECT_ROOT, "results/publication_metrics/meta_feature_documentation.json")
    output   = {
        "timestamp":     datetime.now().isoformat(),
        "total_dims":    total_dims,
        "actual_dims_verified": actual_dims,
        "dims_match":    dims_match,
        "feature_manifest": manifest,
        "corrected_equation_text": eq_text,
        "reviewer_response": reviewer_response,
        "breakdown_summary": {
            "per_expert_dims":    5,
            "n_experts":          5,
            "expert_block_total": 25,
            "global_mean_p":      3,
            "global_var_p":       3,
            "global_entropy":     1,
            "grand_total":        32,
        },
    }
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(output, f, indent=4)

    print(f"\nOK Feature documentation saved -> {out_path}")
    return output


if __name__ == "__main__":
    run_documentation()
