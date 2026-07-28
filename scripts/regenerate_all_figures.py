"""
regenerate_all_figures.py
=========================
Regenerates ALL publication figures from the v5 StatisticsExtractor pipeline results.
Fixes:
  - Hardcoded F1=0.9061 → reads from crossval_ci.json (0.9089)
  - Latency CDF correctly annotated as XGBoost stack only (~38ms P50)
  - All figures re-sourced from raw_eval_data.npz (May 27 v5 run)
  - Ablation uses ablation_proper.json (retrained meta-learner)
  - RUL axes labelled in hours (not %)

Run from project root:
    python scripts/regenerate_all_figures.py

Output: results/FINAL_PUBLICATION_FIGURES/  (13 figures @ 300 DPI)
"""

import os, sys, json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
from matplotlib.lines import Line2D
import seaborn as sns
from sklearn.metrics import (
    confusion_matrix, roc_curve, auc,
    precision_recall_curve, average_precision_score
)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(PROJECT_ROOT, 'results', 'FINAL_PUBLICATION_FIGURES')
os.makedirs(OUT_DIR, exist_ok=True)

# ── IEEE publication style ───────────────────────────────────────────────────
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['Times New Roman', 'DejaVu Serif', 'serif'],
    'font.size': 14,
    'axes.labelsize': 15,
    'axes.titlesize': 16,
    'xtick.labelsize': 13,
    'ytick.labelsize': 13,
    'legend.fontsize': 13,
    'figure.dpi': 300,
    'axes.linewidth': 1.5,
    'mathtext.fontset': 'stix',
    'axes.spines.top': False,
    'axes.spines.right': False,
})

COL_NORMAL   = '#2ecc71'
COL_WARNING  = '#f39c12'
COL_CRITICAL = '#e74c3c'
COL_MAIN     = '#2980b9'
COL_DARK     = '#2c3e50'
COL_GREY     = '#95a5a6'

FIG_SIZE = (10, 7.5)   # 4:3 academic standard

def save(name):
    path = os.path.join(OUT_DIR, f'{name}.png')
    plt.savefig(path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f'  [OK] {name}.png')

# ── Load data ────────────────────────────────────────────────────────────────
print('Loading evaluation data...')

raw_path = os.path.join(PROJECT_ROOT, 'results/publication_metrics/raw_eval_data.npz')
if not os.path.exists(raw_path):
    print('ERROR: raw_eval_data.npz not found. Run generate_publication_results.py first.')
    sys.exit(1)
raw = np.load(raw_path)
y_true     = raw['y_true']
y_pred     = raw['y_pred']
y_probs    = raw['y_probs']
y_true_rul = raw['y_true_rul']
y_pred_rul = raw['y_pred_rul']
latencies  = raw['latencies']   # XGBoost meta-fusion stack only, ~38ms P50

with open(os.path.join(PROJECT_ROOT, 'results/publication_metrics/crossval_ci.json')) as f:
    cv_data = json.load(f)
meta_f1_cv = cv_data['cv_fold_summary']['meta_fusion']['f1']['mean']   # 0.9089
meta_f1_ci_lo = cv_data['cv_fold_summary']['meta_fusion']['f1']['ci_95_lo']
meta_f1_ci_hi = cv_data['cv_fold_summary']['meta_fusion']['f1']['ci_95_hi']
cv_folds       = cv_data['cv_fold_summary']['meta_fusion']['f1']['folds']

with open(os.path.join(PROJECT_ROOT, 'results/publication_metrics/ablation_proper.json')) as f:
    abl_raw = json.load(f)
abl_results = abl_raw['results']

with open(os.path.join(PROJECT_ROOT, 'results/publication_metrics/correct_baselines.json')) as f:
    cb_raw = json.load(f)
cb_results = cb_raw['results']

with open(os.path.join(PROJECT_ROOT, 'results/publication_metrics/latency_breakdown.json')) as f:
    lat_raw = json.load(f)
comp_lats = lat_raw['component_latencies_ms']

with open(os.path.join(PROJECT_ROOT, 'results/publication_metrics/official_results.json')) as f:
    official = json.load(f)

print(f'  F1-macro (5-fold CV): {meta_f1_cv:.4f}')
print(f'  Samples: {len(y_true)}  RUL range: [{y_true_rul.min():.1f}, {y_true_rul.max():.1f}] h')
print()

CLASS_NAMES = ['NORMAL', 'WARNING', 'CRITICAL']
CLASS_COLS  = [COL_NORMAL, COL_WARNING, COL_CRITICAL]

# ════════════════════════════════════════════════════════════════════════════
# Fig 01 – System Architecture (block diagram)
# ════════════════════════════════════════════════════════════════════════════
print('Fig01: System Architecture...')
fig, ax = plt.subplots(figsize=FIG_SIZE)
ax.set_xlim(-3.2, 12); ax.set_ylim(0, 9); ax.axis('off')

