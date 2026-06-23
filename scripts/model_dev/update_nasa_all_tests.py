"""
Update 02_NASA_ML_training.ipynb to use all 3 NASA tests
"""
import json

# Load existing notebook
with open('notebooks/02_NASA_ML_training.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Find and update the data exploration cell (cell that loads files)
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code' and any('EXPLORE DATASET STRUCTURE' in line for line in cell['source']):
        # Update to load all 3 tests
        cell['source'] = [
            "# ============================================\n",
            "# EXPLORE DATASET STRUCTURE - ALL 3 TESTS\n",
            "# ============================================\n",
            "\n",
            "# Path to NASA data\n",
            "NASA_DATA_DIR = r'../NASA_Data'\n",
            "\n",
            "# Define all 3 test directories\n",
            "test_configs = {\n",
            "    '1st_test': os.path.join(NASA_DATA_DIR, '1st_test', '1st_test'),\n",
            "    '2nd_test': os.path.join(NASA_DATA_DIR, '2nd_test', '2nd_test'),\n",
            "    '3rd_test': os.path.join(NASA_DATA_DIR, '3rd_test', '4th_test', 'txt')  # Note: Different structure\n",
            "}\n",
            "\n",
            "# Collect information about each test\n",
            "test_info = {}\n",
            "\n",
            "print(\"Scanning NASA Bearing Test Directories...\")\n",
            "print(\"=\" * 60)\n",
            "\n",
            "for test_name, test_path in test_configs.items():\n",
            "    if os.path.exists(test_path):\n",
            "        # Get all files in directory\n",
            "        files = sorted([f for f in os.listdir(test_path) \n",
            "                       if os.path.isfile(os.path.join(test_path, f))])\n",
            "        \n",
            "        test_info[test_name] = {\n",
            "            'path': test_path,\n",
            "            'files': files,\n",
            "            'count': len(files)\n",
            "        }\n",
            "        \n",
            "        print(f\"\\n{test_name}:\")\n",
            "        print(f\"  Path: {test_path}\")\n",
            "        print(f\"  Files: {len(files):,}\")\n",
            "        print(f\"  First file: {files[0] if files else 'N/A'}\")\n",
            "        print(f\"  Last file: {files[-1] if files else 'N/A'}\")\n",
            "    else:\n",
            "        print(f\"\\n{test_name}: ✗ Path not found\")\n",
            "        print(f\"  Expected: {test_path}\")\n",
            "\n",
            "# Calculate totals\n",
            "total_files = sum(info['count'] for info in test_info.values())\n",
            "\n",
            "print(\"\\n\" + \"=\" * 60)\n",
            "print(f\"TOTAL FILES ACROSS ALL TESTS: {total_files:,}\")\n",
            "print(\"=\" * 60)\n",
            "\n",
            "# We'll combine all tests for training\n",
            "print(\"\\nStrategy: Combine all 3 tests into one large dataset\")\n",
            "print(\"  - More data = better model generalization\")\n",
            "print(\"  - Captures different failure modes\")\n",
            "print(\"  - Train/Val/Test split: 60/20/20 (temporal within each test)\")\n"
        ]
        print(f"Updated cell {i}: Data exploration to include all 3 tests")
        break

# Save
with open('notebooks/02_NASA_ML_training.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=4, ensure_ascii=False)

print("\nPhase 1: Updated data exploration cell")
print("Next: Will update feature extraction to process all 3 tests")
