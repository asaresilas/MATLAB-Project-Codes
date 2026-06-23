import matplotlib.pyplot as plt
import numpy as np
import os

# Ensure output directory exists
os.makedirs('results/publication_figures', exist_ok=True)

def create_thermal_mapping_visual():
    """Generates a high-resolution IEEE-style mapping of physical sensors to the 3x3 Thermal Matrix."""
    fig, ax = plt.subplots(figsize=(8, 8), dpi=600)
    ax.set_xlim(0, 3)
    ax.set_ylim(0, 3)
    
    # Grid Data (Labels)
    grid = [
        ["STATOR", "HOUSING", "STATOR"],
        ["BEARING (DE)", "ROTOR\nSHAFT", "BEARING (NDE)"],
        ["STATOR", "HOUSING", "STATOR"]
    ]
    
    # Draw the 3x3 Grid
    for i in range(3):
        for j in range(3):
            # Color coding (Central source is hotter)
            color = '#ffccbc' if (i==1 and j==1) else '#fff9c4' if (i==1) else '#e1f5fe'
            
            rect = plt.Rectangle((j, 2-i), 1, 1, facecolor=color, edgecolor='black', linewidth=2)
            ax.add_patch(rect)
            
            # Add text
            ax.text(j+0.5, 2-i+0.5, grid[i][j], 
                    ha='center', va='center', fontsize=12, weight='bold', color='#333333')

    # Formatting
    ax.set_xticks([0.5, 1.5, 2.5])
    ax.set_xticklabels(['Drive End', 'Center', 'Non-Drive End'], fontsize=10, weight='bold')
    ax.set_yticks([0.5, 1.5, 2.5])
    ax.set_yticklabels(['Bottom', 'Middle', 'Top'], fontsize=10, weight='bold')
    
    plt.title("DIGITAL TWIN: SPATIAL THERMAL MATRIX MAPPING (3x3)", fontsize=14, weight='bold', pad=20)
    plt.grid(False)
    
    # Save the figure
    save_path = 'results/publication_figures/thermal_mapping.png'
    plt.savefig(save_path, bbox_inches='tight')
    plt.close()
    print(f"OK Thermal Mapping Visual saved to {save_path}")

if __name__ == "__main__":
    create_thermal_mapping_visual()
