"""
Add RUL time conversion to show hours, days, weeks, months, years
"""
import json

# Load notebook
with open('notebooks/02_NASA_ML_training.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Find the RUL calculation cell and enhance it
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code' and any('CREATE RUL LABELS' in line for line in cell['source']):
        # Add time-based RUL conversion
        cell['source'] = [
            "# ============================================\n",
            "# CREATE RUL LABELS (Percentage + Time Units)\n",
            "# ============================================\n",
            "\n",
            "# NASA test sampling information\n",
            "SAMPLING_INTERVAL_MINUTES = 10  # Files recorded every 10 minutes\n",
            "MINUTES_PER_HOUR = 60\n",
            "HOURS_PER_DAY = 24\n",
            "DAYS_PER_WEEK = 7\n",
            "DAYS_PER_MONTH = 30  # Approximate\n",
            "DAYS_PER_YEAR = 365\n",
            "\n",
            "def calculate_rul(file_index, total_files):\n",
            "    \"\"\"\n",
            "    Calculate Remaining Useful Life (RUL) in multiple formats.\n",
            "    \n",
            "    Args:\n",
            "        file_index: Current file index (0 to total_files-1)\n",
            "        total_files: Total number of files in the test\n",
            "    \n",
            "    Returns:\n",
            "        Dictionary with RUL in different units\n",
            "    \"\"\"\n",
            "    # Calculate remaining files\n",
            "    remaining_files = total_files - file_index\n",
            "    \n",
            "    # RUL as percentage\n",
            "    rul_percentage = (remaining_files / total_files) * 100\n",
            "    \n",
            "    # RUL in time units\n",
            "    rul_minutes = remaining_files * SAMPLING_INTERVAL_MINUTES\n",
            "    rul_hours = rul_minutes / MINUTES_PER_HOUR\n",
            "    rul_days = rul_hours / HOURS_PER_DAY\n",
            "    rul_weeks = rul_days / DAYS_PER_WEEK\n",
            "    rul_months = rul_days / DAYS_PER_MONTH\n",
            "    rul_years = rul_days / DAYS_PER_YEAR\n",
            "    \n",
            "    return {\n",
            "        'percentage': rul_percentage,\n",
            "        'minutes': rul_minutes,\n",
            "        'hours': rul_hours,\n",
            "        'days': rul_days,\n",
            "        'weeks': rul_weeks,\n",
            "        'months': rul_months,\n",
            "        'years': rul_years\n",
            "    }\n",
            "\n",
            "def format_rul_time(rul_dict):\n",
            "    \"\"\"\n",
            "    Format RUL in the most appropriate time unit.\n",
            "    \"\"\"\n",
            "    if rul_dict['years'] >= 1:\n",
            "        return f\"{rul_dict['years']:.2f} years\"\n",
            "    elif rul_dict['months'] >= 1:\n",
            "        return f\"{rul_dict['months']:.2f} months\"\n",
            "    elif rul_dict['weeks'] >= 1:\n",
            "        return f\"{rul_dict['weeks']:.2f} weeks\"\n",
            "    elif rul_dict['days'] >= 1:\n",
            "        return f\"{rul_dict['days']:.2f} days\"\n",
            "    elif rul_dict['hours'] >= 1:\n",
            "        return f\"{rul_dict['hours']:.2f} hours\"\n",
            "    else:\n",
            "        return f\"{rul_dict['minutes']:.0f} minutes\"\n",
            "\n",
            "# Example: Calculate RUL for different points\n",
            "print(\"RUL Calculation Examples:\")\n",
            "print(\"=\" * 80)\n",
            "\n",
            "example_total_files = 2156  # 1st test\n",
            "example_points = [0, 500, 1000, 1500, 2000, 2155]\n",
            "\n",
            "for file_idx in example_points:\n",
            "    rul = calculate_rul(file_idx, example_total_files)\n",
            "    print(f\"\\nFile {file_idx:4d}:\")\n",
            "    print(f\"  RUL: {rul['percentage']:6.2f}%\")\n",
            "    print(f\"  Time remaining:\")\n",
            "    print(f\"    {rul['minutes']:8.0f} minutes\")\n",
            "    print(f\"    {rul['hours']:8.2f} hours\")\n",
            "    print(f\"    {rul['days']:8.2f} days\")\n",
            "    print(f\"    {rul['weeks']:8.2f} weeks\")\n",
            "    print(f\"    {rul['months']:8.2f} months\")\n",
            "    print(f\"  Best format: {format_rul_time(rul)}\")\n",
            "\n",
            "print(\"\\n\" + \"=\" * 80)\n",
            "print(\"\\nNote: Files are recorded every 10 minutes in NASA dataset\")\n",
            "print(\"Total test duration ≈ 2156 files × 10 min = 21,560 min ≈ 15 days\")\n"
        ]
        print(f"Updated cell {i}: RUL calculation with time units")
        break

# Now add a visualization cell showing RUL in different time units
new_viz_cell = {
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "## RUL Visualization in Multiple Time Units\n",
        "\n",
        "Let's visualize RUL in different time formats to see which is most intuitive:\n",
        "- **Percentage**: 0-100%\n",
        "- **Hours**: Useful for short-term predictions\n",
        "- **Days**: Most practical for maintenance planning\n",
        "- **Weeks**: Good for medium-term planning\n"
    ]
}

