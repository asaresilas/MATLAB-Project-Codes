import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def draw_inference_pipeline(filename):
    fig, ax = plt.subplots(figsize=(10, 14))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 14)
    ax.axis('off')

    # Define styles
    tensor_style = dict(boxstyle='round,pad=0.5', facecolor='#d6eaf8', edgecolor='#21618c', linewidth=2)
    layer_style = dict(boxstyle='square,pad=0.5', facecolor='#abebc6', edgecolor='#1d8348', linewidth=2)
    attn_style = dict(boxstyle='round,pad=0.5', facecolor='#fcf3cf', edgecolor='#d4ac0d', linewidth=2)
    pool_style = dict(boxstyle='square,pad=0.5', facecolor='#ebdef0', edgecolor='#76448a', linewidth=2)
    out_style = dict(boxstyle='round4,pad=0.5', facecolor='#f5b7b1', edgecolor='#943126', linewidth=2)
    
    arrow_props = dict(facecolor='black', arrowstyle='->', linewidth=2)

    ax.text(5, 13.2, "Diagram G1-B: Deep Learning Inference Pipeline\n(Data Flow & Tensor Transformations)", 
            ha='center', va='center', fontsize=16, fontweight='bold')

    # --- 1D-CNN Branch (Vibration/Current) ---
    ax.text(2, 11.5, "1D-CNN Pathway\n(Vibration / Current)", fontsize=12, fontweight='bold', ha='center', va='center', color='#154360')
    ax.text(2, 10.5, "Input Tensor\nShape: (2048, 1)", ha='center', va='center', bbox=tensor_style, fontsize=10)
    ax.annotate("", xy=(2, 9.8), xytext=(2, 10.1), arrowprops=arrow_props)
    
    ax.text(2, 9.2, "Conv1D Blocks (x4)\n[Conv -> BN -> MaxPool]", ha='center', va='center', bbox=layer_style, fontsize=10)
    ax.annotate("", xy=(2, 8.5), xytext=(2, 8.8), arrowprops=arrow_props)
    
    ax.text(2, 7.9, "Global Average\nPooling 1D", ha='center', va='center', bbox=pool_style, fontsize=10)
    ax.annotate("", xy=(2, 7.2), xytext=(2, 7.5), arrowprops=arrow_props)

    # --- 2D-CNN Branch (Thermal) ---
    ax.text(5, 11.5, "2D-ResNet Pathway\n(Thermal Imagery)", fontsize=12, fontweight='bold', ha='center', va='center', color='#154360')
    ax.text(5, 10.5, "Input Image\nShape: (224, 224, 3)", ha='center', va='center', bbox=tensor_style, fontsize=10)
    ax.annotate("", xy=(5, 9.8), xytext=(5, 10.1), arrowprops=arrow_props)
    
    ax.text(5, 9.2, "EfficientNetB0 Base\n(Pre-trained Weights)", ha='center', va='center', bbox=layer_style, fontsize=10)
    ax.annotate("", xy=(5, 8.5), xytext=(5, 8.8), arrowprops=arrow_props)
    
    ax.text(5, 7.9, "Global Average\nPooling 2D", ha='center', va='center', bbox=pool_style, fontsize=10)
    ax.annotate("", xy=(5, 7.2), xytext=(5, 7.5), arrowprops=arrow_props)

    # --- Bi-LSTM Branch (NASA Time-Series) ---
    ax.text(8, 11.5, "Bi-LSTM Pathway\n(Sequential Degradation)", fontsize=12, fontweight='bold', ha='center', va='center', color='#154360')
    ax.text(8, 10.5, "Input Sequence\nShape: (30, 36)", ha='center', va='center', bbox=tensor_style, fontsize=10)
    ax.annotate("", xy=(8, 9.8), xytext=(8, 10.1), arrowprops=arrow_props)
    
    ax.text(8, 9.2, "Bidirectional LSTMs\n(64 -> 32 Units)", ha='center', va='center', bbox=layer_style, fontsize=10)
    ax.annotate("", xy=(8, 8.5), xytext=(8, 8.8), arrowprops=arrow_props)
    
    ax.text(8, 7.9, "Custom Attention\nMechanism", ha='center', va='center', bbox=attn_style, fontsize=10)
    ax.annotate("", xy=(8, 7.2), xytext=(8, 7.5), arrowprops=arrow_props)

    # --- Softmax Layers ---
    ax.text(2, 6.6, "Dense Output\n(Softmax)", ha='center', va='center', bbox=out_style, fontsize=10)
    ax.text(5, 6.6, "Dense Output\n(Softmax)", ha='center', va='center', bbox=out_style, fontsize=10)
    ax.text(8, 6.6, "Dense Output\n(Softmax/Linear)", ha='center', va='center', bbox=out_style, fontsize=10)

    # --- Epistemic Feature Extraction ---
    ax.annotate("", xy=(4.5, 5.2), xytext=(2, 6.0), arrowprops=arrow_props)
    ax.annotate("", xy=(5, 5.2), xytext=(5, 6.0), arrowprops=arrow_props)
    ax.annotate("", xy=(5.5, 5.2), xytext=(8, 6.0), arrowprops=arrow_props)

    ax.text(5, 4.3, "Epistemic Uncertainty Extractor\nMathematical Transformations", ha='center', va='center', bbox=dict(boxstyle='round,pad=0.8', facecolor='#e5e8e8', edgecolor='#5d6d7e', linewidth=2), fontsize=11, fontweight='bold')
    
    # Mathematical equations text
    eq_text = (
        "1. Entropy: $\\mathcal{H}(p) = -\\sum p_i \\log(p_i)$\n"
        "2. Variance: $\\sigma^2 = \\frac{1}{N}\\sum(p_i - \\bar{p})^2$\n"
        "3. Confidence: $\\max(p_i)$"
    )
    ax.text(5, 2.8, eq_text, ha='center', va='center', fontsize=12, bbox=dict(boxstyle='square,pad=0.5', facecolor='white', edgecolor='black'))

    ax.annotate("", xy=(5, 1.6), xytext=(5, 2.0), arrowprops=arrow_props)

    ax.text(5, 1.0, "32-Dimensional Meta-Feature Tensor\nShape: (Batch, 32)", ha='center', va='center', bbox=tensor_style, fontsize=11, fontweight='bold')

    plt.tight_layout()
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"Successfully generated {filename} at 300 DPI")
    plt.close()

if __name__ == "__main__":
    output_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results", "publication_figures", "G1-B_Inference_Pipeline.png")
    draw_inference_pipeline(output_path)
