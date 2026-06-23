import json

notebook_path = r'd:/Silas Document/UMaT/Year 4/Project work/Matlab_Project codes/notebooks/02_NASA_DL_training.ipynb'

# New visualization cells to add
new_cells = [
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "## 7. Additional Data Exploration\n",
            "\n",
            "Let's explore the data distribution and feature correlations."
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Feature Distribution Analysis\n",
            "fig, axes = plt.subplots(2, 2, figsize=(15, 10))\n",
            "fig.suptitle('Feature Distribution Analysis', fontsize=16, fontweight='bold')\n",
            "\n",
            "# RUL Distribution\n",
            "axes[0, 0].hist(features_df['RUL'], bins=50, edgecolor='black', alpha=0.7)\n",
            "axes[0, 0].set_title('RUL Distribution')\n",
            "axes[0, 0].set_xlabel('RUL (%)')\n",
            "axes[0, 0].set_ylabel('Frequency')\n",
            "axes[0, 0].grid(True, alpha=0.3)\n",
            "\n",
            "# Sample RMS values across bearings\n",
            "rms_cols = [col for col in features_df.columns if 'rms' in col.lower()]\n",
            "for col in rms_cols:\n",
            "    axes[0, 1].plot(features_df[col], label=col, alpha=0.7)\n",
            "axes[0, 1].set_title('RMS Values Across Bearings')\n",
            "axes[0, 1].set_xlabel('Sample Index')\n",
            "axes[0, 1].set_ylabel('RMS Value')\n",
            "axes[0, 1].legend()\n",
            "axes[0, 1].grid(True, alpha=0.3)\n",
            "\n",
            "# Kurtosis Distribution\n",
            "kurt_cols = [col for col in features_df.columns if 'kurtosis' in col.lower()]\n",
            "for col in kurt_cols:\n",
            "    axes[1, 0].plot(features_df[col], label=col, alpha=0.7)\n",
            "axes[1, 0].set_title('Kurtosis Values Across Bearings')\n",
            "axes[1, 0].set_xlabel('Sample Index')\n",
            "axes[1, 0].set_ylabel('Kurtosis')\n",
            "axes[1, 0].legend()\n",
            "axes[1, 0].grid(True, alpha=0.3)\n",
            "\n",
            "# RUL vs Time\n",
            "axes[1, 1].scatter(range(len(features_df)), features_df['RUL'], alpha=0.5, s=10)\n",
            "axes[1, 1].set_title('RUL Over Time')\n",
            "axes[1, 1].set_xlabel('Sample Index')\n",
            "axes[1, 1].set_ylabel('RUL (%)')\n",
            "axes[1, 1].grid(True, alpha=0.3)\n",
            "\n",
            "plt.tight_layout()\n",
            "plt.show()\n",
            "\n",
            "print(f\"Total Samples: {len(features_df)}\")\n",
            "print(f\"RUL Range: {features_df['RUL'].min():.2f} - {features_df['RUL'].max():.2f}\")\n",
            "print(f\"Mean RUL: {features_df['RUL'].mean():.2f}\")"
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Correlation Heatmap\n",
            "import seaborn as sns\n",
            "\n",
            "# Select a subset of features for correlation analysis\n",
            "sample_features = ['b1_rms', 'b1_kurtosis', 'b1_skewness', 'b2_rms', 'b2_kurtosis', \n",
            "                   'b3_rms', 'b3_kurtosis', 'b4_rms', 'b4_kurtosis', 'RUL']\n",
            "corr_data = features_df[sample_features].corr()\n",
            "\n",
            "plt.figure(figsize=(12, 10))\n",
            "sns.heatmap(corr_data, annot=True, fmt='.2f', cmap='coolwarm', center=0,\n",
            "            square=True, linewidths=1, cbar_kws={\"shrink\": 0.8})\n",
            "plt.title('Feature Correlation Heatmap', fontsize=14, fontweight='bold')\n",
            "plt.tight_layout()\n",
            "plt.show()"
        ]
    }
]

# Load notebook
with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Find the position to insert (after data loading, before model definition)
insert_position = None
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'markdown' and 'Define Deep Learning Models' in ''.join(cell['source']):
        insert_position = i
        break

if insert_position:
    # Insert new cells
    for cell in reversed(new_cells):
        nb['cells'].insert(insert_position, cell)
    
    # Save notebook
    with open(notebook_path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=1)
    
    print(f"Successfully added {len(new_cells)} visualization cells to the notebook.")
else:
    print("Could not find insertion point in the notebook.")
