import matplotlib.pyplot as plt
import numpy as np

# Data
labels = ["CK8", "COL1A1", "COL3A1", "ELN", "Ki67", "SMA", "SMTN", "UPK2"]
means = [0.682121547, 3.556771411, 1.030590035, 1.621001522,
         1.042606414, 1.109064498, 1.104165846, 1.454265511]
std_dev = [0.180270134, 1.100294255, 0.30704668, 0.7307007,
           0.371506819, 0.129199057, 0.654008534, 0.437220306]

# Create figure
plt.figure(figsize=(8, 6))

# Bar plot with error bars
bars = plt.bar(
    labels,
    means,
    yerr=std_dev,
    capsize=6,
    color="white",
    edgecolor="black",
    linewidth=1.8,
    error_kw=dict(elinewidth=1.5, ecolor="black")
)

# Labels and title
plt.ylabel("Fold Change", fontsize=12)
plt.title("Mean Fold Change ± SD", fontsize=14)

# Rotate x labels for clarity
plt.xticks(rotation=45, ha='right')

# Set y-axis starting at 0 (typical Prism style)
plt.ylim(0, max(means) + max(std_dev) + 0.5)

# Remove top and right borders (Prism-like style)
ax = plt.gca()
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_linewidth(1.5)
ax.spines["bottom"].set_linewidth(1.5)

plt.tight_layout()
plt.show()