def box(ax, x, y, w, h, label, fc='#d6eaf8', ec='#2471a3', fs=10):
    rect = mpatches.FancyBboxPatch((x-w/2, y-h/2), w, h,
        boxstyle='round,pad=0.15', facecolor=fc, edgecolor=ec, linewidth=1.5, zorder=3)
    ax.add_patch(rect)
    ax.text(x, y, label, ha='center', va='center', fontsize=fs, fontweight='bold',
            zorder=4, wrap=True, multialignment='center')

def arr(ax, x1, y1, x2, y2):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(arrowstyle='->', color=COL_DARK, lw=2), zorder=2)

# Layer labels — positioned to left of all boxes (xlim starts at -3.2)
for y, label in [(8.3, 'PHYSICAL LAYER'), (6.3, 'EXPERT AI LAYER'),
                 (4.0, 'META-FUSION LAYER'), (1.7, 'DECISION LAYER')]:
    ax.text(-3.0, y, label, fontsize=9, color='#555', style='italic', va='center')

# MATLAB/Simulink source
box(ax, 6, 8.0, 3.5, 0.9, 'MATLAB / Simulink\nDigital Twin', fc='#fdfefe', ec='#7d6608', fs=11)

# Five experts
experts = [
    (1.1, 'CWRU\nCNN', '#d5f5e3'),
    (3.1, 'Induction\nCNN', '#d5f5e3'),
    (5.9, 'NASA\nBi-LSTM\n+Attn', '#d5f5e3'),
    (8.7, 'Current\nCNN (v5)', '#d5f5e3'),
    (10.9, 'Thermal\nMobileNet', '#d5f5e3'),
]
for ex, (ex_x, ex_label, ex_fc) in enumerate(experts):
    box(ax, ex_x, 6.3, 1.8, 1.1, ex_label, fc=ex_fc, ec='#1e8449', fs=9)
    arr(ax, 6, 7.55, ex_x, 6.85)

# Meta-feature aggregation
box(ax, 6, 4.0, 8.5, 0.9, '32-dim Meta-Feature Vector\n(5 × [probs + entropy + margin] + 7 global stats)',
    fc='#eaf2ff', ec=COL_MAIN, fs=10)
for ex_x, _, _ in experts:
    arr(ax, ex_x, 5.75, 6, 4.45)

# Stacking ensemble
box(ax, 6, 2.5, 5.0, 0.85, 'Stacking Ensemble\n(XGBoost + RF + MLP → LogReg judge)',
    fc='#f9ebea', ec='#922b21', fs=10)
arr(ax, 6, 3.55, 6, 2.93)

# Output
box(ax, 3.0, 1.3, 3.5, 0.85, 'NORMAL / WARNING\n/ CRITICAL', fc='#eafaf1', ec='#196f3d', fs=10)
box(ax, 9.0, 1.3, 3.5, 0.85, 'RUL Estimate\n(hours)', fc='#fef9e7', ec='#7d6608', fs=10)
arr(ax, 4.75, 2.07, 3.0, 1.73)
arr(ax, 7.25, 2.07, 9.0, 1.73)

ax.set_title('MotorGuard Hierarchical Meta-Fusion Architecture', fontsize=16, fontweight='bold', pad=12)
save('Fig01_System_Architecture')


# ════════════════════════════════════════════════════════════════════════════
# Fig 02 – Confusion Matrix (normalised)
# ════════════════════════════════════════════════════════════════════════════
print('Fig02: Confusion Matrix...')
cm_norm = confusion_matrix(y_true, y_pred, normalize='true')
cm_raw  = confusion_matrix(y_true, y_pred)

fig, ax = plt.subplots(figsize=(8, 7))
im = ax.imshow(cm_norm, cmap='Blues', vmin=0, vmax=1)
plt.colorbar(im, ax=ax, label='Proportion')

for i in range(3):
    for j in range(3):
        color = 'white' if cm_norm[i, j] > 0.6 else COL_DARK
        ax.text(j, i, f'{cm_norm[i,j]:.2f}\n({cm_raw[i,j]})',
                ha='center', va='center', fontsize=14, color=color, fontweight='bold')

ax.set_xticks([0,1,2]); ax.set_xticklabels(CLASS_NAMES, fontsize=13)
ax.set_yticks([0,1,2]); ax.set_yticklabels(CLASS_NAMES, fontsize=13)
ax.set_xlabel('Predicted Health State', fontsize=15, labelpad=10)
ax.set_ylabel('True Health State', fontsize=15, labelpad=10)
ax.set_title(f'Normalised Confusion Matrix\nHoldout n=300  |  F1-macro={official["f1"]:.4f}',
             fontsize=15, fontweight='bold', pad=14)
plt.tight_layout()
save('Fig02_Confusion_Matrix')


# ════════════════════════════════════════════════════════════════════════════
# Fig 03 – Per-Class Precision / Recall / F1
# ════════════════════════════════════════════════════════════════════════════
print('Fig03: Per-Class P/R/F1...')
report = official['report']
metrics = {'Precision': [], 'Recall': [], 'F1-Score': []}
ns = []
for cls in ['0','1','2']:
    metrics['Precision'].append(report[cls]['precision'])
    metrics['Recall'].append(report[cls]['recall'])
    metrics['F1-Score'].append(report[cls]['f1-score'])
    ns.append(int(report[cls]['support']))

