import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def draw_system_architecture(filename):
    fig, ax = plt.subplots(figsize=(10, 13))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 13)
    ax.axis('off')

    # Define styles
    simulink_style = dict(boxstyle='round,pad=0.7', facecolor='#eaf2f8', edgecolor='#154360', linewidth=2.5)
    asset_style = dict(boxstyle='round4,pad=0.6', facecolor='#e8f4f8', edgecolor='#2980b9', linewidth=2)
    expert_style = dict(boxstyle='round,pad=0.5', facecolor='#eafaf1', edgecolor='#27ae60', linewidth=2)
    fusion_style = dict(boxstyle='round,pad=0.6', facecolor='#fef9e7', edgecolor='#f39c12', linewidth=2)
    output_style = dict(boxstyle='round,pad=0.6', facecolor='#fdedec', edgecolor='#c0392b', linewidth=2)
    arrow_props = dict(facecolor='black', arrowstyle='->', linewidth=2)

    ax.text(5, 12.2, "Diagram G1-A: Overall System Architecture\nDecision-Level Expert Fusion Framework", 
            ha='center', va='center', fontsize=16, fontweight='bold')

    # 0. MATLAB Simulink Integration
    ax.text(5, 10.8, "MATLAB Simulink Virtual Motor Model\n(Physics-Based Simulation & Data Acquisition)", ha='center', va='center', bbox=simulink_style, fontsize=12, fontweight='bold')
    
    # 1. Physical / Simulated Signals
    ax.text(2, 9.2, "Vibration\nSignals\n(CWRU/Ind)", ha='center', va='center', bbox=asset_style, fontsize=11, fontweight='bold')
    ax.text(5, 9.2, "Thermal\nImagery\n(Infrared)", ha='center', va='center', bbox=asset_style, fontsize=11, fontweight='bold')
    ax.text(8, 9.2, "Electrical\nSignatures\n(3-Phase)", ha='center', va='center', bbox=asset_style, fontsize=11, fontweight='bold')

    # 2. Local Experts
    ax.text(5, 7.9, "Modality-Specific Deep Learning Experts", ha='center', va='center', fontsize=12, style='italic', color='#7f8c8d')
    ax.text(2, 7.2, "1D-CNN\nFeature Extractor", ha='center', va='center', bbox=expert_style, fontsize=11)
    ax.text(5, 7.2, "2D-EfficientNet\nSpatial Extractor", ha='center', va='center', bbox=expert_style, fontsize=11)
    ax.text(8, 7.2, "Bi-LSTM Attention\nTemporal Extractor", ha='center', va='center', bbox=expert_style, fontsize=11)

    # 3. Uncertainty Profiles
    ax.text(5, 5.2, "Epistemic Uncertainty Mapping\n(Probabilities, Entropy, Variance)", ha='center', va='center', bbox=dict(boxstyle='round,pad=0.5', facecolor='white', edgecolor='#34495e', linestyle='--', linewidth=1.5), fontsize=11, fontweight='bold')

    # 4. Meta-Fusion
    ax.text(5, 3.2, "Virtual Hybrid Asset Alignment\n&\nXGBoost Meta-Learner", ha='center', va='center', bbox=fusion_style, fontsize=12, fontweight='bold')

    # 5. Output
    ax.text(3, 1.2, "Severity State\n(Healthy/Warn/Critical)", ha='center', va='center', bbox=output_style, fontsize=11, fontweight='bold')
    ax.text(7, 1.2, "RUL Estimation\n(Hours Remaining)", ha='center', va='center', bbox=output_style, fontsize=11, fontweight='bold')

    # Draw Arrows
    # Simulink to Signals
    ax.annotate("", xy=(2, 9.8), xytext=(4, 10.4), arrowprops=arrow_props)
    ax.annotate("", xy=(5, 9.8), xytext=(5, 10.4), arrowprops=arrow_props)
    ax.annotate("", xy=(8, 9.8), xytext=(6, 10.4), arrowprops=arrow_props)

    # Data to Experts
    ax.annotate("", xy=(2, 7.9), xytext=(2, 8.6), arrowprops=arrow_props)
    ax.annotate("", xy=(5, 7.9), xytext=(5, 8.6), arrowprops=arrow_props)
    ax.annotate("", xy=(8, 7.9), xytext=(8, 8.6), arrowprops=arrow_props)

    # Experts to Uncertainty
    ax.annotate("", xy=(4, 5.7), xytext=(2, 6.6), arrowprops=arrow_props)
    ax.annotate("", xy=(5, 5.7), xytext=(5, 6.6), arrowprops=arrow_props)
    ax.annotate("", xy=(6, 5.7), xytext=(8, 6.6), arrowprops=arrow_props)

    # Uncertainty to Fusion
    ax.annotate("", xy=(5, 4.0), xytext=(5, 4.7), arrowprops=arrow_props)

    # Fusion to Output
    ax.annotate("", xy=(3, 1.8), xytext=(4.5, 2.6), arrowprops=arrow_props)
    ax.annotate("", xy=(7, 1.8), xytext=(5.5, 2.6), arrowprops=arrow_props)

    # Add surrounding Digital Twin Box
    rect = patches.Rectangle((0.5, 0.2), 9, 11.2, linewidth=2, edgecolor='#bdc3c7', facecolor='none', linestyle='-.')
    ax.add_patch(rect)
    ax.text(0.7, 0.4, "MATLAB Web App / Digital Twin UI Framework", fontsize=10, color='#7f8c8d', fontweight='bold')

    plt.tight_layout()
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"Successfully generated {filename} at 300 DPI")
    plt.close()

if __name__ == "__main__":
    output_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results", "publication_figures", "G1-A_System_Architecture.png")
    draw_system_architecture(output_path)