# Add visualization code cell
new_code_cell = {
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [
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
        "\n",
        "# Create 4 separate plots\n",
        "time_indices = np.arange(len(rul_data))\n",
        "\n",
        "# Plot 1: RUL in Percentage\n",
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
        "# Plot 2: RUL in Hours\n",
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
        "# Plot 3: RUL in Days\n",
        "plt.figure(figsize=(16, 5))\n",
        "plt.plot(time_indices, rul_days, linewidth=2.5, color='purple', label='RUL (Days)')\n",
        "plt.axhline(y=7, color='orange', linestyle='--', linewidth=2, alpha=0.7, label='1 Week')\n",
        "plt.axhline(y=3, color='red', linestyle='--', linewidth=2, alpha=0.7, label='3 Days (Critical)')\n",
        "plt.xlabel('File Index (Time)', fontsize=13, fontweight='bold')\n",
        "plt.ylabel('RUL (Days)', fontsize=13, fontweight='bold')\n",
        "plt.title('Remaining Useful Life - Days (Most Practical)', fontsize=15, fontweight='bold')\n",
        "plt.grid(True, alpha=0.4)\n",
        "plt.legend(fontsize=12)\n",
        "plt.tight_layout()\n",
        "plt.show()\n",
        "\n",
        "# Plot 4: RUL in Weeks\n",
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
        "# Summary statistics\n",
        "print(\"\\nRUL Statistics for Full Test Duration:\")\n",
        "print(\"=\" * 60)\n",
        "print(f\"Total duration: {rul_hours[0]:.1f} hours = {rul_days[0]:.1f} days = {rul_weeks[0]:.2f} weeks\")\n",
        "print(f\"\\nAt 50% RUL:\")\n",
        "mid_idx = len(rul_data) // 2\n",
        "print(f\"  Remaining: {rul_hours[mid_idx]:.1f} hours = {rul_days[mid_idx]:.1f} days\")\n",
        "print(f\"\\nAt 20% RUL (Critical):\")\n",
        "critical_idx = int(len(rul_data) * 0.2)\n",
        "print(f\"  Remaining: {rul_hours[critical_idx]:.1f} hours = {rul_days[critical_idx]:.1f} days\")\n"
    ]
}

# Find where to insert these cells (after RUL calculation)
insert_index = None
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code' and any('CREATE RUL LABELS' in line for line in cell['source']):
        insert_index = i + 1
        break

if insert_index:
    nb['cells'].insert(insert_index, new_viz_cell)
    nb['cells'].insert(insert_index + 1, new_code_cell)
    print(f"Inserted RUL time visualization cells at index {insert_index}")

# Save
with open('notebooks/02_NASA_ML_training.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=4, ensure_ascii=False)

print("\n✓ Added RUL time unit conversions!")
print("  - RUL now calculated in: percentage, minutes, hours, days, weeks, months, years")
print("  - Added 4 visualization plots showing RUL in different time units")
print("  - Most practical: Days (for maintenance planning)")
