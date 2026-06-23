import os
import sys

def verify_notebook():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

    nb_file = 'notebooks/02_NASA_DL_training.ipynb'
    print(f"Checking {nb_file}...")
    try:
        with open(nb_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'Trained_models' in content:
            print("Found 'Trained_models' in content.")
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if 'Trained_models' in line:
                    if len(line) < 500:
                        print(f"Line {i+1}: {line.strip()}")
        else:
            print("'Trained_models' NOT found in content.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verify_notebook()