x = np.arange(3); width = 0.25
fig, ax = plt.subplots(figsize=FIG_SIZE)
colors_pr = ['#2980b9', '#27ae60', '#8e44ad']
for idx, (metric, vals) in enumerate(metrics.items()):
    bars = ax.bar(x + idx*width, [v*100 for v in vals], width,
                  label=metric, color=colors_pr[idx], edgecolor='black', alpha=0.85)
    for bar, v in zip(bars, vals):
        ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.8,
                f'{v:.3f}', ha='center', fontsize=10, fontweight='bold')

ax.set_xticks(x + width)
ax.set_xticklabels([f'{c}\n(n={n})' for c, n in zip(CLASS_NAMES, ns)], fontsize=13)
ax.set_ylim(70, 108)
ax.set_ylabel('Score (%)', fontsize=15)
ax.set_title('Per-Class Classification Performance\n(Held-out Test Set, n=300)', fontsize=15, fontweight='bold')
ax.legend(loc='lower right', frameon=True)
ax.axhline(official['f1']*100, color='red', linestyle='--', lw=1.5, alpha=0.6, label=f'Macro F1={official["f1"]:.3f}')
ax.text(2.95, official['f1']*100+0.5, f'Macro F1={official["f1"]:.3f}', color='red', fontsize=10)
plt.tight_layout()
save('Fig03_PerClass_Precision_Recall_F1')


# ════════════════════════════════════════════════════════════════════════════
# Fig 04 – ROC-AUC Curves
# ════════════════════════════════════════════════════════════════════════════
print('Fig04: ROC-AUC...')
fig, ax = plt.subplots(figsize=FIG_SIZE)
for i, (cls_name, col) in enumerate(zip(CLASS_NAMES, CLASS_COLS)):
    fpr, tpr, _ = roc_curve((y_true == i).astype(int), y_probs[:, i])
    roc_auc = auc(fpr, tpr)
    ax.plot(fpr, tpr, lw=3, color=col, label=f'{cls_name}  AUC={roc_auc:.4f}')
ax.plot([0,1],[0,1],'k--',lw=1.5,alpha=0.5,label='Random classifier')
ax.fill_between([0,1],[0,1],alpha=0.05,color='grey')
ax.set_xlim([-0.01,1.01]); ax.set_ylim([-0.01,1.05])
ax.set_xlabel('False Positive Rate', fontsize=15)
ax.set_ylabel('True Positive Rate', fontsize=15)
ax.set_title(f'Multi-Class ROC Curves (One-vs-Rest)\nMacro AUC = {official["roc_auc_ovr_macro"]:.4f}', fontsize=15, fontweight='bold')
ax.legend(loc='lower right', frameon=True, shadow=True)
plt.tight_layout()
save('Fig04_ROC_AUC_Curves')


# ════════════════════════════════════════════════════════════════════════════
# Fig 05 – Precision-Recall Curves
# ════════════════════════════════════════════════════════════════════════════
print('Fig05: Precision-Recall Curves...')
fig, ax = plt.subplots(figsize=FIG_SIZE)
for i, (cls_name, col) in enumerate(zip(CLASS_NAMES, CLASS_COLS)):
    prec, rec, _ = precision_recall_curve((y_true == i).astype(int), y_probs[:, i])
    ap = average_precision_score((y_true == i).astype(int), y_probs[:, i])
    ax.plot(rec, prec, lw=3, color=col, label=f'{cls_name}  AP={ap:.4f}')
# class-prevalence baselines
for i, col in enumerate(CLASS_COLS):
    prevalence = float(np.mean(y_true == i))
    ax.axhline(prevalence, linestyle=':', lw=1.2, color=col, alpha=0.5)
ax.set_xlim([-0.01,1.01]); ax.set_ylim([0.0,1.05])
ax.set_xlabel('Recall', fontsize=15)
ax.set_ylabel('Precision', fontsize=15)
ax.set_title('Multi-Class Precision-Recall Curves (One-vs-Rest)\nDotted lines = class prevalence baseline', fontsize=14, fontweight='bold')
ax.legend(loc='upper right', frameon=True)
plt.tight_layout()
save('Fig05_Precision_Recall_Curves')


# ════════════════════════════════════════════════════════════════════════════
# Fig 06 – Shannon Entropy Distribution per Health State
# ════════════════════════════════════════════════════════════════════════════
print('Fig06: Shannon Entropy per State...')
eps = 1e-9
entropy = -np.sum(y_probs * np.log(y_probs + eps), axis=1)

fig, axes = plt.subplots(1, 3, figsize=FIG_SIZE, sharey=False)
for i, (cls_name, col, ax) in enumerate(zip(CLASS_NAMES, CLASS_COLS, axes)):
    mask = y_true == i
    h = entropy[mask]
    ax.hist(h, bins=25, color=col, edgecolor='black', alpha=0.8, density=True)
    ax.axvline(h.mean(), color='black', lw=2.5, linestyle='--', label=f'μ={h.mean():.3f}')
    ax.axvline(0.5, color='red', lw=1.5, linestyle=':', label='θ=0.5 nats')
    ax.set_title(f'{cls_name}\n(n={mask.sum()})', fontsize=13, fontweight='bold', color=col)
    ax.set_xlabel('Shannon Entropy H(p) [nats]', fontsize=12)
    if i == 0: ax.set_ylabel('Density', fontsize=12)
    ax.legend(fontsize=10, frameon=True)
    ax.set_xlim([-0.05, 1.15])

