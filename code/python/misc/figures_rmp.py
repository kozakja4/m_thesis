import numpy as np
import matplotlib.pyplot as plt
from matplotlib.collections import PatchCollection
from matplotlib.patches import Polygon


def calc_a():
    # a(x,y) OR NOT a(y,x), domain size = 3, unique name assmptn
    table = []
    init = [0,0,0,0,0,0]

    def traverse(ix):
        if ix == 6:
            table.append(init.copy())
            return
        traverse(ix + 1)
        init[ix] = 1 if init[ix] == 0 else 0
        traverse(ix + 1)
    traverse(0)
    pairs = set()
    for val in table:
        a_ok = sum(val)
        phi_ok = 6
        for i in range(3):
            if val[2 * i] != val[2 * i + 1]:
                phi_ok -= 1
        pairs.add((a_ok, phi_ok))
    return pairs


def calc_b():
    # a(x,y) OR NOT a(y,x), domain size = 3, unique name assmptn
    table = []
    init = [0,0,0,0,0,0]

    def traverse(ix):
        if ix == 6:
            table.append(init.copy())
            return
        traverse(ix + 1)
        init[ix] = 1 if init[ix] == 0 else 0
        traverse(ix + 1)
    traverse(0)
    pairs = set()
    for val in table:
        a_ok = sum(val)
        phi_ok = 0
        for i in range(3):
            if val[2 * i] == val[2 * i + 1] == 1:
                phi_ok += 2
        pairs.add((a_ok, phi_ok))
    return pairs


if __name__ == "__main__":
    fig, (ax, ax2) = plt.subplots(1, 2)

    v1 = np.array([1, 1])
    v2 = np.array([0.5, 0.5])
    v3 = np.array([0, 1])
    polygon = Polygon([v1, v2, v3], True)
    p = PatchCollection([polygon], alpha=0.4)

    ax.add_collection(p)
    ax.set_xlim([0, 1])
    ax.set_ylim([0, 1])
    pairs = calc_a()
    ax.plot([x[0] / 6 for x in pairs], [x[1] / 6 for x in pairs], "ro", clip_on=False)

    ax.set_xlabel(r'$p(A)$')
    ax.set_ylabel(r'$p(\phi)$')

    v4 = np.array([1, 1])
    v5 = np.array([0.5, 0])
    v6 = np.array([0, 0])
    polygon = Polygon([v4, v5, v6], True)
    p = PatchCollection([polygon], alpha=0.4)

    ax2.add_collection(p)
    ax2.set_xlim([0, 1])
    ax2.set_ylim([0, 1])

    pairs = calc_b()
    ax2.plot([x[0] / 6 for x in pairs], [x[1] / 6 for x in pairs], "ro", clip_on=False)

    ax2.set_xlabel(r'$p(B)$')
    ax2.set_ylabel(r'$p(\psi)$')

    ax.set_aspect('equal')
    ax2.set_aspect('equal')
    plt.show()
