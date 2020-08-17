from mpl_toolkits import mplot3d
import numpy as np
import matplotlib.pyplot as plt

if __name__ == "__main__":
    x = np.outer(np.linspace(0, 1, 20), np.ones(20))
    y = x.copy().T  # transpose
    z = np.min(np.dstack((x, y)), 2)
    #z = np.max(np.dstack((np.zeros((20, 20)), x + y - 1)), 2)

    fig = plt.figure()
    ax = plt.axes(projection='3d')
    ax.set_zlim(0.0, 1.0)
    ax.set_ylim(0.0, 1.0)
    ax.set_xlim(0.0, 1.0)

    ax.plot_surface(x, y, z, cmap='winter_r', edgecolor='black')
    ax.set_title('Minimum t-norm')
    ax.set_xlabel('a')
    ax.set_ylabel('b')
    ax.set_zlabel('a AND b')
    plt.show()