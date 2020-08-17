import numpy as np
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection, Line3DCollection
import matplotlib.pyplot as plt


if __name__ == "__main__":
    fig = plt.figure()
    ax = Axes3D(fig)
    ax.set_zlim(0.0, 1.0)
    ax.set_ylim(0.0, 1.0)
    ax.set_xlim(0.0, 1.0)

    v1 = np.array([1, 1, 1])
    v2 = np.array([1, 0, 0])
    v3 = np.array([0, 1, 1])
    v4 = np.array([0, 1, 0])

    ax.add_collection3d(Line3DCollection([(v2, v4)], linestyles='dashed',  color='black', linewidth=1))
    ax.add_collection3d(Line3DCollection([(v1, v4, v3)], linestyles='dashed',  color='black', linewidth=1))
    #ax.add_collection3d(Poly3DCollection([v1, v2, v3], alpha=0.4))
    #ax.add_collection3d(Poly3DCollection([v1, v2, v4], alpha=0.4))
    #ax.add_collection3d(Poly3DCollection([v1, v3, v4], alpha=0.4))
    #ax.add_collection3d(Poly3DCollection([v2, v3, v4], alpha=0.4))
    ax.add_collection3d(Line3DCollection([(v1, v2, v3, v1)], color='black',  linewidth=1))

    #ax.add_collection3d(Line3DCollection([((0.7, 0, 0), (0.7, 1, 0), (0.7, 1, 1), (0.7, 0, 1), (0.7, 0, 0))],
    #                                     color='black', linewidth=0.5))
    #ax.add_collection3d(Line3DCollection([((0, 0.6, 0), (1, 0.6, 0), (1, 0.6, 1), (0, 0.6, 1), (0, 0.6, 0))],
    #                                     color='black', linewidth=0.5))

    ax.add_collection3d(Line3DCollection([((0.6, 0.7, 0.3), (0.6, 0.7, 0.7))],
                                         color='red', linewidth=3))
    ax.add_collection3d(Poly3DCollection([[(0.3, 0.7, 0), (0.3, 0.7, 0.7), (1, 0.7, 0.7)]],
                                         color='orange', alpha=0.05))
    ax.add_collection3d(Poly3DCollection([[(0.6, 1, 1), (0.6, 1, 0.6), (0.6, 0.4, 0), (0.6, 0.4, 0.4)]],
                                         color='blue', alpha=0.05))



    ax.set_title('Polytope of admissible values')
    ax.set_xlabel(r'$\pi_1$')
    ax.set_ylabel(r'$\pi_2$')
    ax.set_zlabel(r'$\pi_3$')
    plt.show()
