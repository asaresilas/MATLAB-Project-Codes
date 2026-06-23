import os
import json
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

import sys
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'utility_scripts'))
from plotting_config import apply_publication_style, save_figure

def generate_ablation_figure():
    print("🎨 Generating Standardized High-Resolution Ablation Figure...")
    apply_publication_style()
    
    # Load Data
    with open('results/publication_metrics/ablation_study.json', 'r') as f:
        data = json.load(f)
    df = pd.DataFrame(data)
    df['Scenario'] = df['Scenario'].str.replace('Ablation: ', '').str.replace('Baseline: ', '')
    
    # Create Figure (Custom vertical size to fit the requested 1800x2400 area)
    fig, ax = plt.subplots(figsize=(6, 8))
    
    # Preparation for grouped bar chart
    x = np.arange(len(df['Scenario']))
    width = 0.35
    
    # Plot F1-Macro and Critical Recall
    # We use a professional color palette
    colors = sns.color_palette("deep")
    
    rects1 = ax.barh(x - width/2, df['F1_Macro']*100, width, label='F1-Macro (%)', color=colors[0], alpha=0.9, edgecolor='black', linewidth=1)
    rects2 = ax.barh(x + width/2, df['Critical_Recall']*100, width, label='Critical Recall (%)', color=colors[1], alpha=0.9, edgecolor='black', linewidth=1)
    
    # 4. Styling
    ax.set_title('Hierarchical Meta-Fusion Ablation Analysis', fontweight='bold', pad=20)
    ax.set_xlabel('Score (%)', fontweight='bold')
    ax.set_yticks(x)
    ax.set_yticklabels(df['Scenario'])
    ax.set_xlim(0, 115) # Leave room for labels
    ax.invert_yaxis() # Highest modality count at top
    
    ax.legend(loc='lower right', frameon=True, shadow=True)
    
    # Add data labels on bars
    def autolabel(rects):
        for rect in rects:
            width = rect.get_width()
            ax.annotate(f'{width:.1f}%',
                        xy=(width, rect.get_y() + rect.get_height() / 2),
                        xytext=(5, 0),  # 5 points horizontal offset
                        textcoords="offset points",
                        ha='left', va='center', fontweight='bold')

    autolabel(rects1)
    autolabel(rects2)
    
    # 5. Scientific Annotation
    ax.text(50, 4.5, "Conference Standard: 300 DPI | Single-Column Width", 
            style='italic', fontsize=10, ha='center', alpha=0.7)
    
    plt.tight_layout()
    
    # 6. Save in Multiple Formats
    save_figure('ablation_study_final', fig)
    print("OK Success: High-resolution ablation figure saved.")

if __name__ == "__main__":
    generate_ablation_figure()