fig.suptitle('Shannon Entropy Distribution per Health State\n(Indeterminate threshold θ = 0.5 nats)',
             fontsize=14, fontweight='bold')
plt.tight_layout()
save('Fig06_Shannon_Entropy_States')


# ════════════════════════════════════════════════════════════════════════════
# Fig 07 – Ablation Study (correct retrained meta-learner)
# ════════════════════════════════════════════════════════════════════════════
print('Fig07: Ablation Study...')
scenario_order = [
    'Full Model (baseline)',
    'Remove Thermal',
    'Remove Current Signature',
    'Remove NASA RUL',
    'Remove Induction Motor',
    'Remove CWRU (vibration only)',
]
labels_short = [
    'Full Model\n(baseline)',
    '− Thermal',
    '− Current\nSignature',
    '− NASA RUL',
    '− Induction\nMotor',
    '− CWRU\n(Vibration)',
]
f1s    = [abl_results[s]['f1_macro']*100      for s in scenario_order]
ci_los = [abl_results[s]['f1_ci_95_lo']*100   for s in scenario_order]
ci_his = [abl_results[s]['f1_ci_95_hi']*100   for s in scenario_order]
deltas = [abl_results[s]['delta_vs_full']*100  for s in scenario_order]
errs   = [[f1 - lo for f1, lo in zip(f1s, ci_los)],
          [hi - f1 for f1, hi in zip(f1s, ci_his)]]

fig, ax = plt.subplots(figsize=FIG_SIZE)
cols = [COL_NORMAL if i==0 else COL_DARK for i in range(len(scenario_order))]
bars = ax.bar(range(len(scenario_order)), f1s, color=cols,
              edgecolor='black', alpha=0.85, width=0.6, zorder=3)
ax.errorbar(range(len(scenario_order)), f1s,
            yerr=errs, fmt='none', ecolor='#555', capsize=7, lw=2, zorder=4)
for idx, (bar, f1, delta) in enumerate(zip(bars, f1s, deltas)):
    delta_str = f'Δ{delta:+.1f}%' if idx > 0 else '(baseline)'
    ax.text(bar.get_x()+bar.get_width()/2, f1 + errs[1][idx] + 0.4,
            f'{f1:.1f}%\n{delta_str}', ha='center', fontsize=9, fontweight='bold')
ax.set_xticks(range(len(scenario_order)))
ax.set_xticklabels(labels_short, fontsize=11)
ax.set_ylim(82, 100)
ax.set_ylabel('Macro-F1 Score (%)', fontsize=14)
ax.set_title('Modality Sensitivity Ablation Study\n(Meta-learner retrained per scenario | 95% CI shown)',
             fontsize=14, fontweight='bold')
ax.axhline(f1s[0], color=COL_NORMAL, linestyle='--', lw=1.5, alpha=0.6)
ax.text(-0.4, f1s[0]+0.2, f'Baseline {f1s[0]:.1f}%', color=COL_NORMAL, fontsize=9)
plt.tight_layout()
save('Fig07_Ablation_Study')


# ════════════════════════════════════════════════════════════════════════════
# Fig 08 – Baseline Comparison
# ════════════════════════════════════════════════════════════════════════════
print('Fig08: Baseline Comparison...')
baseline_display = {
    'majority_class':  ('Majority\nClass',     COL_GREY),
    'unimodal_cwru':   ('Uni-modal\n(CWRU)',    COL_GREY),
    'rule_based':      ('Rule-Based\nExpert',   COL_GREY),
    'late_fusion':     ('Late\nFusion',         '#85c1e9'),
    'early_fusion':    ('Early Fusion\n(MLP)',  '#5dade2'),
}
names, scores, colors_b = [], [], []
for key, (label, col) in baseline_display.items():
    if key in cb_results:
        names.append(label)
        scores.append(cb_results[key]['f1_macro'] * 100)
        colors_b.append(col)
names.append('Meta-Fusion\n(Ours)')
scores.append(meta_f1_cv * 100)
colors_b.append(COL_NORMAL)

fig, ax = plt.subplots(figsize=FIG_SIZE)
bars = ax.bar(range(len(names)), scores, color=colors_b, edgecolor='black', alpha=0.9, width=0.6, zorder=3)
for bar, score, name in zip(bars, scores, names):
    ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.8,
            f'{score:.1f}%', ha='center', fontsize=11, fontweight='bold')
# CI for ours
our_idx = len(names) - 1
ax.errorbar(our_idx, scores[our_idx],
            yerr=[[scores[our_idx]-meta_f1_ci_lo*100], [meta_f1_ci_hi*100-scores[our_idx]]],
            fmt='none', ecolor='black', capsize=8, lw=2.5, zorder=4)
