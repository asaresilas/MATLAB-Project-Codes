"""
Update RUL visualization to include Months and Years as separate plots
"""
import json

# Load notebook
with open('notebooks/02_NASA_ML_training.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Find the visualization cell (Cell 9 usually, or search for content)
viz_cell_index = -1
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code' and any('VISUALIZE RUL IN MULTIPLE TIME UNITS' in line for line in cell['source']):
        viz_cell_index = i
        break

if viz_cell_index != -1:
    # New code with ALL time units plotted separately
    new_viz_code = [
        "# ============================================\n",
        "# VISUALIZE RUL IN MULTIPLE TIME UNITS\n",
        "# ============================================\n",
        "\n",
        "# Calculate RUL in all formats for 1st test (example)\n",
        "example_files = 2156\n",
        "rul_data = [calculate_rul(i, example_files) for i in range(example_files)]\n",
        "\n",
        "# Extract different time units\n",
        "rul_percentage = [r['percentage'] for r in rul_data]\n",
        "rul_hours = [r['hours'] for r in rul_data]\n",
        "rul_days = [r['days'] for r in rul_data]\n",
        "rul_weeks = [r['weeks'] for r in rul_data]\n",
        "rul_months = [r['months'] for r in rul_data]\n",
        "rul_years = [r['years'] for r in rul_data]\n",
        "\n",
        "# Create separate plots for each unit\n",
        "time_indices = np.arange(len(rul_data))\n",
        "\n",
        "# 1. RUL in Percentage\n",
        "plt.figure(figsize=(16, 5))\n",
        "plt.plot(time_indices, rul_percentage, linewidth=2.5, color='darkblue', label='RUL (%)')\n",
        "plt.axhline(y=50, color='orange', linestyle='--', linewidth=2, alpha=0.7, label='50% RUL')\n",
        "plt.axhline(y=20, color='red', linestyle='--', linewidth=2, alpha=0.7, label='20% RUL (Critical)')\n",
        "plt.xlabel('File Index (Time)', fontsize=13, fontweight='bold')\n",
        "plt.ylabel('RUL (%)', fontsize=13, fontweight='bold')\n",
        "plt.title('Remaining Useful Life - Percentage', fontsize=15, fontweight='bold')\n",
        "plt.grid(True, alpha=0.4)\n",
        "plt.legend(fontsize=12)\n",
        "plt.tight_layout()\n",
        "plt.show()\n",
        "\n",
        "# 2. RUL in Hours\n",
        "plt.figure(figsize=(16, 5))\n",
        "plt.plot(time_indices, rul_hours, linewidth=2.5, color='green', label='RUL (Hours)')\n",
        "plt.xlabel('File Index (Time)', fontsize=13, fontweight='bold')\n",
        "plt.ylabel('RUL (Hours)', fontsize=13, fontweight='bold')\n",
        "plt.title('Remaining Useful Life - Hours', fontsize=15, fontweight='bold')\n",
        "plt.grid(True, alpha=0.4)\n",
        "plt.legend(fontsize=12)\n",
        "plt.tight_layout()\n",
        "plt.show()\n",
        "\n",
        "# 3. RUL in Days\n",
        "plt.figure(figsize=(16, 5))\n",
        "plt.plot(time_indices, rul_days, linewidth=2.5, color='purple', label='RUL (Days)')\n",
        "plt.axhline(y=7, color='orange', linestyle='--', linewidth=2, alpha=0.7, label='1 Week')\n",
        "plt.axhline(y=3, color='red', linestyle='--', linewidth=2, alpha=0.7, label='3 Days (Critical)')\n",
        "plt.xlabel('File Index (Time)', fontsize=13, fontweight='bold')\n",
        "plt.ylabel('RUL (Days)', fontsize=13, fontweight='bold')\n",
        "plt.title('Remaining Useful Life - Days', fontsize=15, fontweight='bold')\n",
        "plt.grid(True, alpha=0.4)\n",
        "plt.legend(fontsize=12)\n",
        "plt.tight_layout()\n",
        "plt.show()\n",
        "\n",
        "# 4. RUL in Weeks\n",
        "plt.figure(figsize=(16, 5))\n",
        "plt.plot(time_indices, rul_weeks, linewidth=2.5, color='coral', label='RUL (Weeks)')\n",
        "plt.xlabel('File Index (Time)', fontsize=13, fontweight='bold')\n",
        "plt.ylabel('RUL (Weeks)', fontsize=13, fontweight='bold')\n",
        "plt.title('Remaining Useful Life - Weeks', fontsize=15, fontweight='bold')\n",
        "plt.grid(True, alpha=0.4)\n",
        "plt.legend(fontsize=12)\n",
        "plt.tight_layout()\n",
        "plt.show()\n",
        "\n",
        "# 5. RUL in Months\n",
        "plt.figure(figsize=(16, 5))\n",
        "plt.plot(time_indices, rul_months, linewidth=2.5, color='teal', label='RUL (Months)')\n",
        "plt.xlabel('File Index (Time)', fontsize=13, fontweight='bold')\n",
        "plt.ylabel('RUL (Months)', fontsize=13, fontweight='bold')\n",
        "plt.title('Remaining Useful Life - Months', fontsize=15, fontweight='bold')\n",
        "plt.grid(True, alpha=0.4)\n",
        "plt.legend(fontsize=12)\n",
        "plt.tight_layout()\n",
        "plt.show()\n",
        "\n",
        "# 6. RUL in Years\n",
        "plt.figure(figsize=(16, 5))\n",
        "plt.plot(time_indices, rul_years, linewidth=2.5, color='brown', label='RUL (Years)')\n",
        "plt.xlabel('File Index (Time)', fontsize=13, fontweight='bold')\n",
        "plt.ylabel('RUL (Years)', fontsize=13, fontweight='bold')\n",
        "plt.title('Remaining Useful Life - Years', fontsize=15, fontweight='bold')\n",
        "plt.grid(True, alpha=0.4)\n",
        "plt.legend(fontsize=12)\n",
        "plt.tight_layout()\n",
        "plt.show()\n",
        "\n",
        "# Summary statistics\n",
        "print(\"\\nRUL Statistics for Full Test Duration:\")\n",
        "print(\"=\" * 60)\n",
        "print(f\"Total duration: {rul_days[0]:.1f} days = {rul_weeks[0]:.2f} weeks = {rul_months[0]:.2f} months\")\n"
    ]
    
    nb['cells'][viz_cell_index]['source'] = new_viz_code
    
    # Save
    with open('notebooks/02_NASA_ML_training.ipynb', 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=4, ensure_ascii=False)
    
    print("Updated visualization cell to include Months and Years plots.")
else:
    print("Could not find the visualization cell to update.")
