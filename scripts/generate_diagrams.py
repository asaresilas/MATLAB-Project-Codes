
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def draw_block_diagram(filename):
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 8)
    ax.axis('off')

    # Define box styles
    box_props = dict(boxstyle='round,pad=0.5', facecolor='lightblue', edgecolor='black')
    arrow_props = dict(facecolor='black', arrowstyle='->', linewidth=1.5)

    # Nodes
    ax.text(2, 6, "Sensors / CAD Simulation\n(Physical/Virtual System)", ha='center', va='center', bbox=box_props, fontsize=10)
    ax.text(6, 6, "Data Acquisition\n(DAQ)", ha='center', va='center', bbox=box_props, fontsize=10)
    ax.text(10, 6, "API Input\n(Raw Signals/Images)", ha='center', va='center', bbox=box_props, fontsize=10)

    ax.text(6, 4, "Predictive Maintenance Engine\n(Python Deep Learning)", ha='center', va='center', bbox=dict(boxstyle='round,pad=0.5', facecolor='lightgreen', edgecolor='black'), fontsize=12, fontweight='bold')
    
    ax.text(2, 2, "Fault Class / RUL\n(API Response)", ha='center', va='center', bbox=box_props, fontsize=10)
    ax.text(6, 2, "MATLAB Digital Twin\n(Integration)", ha='center', va='center', bbox=box_props, fontsize=10)
    ax.text(10, 2, "Visualization & UI\n(Simulation)", ha='center', va='center', bbox=box_props, fontsize=10)

    # Edges
    ax.annotate("", xy=(4.5, 6), xytext=(3.5, 6), arrowprops=arrow_props)
    ax.annotate("", xy=(8.5, 6), xytext=(7.5, 6), arrowprops=arrow_props)
    
    ax.annotate("", xy=(6, 5), xytext=(10, 5.5), arrowprops=dict(facecolor='black', arrowstyle='->', connectionstyle="arc3,rad=0.2"))
    
    ax.annotate("", xy=(2, 3), xytext=(6, 3.5), arrowprops=dict(facecolor='black', arrowstyle='->', connectionstyle="arc3,rad=0.2"))
    
    ax.annotate("", xy=(4.5, 2), xytext=(3.5, 2), arrowprops=arrow_props)
    ax.annotate("", xy=(8.5, 2), xytext=(7.5, 2), arrowprops=arrow_props)

    plt.title("System Block Diagram", fontsize=16)
    plt.tight_layout()
    plt.savefig(filename, dpi=300)
    print(f"Saved {filename}")
    plt.close()

def draw_flow_chart(filename):
    fig, ax = plt.subplots(figsize=(10, 12))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 12)
    ax.axis('off')

    box_props = dict(boxstyle='round,pad=0.5', facecolor='white', edgecolor='black')
    decision_props = dict(boxstyle='sawtooth,pad=0.5', facecolor='lightyellow', edgecolor='black')
    start_props = dict(boxstyle='circle,pad=0.5', facecolor='lightgray', edgecolor='black')
    arrow_props = dict(facecolor='black', arrowstyle='->', linewidth=1.5)

    # Nodes
    ax.text(5, 11, "Start", ha='center', va='center', bbox=start_props, fontsize=10)
    ax.text(5, 9.5, "Load Sensor Data", ha='center', va='center', bbox=box_props, fontsize=10)
    ax.text(5, 8, "Check Dataset Type?", ha='center', va='center', bbox=decision_props, fontsize=10)
    
    ax.text(2, 6.5, "Induction:\nFeature Extraction", ha='center', va='center', bbox=box_props, fontsize=9)
    ax.text(5, 6.5, "Thermal:\nImage Norm.", ha='center', va='center', bbox=box_props, fontsize=9)
    ax.text(8, 6.5, "Vibration:\nSignal Proc.", ha='center', va='center', bbox=box_props, fontsize=9)
    
    ax.text(5, 5, "Load Optimized DL Model", ha='center', va='center', bbox=box_props, fontsize=10)
    ax.text(5, 3.5, "Generate Prediction", ha='center', va='center', bbox=box_props, fontsize=10)
    ax.text(5, 2, "Confidence Check\n> 96%?", ha='center', va='center', bbox=decision_props, fontsize=10)
    
    ax.text(2, 0.5, "Flag for Review", ha='center', va='center', bbox=box_props, fontsize=9)
    ax.text(8, 0.5, "Return Result\nto Digital Twin", ha='center', va='center', bbox=box_props, fontsize=9)

    # Edges
    ax.annotate("", xy=(5, 10), xytext=(5, 10.5), arrowprops=arrow_props)
    ax.annotate("", xy=(5, 8.5), xytext=(5, 9), arrowprops=arrow_props)
    
    ax.annotate("", xy=(2, 7), xytext=(4, 8), arrowprops=arrow_props)
    ax.annotate("", xy=(5, 7), xytext=(5, 7.5), arrowprops=arrow_props)
    ax.annotate("", xy=(8, 7), xytext=(6, 8), arrowprops=arrow_props)
    
    ax.annotate("", xy=(5, 5.5), xytext=(2, 6), arrowprops=arrow_props)
    ax.annotate("", xy=(5, 5.5), xytext=(5, 6), arrowprops=arrow_props)
    ax.annotate("", xy=(5, 5.5), xytext=(8, 6), arrowprops=arrow_props)
    
    ax.annotate("", xy=(5, 4), xytext=(5, 4.5), arrowprops=arrow_props)
    ax.annotate("", xy=(5, 2.5), xytext=(5, 3), arrowprops=arrow_props)
    
    ax.annotate("No", xy=(2, 1), xytext=(4, 2), arrowprops=arrow_props)
    ax.annotate("Yes", xy=(8, 1), xytext=(6, 2), arrowprops=arrow_props)

    plt.title("System Process Flow Chart", fontsize=16)
    plt.tight_layout()
    plt.savefig(filename, dpi=300)
    print(f"Saved {filename}")
    plt.close()

if __name__ == "__main__":
    draw_block_diagram("System_Block_Diagram.png")
    draw_flow_chart("System_Flow_Chart.png")
