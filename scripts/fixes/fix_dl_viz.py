import json
import os

# Fix the regression visualization code to handle numpy arrays
notebook_path = r'd:/Silas Document/UMaT/Year 4/Project work/Matlab_Project codes/notebooks/02_NASA_DL_training.ipynb'

# Load notebook
with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Find and fix the problematic cell
fixed = False
for cell in nb['cells']:
    if cell['cell_type'] == 'code' and 'corrwith' in ''.join(cell['source']):
        # Replace with corrected code that works with the features_df
        cell['source'] = [
            "# Feature Correlation with RUL\n",
            "import seaborn as sns\n",
            "\n",
            "# Use the original features_df before sequence generation\n",
            "feature_cols = [c for c in features_df.columns if c != 'RUL']\n",
            "correlations = features_df[feature_cols].corrwith(features_df['RUL']).sort_values(ascending=False)\n",
            "top_features = correlations.abs().nlargest(15)\n",
            "\n",
            "plt.figure(figsize=(12, 8))\n",
            "plt.barh(range(len(top_features)), correlations[top_features.index].values, alpha=0.7)\n",
            "plt.yticks(range(len(top_features)), top_features.index)\n",
            "plt.xlabel('Correlation with RUL')\n",
            "plt.title('Top 15 Features Correlated with RUL', fontsize=14, fontweight='bold')\n",
            "plt.grid(True, alpha=0.3, axis='x')\n",
            "plt.tight_layout()\n",
            "plt.show()"
        ]
        fixed = True
        print("Fixed correlation visualization cell")
        break

if fixed:
    # Save notebook
    with open(notebook_path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=1)
    print("Successfully updated 02_NASA_DL_training.ipynb")
else:
    print("Could not find the problematic cell")
