import numpy as np
import matplotlib.pyplot as plt


if __name__ == "__main__":
    xlist = np.linspace(0.0, 1.0, 1000)
    ylist = np.linspace(0.0, 1.0, 1000)
    x, y = np.meshgrid(xlist, ylist)
    # Z = np.min(np.dstack((x, y)), 2)
    Z = np.max(np.dstack((np.zeros((1000, 1000)), x + y - 1)), 2)
    fig, ax = plt.subplots(1, 1)
    cp = ax.contour(x, y, Z, levels=np.linspace(0.0, 1.0, 21), cmap='winter_r')
    fig.colorbar(cp) # Add a colorbar to a plot
    ax.set_title('Minimum t-norm')
    ax.set_xlabel('a')
    ax.set_ylabel('b')
    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(0.0, 1.0)
    plt.show()