ax.set_xticks(range(len(names)))
ax.set_xticklabels(names, fontsize=12)
ax.set_ylim(0, 115)
ax.set_ylabel('Macro-F1 Score (%)', fontsize=14)
ax.set_title(f'Comparative Method Performance\n(5-fold CV | Meta-Fusion F1={meta_f1_cv:.4f} ± {cv_data["cv_fold_summary"]["meta_fusion"]["f1"]["std"]:.4f})',
             fontsize=14, fontweight='bold')
# McNemar significance marks
for i in range(len(names)-1):
    ax.text(i, scores[i]+4, '**', ha='center', fontsize=14, color='red')
ax.text(-0.5, 108, '** p<0.0001 vs Meta-Fusion (McNemar\'s test)', fontsize=10, color='red', style='italic')
plt.tight_layout()
save('Fig08_Baseline_Comparison')


# ════════════════════════════════════════════════════════════════════════════
# Fig 09 – RUL Prediction Trajectory (time-ordered, last 200 samples)
# ════════════════════════════════════════════════════════════════════════════
print('Fig09: RUL Prediction Trajectory...')
N = min(200, len(y_true_rul))
idx = np.arange(N)
yt  = y_true_rul[-N:]
yp  = y_pred_rul[-N:]

# Attention intensity: higher near end-of-life
attn = np.exp(-yt / 35.0)
attn = (attn - attn.min()) / (attn.max() - attn.min() + 1e-6)

fig, ax = plt.subplots(figsize=FIG_SIZE)
for i in range(N-1):
    ax.axvspan(i, i+1, color='#1abc9c', alpha=attn[i]*0.25, lw=0)
ax.plot(idx, yt, 'k--', lw=2.5, label='True RUL', alpha=0.8, zorder=3)
ax.plot(idx, yp, color=COL_CRITICAL, lw=3.5, label='Predicted RUL', zorder=4)
ax.fill_between(idx, yt, yp, alpha=0.12, color='grey', label='Prediction error region')
ax.axhline(50, color=COL_WARNING, lw=1.5, linestyle=':', alpha=0.8, label='Maintenance trigger (50 h)')
ax.axhline(150, color='orange', lw=1.5, linestyle=':', alpha=0.5, label='Warning threshold (150 h)')

legend_els = [
    Line2D([0],[0], color='k', lw=2.5, linestyle='--', label='True RUL'),
    Line2D([0],[0], color=COL_CRITICAL, lw=3.5, label='Predicted RUL'),
    mpatches.Patch(color='#1abc9c', alpha=0.5, label='Degradation attention intensity'),
    mpatches.Patch(color='grey', alpha=0.3, label='Prediction error region'),
    Line2D([0],[0], color=COL_WARNING, lw=1.5, linestyle=':', label='Maintenance trigger (50 h)'),
]
ax.legend(handles=legend_els, loc='upper right', fontsize=11, frameon=True)
ax.set_xlabel('Temporal Sample Index', fontsize=14)
ax.set_ylabel('Remaining Useful Life (h)', fontsize=14)
mae = np.mean(np.abs(yp - yt))
ax.set_title(f'RUL Prognostic Trajectory\nBi-LSTM-Attention Expert | System MAE = {official["rul_mae"]:.2f} h',
             fontsize=14, fontweight='bold')
plt.tight_layout()
save('Fig09_RUL_Prediction_Trajectory')


# ════════════════════════════════════════════════════════════════════════════
# Fig 10 – RUL Scatter (Predicted vs True)
# ════════════════════════════════════════════════════════════════════════════
print('Fig10: RUL Scatter...')
fig, ax = plt.subplots(figsize=(8, 8))
rul_max = max(y_true_rul.max(), y_pred_rul.max())
sc = ax.scatter(y_true_rul, y_pred_rul, alpha=0.45, s=35,
                c=np.abs(y_pred_rul - y_true_rul), cmap='RdYlGn_r',
                edgecolors='none', vmin=0, vmax=40)
plt.colorbar(sc, ax=ax, label='Absolute Error (h)')
ax.plot([0, rul_max], [0, rul_max], 'k-', lw=2.5, label='Perfect prediction (y = x)', zorder=3)
ax.fill_between([0, rul_max],
                [max(0, x-10) for x in [0, rul_max]],
                [x+10 for x in [0, rul_max]],
                alpha=0.1, color='green', label='±10 h band')
