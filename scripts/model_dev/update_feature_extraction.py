"""
Update feature extraction and add train/test accuracy - Phase 2
"""
import json

# Load notebook
with open('notebooks/02_NASA_ML_training.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Find and update the feature extraction cell
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code' and any('EXTRACT FEATURES FROM ALL FILES' in line for line in cell['source']):
        # Update to process all 3 tests
        cell['source'] = [
            "# ============================================\n",
            "# EXTRACT FEATURES FROM ALL 3 TESTS\n",
            "# ============================================\n",
            "\n",
            "# Option to use subset for faster testing\n",
            "USE_SUBSET = False  # Set to True for quick testing\n",
            "SUBSET_SIZE_PER_TEST = 300  # Files per test if using subset\n",
            "\n",
            "# Initialize storage for all data\n",
            "all_features = []\n",
            "all_rul = []\n",
            "all_test_labels = []  # Track which test each sample came from\n",
            "\n",
            "print(\"Extracting features from all 3 NASA bearing tests...\")\n",
            "print(\"=\" * 70)\n",
            "\n",
            "# Process each test\n",
            "for test_name in ['1st_test', '2nd_test', '3rd_test']:\n",
            "    if test_name not in test_info:\n",
            "        print(f\"\\nSkipping {test_name} - not found\")\n",
            "        continue\n",
            "    \n",
            "    print(f\"\\nProcessing {test_name}...\")\n",
            "    \n",
            "    test_path = test_info[test_name]['path']\n",
            "    test_files = test_info[test_name]['files']\n",
            "    \n",
            "    # Use subset if enabled\n",
            "    if USE_SUBSET and len(test_files) > SUBSET_SIZE_PER_TEST:\n",
            "        # Take evenly spaced files to capture full degradation\n",
            "        indices = np.linspace(0, len(test_files)-1, SUBSET_SIZE_PER_TEST, dtype=int)\n",
            "        files_to_process = [test_files[i] for i in indices]\n",
            "        print(f\"  Using subset: {len(files_to_process)} files (evenly spaced)\")\n",
            "    else:\n",
            "        files_to_process = test_files\n",
            "        print(f\"  Processing all {len(files_to_process)} files\")\n",
            "    \n",
            "    # Initialize loader for this test\n",
            "    loader = NASALoader(test_path)\n",
            "    \n",
            "    # Calculate RUL for this test\n",
            "    total_files_in_test = len(files_to_process)\n",
            "    \n",
            "    # Extract features\n",
            "    test_features = []\n",
            "    test_rul = []\n",
            "    \n",
            "    for file_idx, filename in enumerate(tqdm(files_to_process, desc=f\"  {test_name}\")):\n",
            "        try:\n",
            "            # Load data\n",
            "            data = loader.load_snapshot(filename)\n",
            "            \n",
            "            # Calculate RUL for this file\n",
            "            rul = calculate_rul(file_idx, total_files_in_test)\n",
            "            \n",
            "            # Extract features from each bearing\n",
            "            file_features = {}\n",
            "            for bearing_idx in range(4):\n",
            "                signal = data[:, bearing_idx]\n",
            "                bearing_features = extract_features_from_signal(signal)\n",
            "                \n",
            "                # Add bearing prefix\n",
            "                for feat_name, feat_value in bearing_features.items():\n",
            "                    file_features[f'bearing{bearing_idx+1}_{feat_name}'] = feat_value\n",
            "            \n",
            "            test_features.append(file_features)\n",
            "            test_rul.append(rul)\n",
            "            \n",
            "        except Exception as e:\n",
            "            print(f\"\\n  Error processing {filename}: {e}\")\n",
            "            continue\n",
            "    \n",
            "    # Add to combined dataset\n",
            "    all_features.extend(test_features)\n",
            "    all_rul.extend(test_rul)\n",
            "    all_test_labels.extend([test_name] * len(test_features))\n",
            "    \n",
            "    print(f\"  ✓ Extracted {len(test_features)} samples from {test_name}\")\n",
            "\n",
            "# Convert to DataFrame\n",
            "features_df = pd.DataFrame(all_features)\n",
            "features_df['RUL'] = all_rul\n",
            "features_df['Test'] = all_test_labels\n",
            "\n",
            "print(\"\\n\" + \"=\" * 70)\n",
            "print(\"✓ Feature extraction complete!\")\n",
            "print(f\"\\nCombined Dataset:\")\n",
            "print(f\"  Total samples: {len(features_df):,}\")\n",
            "print(f\"  Features: {features_df.shape[1] - 2}  (48 features + RUL + Test)\")\n",
            "print(f\"\\nSamples per test:\")\n",
            "for test_name in ['1st_test', '2nd_test', '3rd_test']:\n",
            "    count = (features_df['Test'] == test_name).sum()\n",
            "    if count > 0:\n",
            "        print(f\"  {test_name}: {count:,} samples\")\n",
            "\n",
            "print(\"\\nFirst few samples:\")\n",
            "display(features_df.head())\n"
        ]
        print(f"Updated cell {i}: Feature extraction for all 3 tests")
        break

# Save
with open('notebooks/02_NASA_ML_training.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=4, ensure_ascii=False)

print("\nPhase 2: Updated feature extraction to process all 3 tests")
print("Next: Will add train accuracy metrics to model training section")
