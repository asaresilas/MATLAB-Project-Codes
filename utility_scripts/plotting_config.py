import os

import matplotlib.pyplot as plt
import seaborn as sns


def apply_publication_style():
    """
    Apply a publication-oriented plotting style with vector-friendly defaults.
    """
    plt.style.use("default")
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Times New Roman", "DejaVu Serif"],
            "font.size": 10,
            "axes.labelsize": 12,
            "axes.titlesize": 13,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
            "legend.fontsize": 10,
            "figure.dpi": 600,
            "savefig.dpi": 600,
            "axes.grid": True,
            "grid.alpha": 0.2,
            "grid.linestyle": "--",
            "axes.facecolor": "white",
            "axes.edgecolor": "black",
            "axes.linewidth": 1.5,
            "figure.facecolor": "white",
            "legend.frameon": True,
            "legend.edgecolor": "black",
            "legend.fancybox": False,
            "figure.figsize": (6.0, 8.0), # Exact 1800x2400 pixels at 300 DPI
        }
    )
    sns.set_palette("muted")


def save_figure(name, fig=None, output_dir="results/publication_figures"):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    if fig is None:
        fig = plt.gcf()

    png_path = os.path.join(output_dir, f"{name}.png")
    pdf_path = os.path.join(output_dir, f"{name}.pdf")

    try:
        fig.savefig(png_path, dpi=600, bbox_inches="tight", transparent=False)
        fig.savefig(pdf_path, bbox_inches="tight")
        print(f"Saved figure: {name}.png")
    except PermissionError:
        alt_png_path = os.path.join(output_dir, f"{name}_updated.png")
        alt_pdf_path = os.path.join(output_dir, f"{name}_updated.pdf")
        fig.savefig(alt_png_path, dpi=300, bbox_inches="tight", transparent=False)
        fig.savefig(alt_pdf_path, bbox_inches="tight")
        print(f"Saved figure with alternate name: {name}_updated.png")


if __name__ == "__main__":
    apply_publication_style()
    plt.plot([1, 2, 3], [1, 4, 9], label="Test Data")
    plt.title("Sample Conference Plot")
    plt.xlabel("Time (s)")
    plt.ylabel("Amplitude")
    plt.legend()
    save_figure("style_test")