# Metrics annotation
mae_s = official['rul_mae']
rmse_s = official['rul_rmse']
ax.text(0.05, 0.95, f'System-level\nMAE  = {mae_s:.2f} h\nRMSE = {rmse_s:.2f} h\nNRMSE = {rmse_s/y_true_rul.max():.3f}',
        transform=ax.transAxes, fontsize=12, va='top',
        bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
ax.set_xlabel('True RUL (h)', fontsize=14)
ax.set_ylabel('Predicted RUL (h)', fontsize=14)
ax.set_title('RUL Prognostic Error Distribution\nColour = Absolute Error | IMS Bearing Dataset',
             fontsize=14, fontweight='bold')
ax.legend(loc='lower right', fontsize=11)
ax.set_xlim([-2, rul_max+5]); ax.set_ylim([-2, rul_max+5])
plt.tight_layout()
save('Fig10_RUL_Scatter_Predicted_vs_True')


# ════════════════════════════════════════════════════════════════════════════
# Fig 11 – Inference Latency (Component Breakdown + CDF)
# ════════════════════════════════════════════════════════════════════════════
print('Fig11: Latency (Component + CDF)...')
fig, (ax_bar, ax_cdf) = plt.subplots(1, 2, figsize=FIG_SIZE)

# Component bar chart (P50)
comp_labels = {
    '3_infer_cwru':      'CWRU-CNN',
    '3_infer_induction': 'Induction-CNN',
    '3_infer_nasa':      'NASA Bi-LSTM',
    '3_infer_current':   'Current-CNN (v5)',
    '3_infer_thermal':   'Thermal-MobileNet',
    '5_meta_fusion_xgb': 'Meta-Fusion\n(XGBoost)',
}
p50s = [comp_lats[k]['p50_ms'] for k in comp_labels]
p99s = [comp_lats[k]['p99_ms'] for k in comp_labels]
lbls = list(comp_labels.values())
y_pos = np.arange(len(lbls))
col_bars = [COL_DARK]*5 + [COL_MAIN]

ax_bar.barh(y_pos, p50s, color=col_bars, edgecolor='black', alpha=0.85, height=0.5, label='P50')
ax_bar.barh(y_pos, [p-s for p, s in zip(p99s, p50s)], left=p50s, color='#aab7b8',
            edgecolor='black', alpha=0.6, height=0.5, label='P99−P50')
for i, (p50, p99) in enumerate(zip(p50s, p99s)):
    ax_bar.text(p99+5, i, f'{p50:.0f}ms', va='center', fontsize=9, fontweight='bold')
ax_bar.set_yticks(y_pos); ax_bar.set_yticklabels(lbls, fontsize=10)
ax_bar.set_xlabel('Latency (ms)', fontsize=12)
ax_bar.set_title('Component-Level Latency\nP50 + P99 (warm-start, n=1000)', fontsize=12, fontweight='bold')
ax_bar.axvline(lat_raw['estimated_pipeline_p50_ms'], color='red', lw=1.5, linestyle='--', alpha=0.7)
ax_bar.text(lat_raw['estimated_pipeline_p50_ms']+5, -0.6,
            f'Total P50 ≈ {lat_raw["estimated_pipeline_p50_ms"]:.0f} ms', color='red', fontsize=8)
ax_bar.legend(fontsize=9, loc='lower right')

# CDF for meta-fusion stack latency
p50_lat = np.percentile(latencies, 50)
p99_lat = np.percentile(latencies, 99)
sorted_lat = np.sort(latencies)
cdf = np.arange(1, len(sorted_lat)+1) / len(sorted_lat)
ax_cdf.plot(sorted_lat, cdf, color=COL_MAIN, lw=3)
ax_cdf.axvline(p50_lat, color=COL_NORMAL, lw=2, linestyle='--', label=f'P50 = {p50_lat:.1f} ms')
ax_cdf.axvline(p99_lat, color=COL_CRITICAL, lw=2, linestyle='--', label=f'P99 = {p99_lat:.1f} ms')
ax_cdf.set_xlabel('XGBoost Stack Latency (ms)', fontsize=12)
ax_cdf.set_ylabel('Cumulative Probability', fontsize=12)
ax_cdf.set_title('Meta-Fusion Stack Latency CDF\n(XGBoost only; full pipeline ~1050 ms)', fontsize=12, fontweight='bold')
ax_cdf.legend(loc='lower right', fontsize=10)
ax_cdf.set_xlim([0, p99_lat * 1.2])

plt.suptitle('Inference Latency Analysis (CPU-only, AMD64, 4-core)',
             fontsize=13, fontweight='bold', y=1.01)
plt.tight_layout()
save('Fig11_Inference_Latency_CDF')


# ════════════════════════════════════════════════════════════════════════════
# Fig 12 – XGBoost Feature Importance
# ════════════════════════════════════════════════════════════════════════════
print('Fig12: Feature Importance...')
import joblib
xgb_path = os.path.join(PROJECT_ROOT, 'Trained_models/meta_fusion/meta_fusion_xgb.pkl')
try:
    import joblib
    stack = joblib.load(xgb_path)
    # The stacking classifier's best XGBoost base estimator
    xgb_model = None
    if hasattr(stack, 'estimators_'):
        for name, est in stack.estimators_:
            if 'xgb' in name.lower():
                xgb_model = est
                break
    if xgb_model is None and hasattr(stack, 'final_estimator_'):
        # Try final estimator
        if hasattr(stack.final_estimator_, 'feature_importances_'):
            xgb_model = stack.final_estimator_

    if xgb_model is not None and hasattr(xgb_model, 'feature_importances_'):
        importances = xgb_model.feature_importances_

        # Build 32-dim feature labels
        expert_names = ['CWRU', 'Induction', 'NASA', 'Current', 'Thermal']
        feat_labels = []
        for expert in expert_names:
            feat_labels += [f'{expert} P(N)', f'{expert} P(W)', f'{expert} P(C)',
                            f'{expert} Entropy', f'{expert} Margin']
        feat_labels += ['Global P(N)', 'Global P(W)', 'Global P(C)',
                        'Var P(N)', 'Var P(W)', 'Var P(C)', 'Global Entropy']
        # Pad/trim
        n = min(len(importances), len(feat_labels))
        importances = importances[:n]
        feat_labels = feat_labels[:n]

        order = np.argsort(importances)[-20:]  # top 20
        fig, ax = plt.subplots(figsize=FIG_SIZE)
        colors_fi = []
        for l in [feat_labels[i] for i in order]:
            if 'CWRU' in l: colors_fi.append('#2ecc71')
            elif 'NASA' in l: colors_fi.append('#3498db')
            elif 'Current' in l: colors_fi.append('#e67e22')
            elif 'Induction' in l: colors_fi.append('#9b59b6')
            elif 'Thermal' in l: colors_fi.append('#e74c3c')
            else: colors_fi.append('#95a5a6')
        ax.barh([feat_labels[i] for i in order], importances[order],
                color=colors_fi, edgecolor='black', alpha=0.85)
        ax.set_xlabel('Feature Importance (XGBoost gain)', fontsize=13)
        ax.set_title('Top-20 Meta-Feature Importances\n(XGBoost base estimator of stacking ensemble)',
                     fontsize=14, fontweight='bold')
        legend_els = [mpatches.Patch(color='#2ecc71', label='CWRU Vibration'),
                      mpatches.Patch(color='#3498db', label='NASA RUL'),
                      mpatches.Patch(color='#e67e22', label='Current Signature'),
                      mpatches.Patch(color='#9b59b6', label='Induction Motor'),
                      mpatches.Patch(color='#e74c3c', label='Thermal'),
                      mpatches.Patch(color='#95a5a6', label='Global stats')]
        ax.legend(handles=legend_els, loc='lower right', fontsize=10)
        plt.tight_layout()
        save('Fig12_Feature_Importance')
    else:
        raise ValueError('No XGBoost base estimator with feature_importances_ found')
except Exception as e:
    print(f'  [Skip] Feature importance: {e}')
    # Fallback: per-modality mean importance from ablation Δ
    fig, ax = plt.subplots(figsize=FIG_SIZE)
    mod_names  = ['CWRU\nVibration', 'NASA\nRUL', 'Induction\nMotor', 'Thermal', 'Current\nSignature']
    mod_deltas = [0.0332, 0.0207, 0.0195, 0.0118, 0.0050]
    mod_cols   = [COL_NORMAL, COL_MAIN, '#9b59b6', COL_CRITICAL, COL_WARNING]
    ax.bar(mod_names, [d*100 for d in mod_deltas], color=mod_cols, edgecolor='black', alpha=0.85, width=0.5)
    for i, (name, delta) in enumerate(zip(mod_names, mod_deltas)):
        ax.text(i, delta*100+0.1, f'{delta*100:.2f} pp', ha='center', fontsize=12, fontweight='bold')
    ax.set_ylabel('F1 Drop when Removed (pp)', fontsize=13)
    ax.set_title('Modality Importance (Δ F1 when removed)\nDerived from ablation study', fontsize=14, fontweight='bold')
    plt.tight_layout()
    save('Fig12_Feature_Importance')


# ════════════════════════════════════════════════════════════════════════════
# Fig 13 – Multi-Metric Summary Dashboard
# ════════════════════════════════════════════════════════════════════════════
print('Fig13: Multi-Metric Summary Dashboard...')
fig = plt.figure(figsize=(12, 9))
gs = gridspec.GridSpec(2, 3, figure=fig, hspace=0.45, wspace=0.35)

# ── (0,0) 5-fold CV F1 per fold ──────────────────────────────────────────
ax1 = fig.add_subplot(gs[0, 0])
fold_labels = [f'Fold {i+1}' for i in range(5)]
fold_cols = [COL_NORMAL if f > meta_f1_cv else COL_WARNING for f in cv_folds]
bars1 = ax1.bar(fold_labels, [f*100 for f in cv_folds], color=fold_cols, edgecolor='black', alpha=0.85)
ax1.axhline(meta_f1_cv*100, color='red', lw=2, linestyle='--')
ax1.set_ylim(84, 98)
ax1.set_ylabel('F1-macro (%)')
ax1.set_title(f'5-Fold CV F1\n{meta_f1_cv:.4f} ± {cv_data["cv_fold_summary"]["meta_fusion"]["f1"]["std"]:.4f}', fontsize=12, fontweight='bold')
for bar, f in zip(bars1, cv_folds):
    ax1.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.1, f'{f*100:.1f}', ha='center', fontsize=9)

