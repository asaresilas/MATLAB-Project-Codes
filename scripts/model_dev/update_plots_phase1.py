"""
Update NASA notebook to use separate figures instead of subplots
"""
import json

# Load notebook
with open('notebooks/02_NASA_ML_training.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Find and update visualization cells
# We'll identify them by looking for plt.subplots or fig.add_subplot

# Cell 4: Vibration signals visualization (3x4 subplots)
# Replace with individual plots for each bearing at each time point
cell_4_new_code = [
    "# ============================================\n",
    "# LOAD AND VISUALIZE SAMPLE DATA\n",
    "# ============================================\n",
    "\n",
    "# Initialize NASA loader\n",
    "loader = NASALoader(TEST_PATH)\n",
    "\n",
    "# Load first, middle, and last files to see degradation\n",
    "sample_indices = [0, len(data_files)//2, -1]\n",
    "sample_labels = ['Start (Healthy)', 'Middle', 'End (Near Failure)']\n",
    "\n",
    "print(\"Visualizing vibration signals at different time points...\\n\")\n",
    "\n",
    "# Plot each time point separately\n",
    "for idx, label in zip(sample_indices, sample_labels):\n",
    "    filename = data_files[idx]\n",
    "    data = loader.load_snapshot(filename)  # Shape: (20480, 4)\n",
    "    \n",
    "    print(f\"File: {filename} - {label}\")\n",
    "    \n",
    "    # Create separate figure for this time point\n",
    "    plt.figure(figsize=(16, 10))\n",
    "    \n",
    "    for bearing in range(4):\n",
    "        signal = data[:, bearing]\n",
    "        \n",
    "        # Create subplot for each bearing\n",
    "        plt.subplot(2, 2, bearing + 1)\n",
    "        plt.plot(signal[:1000], linewidth=1.5, color=f'C{bearing}', label=f'Bearing {bearing+1}')\n",
    "        \n",
    "        # Calculate RMS for annotation\n",
    "        rms = np.sqrt(np.mean(signal**2))\n",
    "        \n",
    "        plt.title(f'Bearing {bearing+1} - RMS: {rms:.4f}', fontsize=12, fontweight='bold')\n",
    "        plt.xlabel('Sample', fontsize=11)\n",
    "        plt.ylabel('Amplitude', fontsize=11)\n",
    "        plt.grid(True, alpha=0.3)\n",
    "        plt.legend(loc='upper right', fontsize=10)\n",
    "    \n",
    "    plt.suptitle(f'Vibration Signals - {label}', fontsize=14, fontweight='bold')\n",
    "    plt.tight_layout()\n",
    "    plt.show()\n",
    "    print()\n",
    "\n",
    "print(f\"\\nData shape: {data.shape}\")\n",
    "print(f\"Sampling rate: 20 kHz\")\n",
    "print(f\"Duration: {data.shape[0]/20000:.2f} seconds\")\n"
]

# Cell 6: RUL visualization - already standalone, just improve it
cell_6_new_code = [
    "# ============================================\n",
    "# CREATE RUL LABELS\n",
    "# ============================================\n",
    "\n",
    "def calculate_rul(file_index, total_files):\n",
    "    \"\"\"\n",
    "    Calculate Remaining Useful Life (RUL) as percentage.\n",
    "    \n",
    "    Args:\n",
    "        file_index: Current file index (0 to total_files-1)\n",
    "        total_files: Total number of files in the test\n",
    "    \n",
    "    Returns:\n",
    "        RUL as percentage (0-100)\n",
    "    \"\"\"\n",
    "    remaining_files = total_files - file_index\n",
    "    rul_percentage = (remaining_files / total_files) * 100\n",
    "    return rul_percentage\n",
    "\n",
    "# Calculate RUL for all files\n",
    "total_files = len(data_files)\n",
    "rul_labels = [calculate_rul(i, total_files) for i in range(total_files)]\n",
    "\n",
    "# Visualize RUL over time\n",
    "plt.figure(figsize=(16, 6))\n",
    "plt.plot(rul_labels, linewidth=2.5, color='darkblue', label='RUL (Linear Degradation)')\n",
    "plt.axhline(y=50, color='orange', linestyle='--', linewidth=2, label='50% RUL', alpha=0.7)\n",
    "plt.axhline(y=20, color='red', linestyle='--', linewidth=2, label='20% RUL (Critical)', alpha=0.7)\n",
    "plt.xlabel('File Index (Time)', fontsize=13, fontweight='bold')\n",
    "plt.ylabel('RUL (%)', fontsize=13, fontweight='bold')\n",
    "plt.title('Remaining Useful Life (RUL) Over Time - Linear Degradation Model', \n",
    "          fontsize=15, fontweight='bold')\n",
    "plt.grid(True, alpha=0.4)\n",
    "plt.legend(fontsize=12, loc='upper right')\n",
    "plt.tight_layout()\n",
    "plt.show()\n",
    "\n",
    "print(f\"RUL Statistics:\")\n",
    "print(f\"  Min RUL: {min(rul_labels):.2f}%\")\n",
    "print(f\"  Max RUL: {max(rul_labels):.2f}%\")\n",
    "print(f\"  Mean RUL: {np.mean(rul_labels):.2f}%\")\n",
    "print(f\"\\nExample RUL values:\")\n",
    "for i in [0, total_files//4, total_files//2, 3*total_files//4, total_files-1]:\n",
    "    print(f\"  File {i:4d}: RUL = {rul_labels[i]:6.2f}%\")\n"
]

# Update the cells
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        # Check if this is the visualization cell (cell 4)
        if any('LOAD AND VISUALIZE SAMPLE DATA' in line for line in cell['source']):
            nb['cells'][i]['source'] = cell_4_new_code
            print("Updated Cell: Load and Visualize Sample Data")
        
        # Check if this is the RUL visualization cell (cell 6)
        elif any('CREATE RUL LABELS' in line for line in cell['source']):
            nb['cells'][i]['source'] = cell_6_new_code
            print("Updated Cell: RUL Labels")

# Save
with open('notebooks/02_NASA_ML_training.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=4, ensure_ascii=False)

print("\nPhase 1 complete: Updated initial visualization cells")