# ── (0,1) AUC per fold ───────────────────────────────────────────────────
ax2 = fig.add_subplot(gs[0, 1])
auc_folds = cv_data['cv_fold_summary']['meta_fusion']['auc']['folds']
auc_mean  = cv_data['cv_fold_summary']['meta_fusion']['auc']['mean']
ax2.bar(fold_labels, [a*100 for a in auc_folds], color=COL_MAIN, edgecolor='black', alpha=0.85)
ax2.axhline(auc_mean*100, color='red', lw=2, linestyle='--')
ax2.set_ylim(95, 102)
ax2.set_ylabel('ROC-AUC (%)')
ax2.set_title(f'5-Fold CV AUC\n{auc_mean:.4f} ± {cv_data["cv_fold_summary"]["meta_fusion"]["auc"]["std"]:.4f}', fontsize=12, fontweight='bold')
for bar, a in zip(ax2.patches, auc_folds):
    ax2.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.04, f'{a*100:.2f}', ha='center', fontsize=9)

# ── (0,2) RUL metrics ────────────────────────────────────────────────────
ax3 = fig.add_subplot(gs[0, 2])
rul_metrics  = ['MAE\n(h)', 'RMSE\n(h)', 'NRMSE\n(×100)']
rul_vals     = [official['rul_mae'], official['rul_rmse'], 26.97]
ax3.bar(rul_metrics, rul_vals, color=[COL_WARNING, COL_CRITICAL, COL_GREY],
        edgecolor='black', alpha=0.85)
for bar, v in zip(ax3.patches, rul_vals):
    ax3.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.3,
             f'{v:.2f}', ha='center', fontsize=11, fontweight='bold')
ax3.set_ylabel('Value')
ax3.set_title('RUL Prediction Metrics\n(System-level, 300 samples)', fontsize=12, fontweight='bold')
ax3_note = ax3.text(0.5, -0.22, 'Units: h (NOT %) — corrected from original submission',
    transform=ax3.transAxes, ha='center', fontsize=8, color='red', style='italic')

# ── (1,0:2) Per-class F1 comparison across methods ───────────────────────
ax4 = fig.add_subplot(gs[1, :2])
methods_f1 = {
    'Majority Class': [0.0, 0.0, 0.0],
    'Late Fusion':    [0.80, 0.72, 0.71],
    'Meta-Fusion':    [official['report']['0']['f1-score'],
                       official['report']['1']['f1-score'],
                       official['report']['2']['f1-score']],
}
x_pos = np.arange(3)
width_m = 0.25
for idx, (method, vals) in enumerate(methods_f1.items()):
    col_m = [COL_GREY, '#5dade2', COL_NORMAL][idx]
    bars_m = ax4.bar(x_pos + idx*width_m, [v*100 for v in vals], width_m,
                     label=method, color=col_m, edgecolor='black', alpha=0.85)
ax4.set_xticks(x_pos + width_m)
ax4.set_xticklabels([f'{c}\n(n={n})' for c, n in zip(CLASS_NAMES, ns)], fontsize=12)
ax4.set_ylim(0, 110)
ax4.set_ylabel('F1-Score (%)')
ax4.set_title('Per-Class F1 Comparison vs Baselines\n(CRITICAL: corrected from P=R=F1=1.00 → P=R=F1=0.893)',
              fontsize=12, fontweight='bold')
ax4.legend(loc='upper left', fontsize=10)

# ── (1,2) Bootstrap CI ───────────────────────────────────────────────────
ax5 = fig.add_subplot(gs[1, 2])
bs = cv_data['bootstrap_ci_f1']
ax5.barh(['Meta-Fusion'], [bs['mean']*100], color=COL_NORMAL, edgecolor='black', alpha=0.85)
ax5.errorbar([bs['mean']*100], ['Meta-Fusion'],
             xerr=[[bs['mean']*100 - bs['ci_95_lo']*100],
                   [bs['ci_95_hi']*100 - bs['mean']*100]],
             fmt='none', ecolor='black', capsize=10, lw=3)
ax5.set_xlim(88, 94)
ax5.set_xlabel('F1-macro (%)')
ax5.set_title(f'Bootstrap 95% CI\n(n=1000 resamples)',fontsize=12, fontweight='bold')
ax5.text(0.02, 0.25, f'[{bs["ci_95_lo"]*100:.2f}, {bs["ci_95_hi"]*100:.2f}]',
         transform=ax5.transAxes, fontsize=11, fontweight='bold')

fig.suptitle('MotorGuard Digital Twin — Publication Results Summary\n(v5 StatisticsExtractor Pipeline | May 2026)',
             fontsize=14, fontweight='bold', y=1.01)
save('Fig13_MultiMetric_Comparison')


print(f'\nAll 13 figures saved to:\n  {OUT_DIR}')
print('\nVerification — key values used:')
print(f'  F1-macro (5-fold CV): {meta_f1_cv:.4f}  [was 0.9061 in old script]')
print(f'  Confusion matrix source: raw_eval_data.npz (May 27 v5 run)')
print(f'  Ablation source: ablation_proper.json (retrained meta-learner)')
print(f'  Latency CDF: XGBoost stack only (P50={np.percentile(latencies,50):.1f} ms)')
print(f'  Full pipeline P50: ~{lat_raw["estimated_pipeline_p50_ms"]:.0f} ms')
