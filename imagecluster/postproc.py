import os
import shutil
from typing import Dict, Sequence, Optional, Any

from matplotlib import pyplot as plt
import numpy as np

from . import calc as ic

pj = os.path.join


def plot_clusters(
        clusters,
        images,
        max_csize: Optional[int] = None,
        mem_limit: int = 1024**3,
        n_examples: Optional[int] = None
):
    """Plot `clusters` of images in `images`.

    For interactive work, use :func:`visualize` instead.

    Parameters
    ----------
    clusters : see :func:`~imagecluster.calc.cluster`
    images : see :func:`~imagecluster.io.read_images`
    max_csize : int
        plot clusters with at most this many images
    mem_limit : float or int, bytes
        hard memory limit for the plot array (default: 1 GiB), increase if you
        have (i) enough memory, (ii) many clusters and/or (iii) large
        max(csize) and (iv) max_csize is large or None
    n_examples : int, optional
        show max n image examples from each cluster
    """
    assert len(clusters) > 0, "`clusters` is empty"

    stats = ic.cluster_stats(clusters)
    if max_csize is not None:
        stats = stats[stats[:, 0] <= max_csize, :]

    # number of clusters
    n_columns = stats[:, 1].sum()

    # cluster_size (number of images per cluster)
    max_rows = stats[:, 0].max()
    n_rows = max_rows if (n_examples is None) else min(n_examples, max_rows)

    # image shape
    shape = images[list(images.keys())[0]].shape[:2]

    # memory check
    mem = n_rows * shape[0] * n_columns * shape[1] * 3
    if mem > mem_limit:
        raise Exception(
            f"size of plot array ({mem/1024**2} MiB) > mem_limit ({mem_limit/1024**2} MiB)"
        )

    # uint8 has range 0..255, perfect for images represented as integers, makes
    # rather big arrays possible
    clusters_image = np.ones((n_rows*shape[0], n_columns*shape[1], 3), dtype=np.uint8) * 255
    column_idx = -1
    for cluster_size in stats[:, 0]:
        for cluster in clusters[cluster_size]:
            column_idx += 1
            for row_idx, filename in enumerate(cluster):
                if row_idx >= n_rows:
                    break

                image = images[filename]
                row_min = row_idx * shape[0]
                row_max = (row_idx + 1) * shape[0]
                column_min = column_idx * shape[1]
                column_max = (column_idx + 1) * shape[1]
                clusters_image[row_min:row_max, column_min:column_max, :] = image

    print(f"plot array ({clusters_image.dtype}) size: {clusters_image.nbytes/1024**2} MiB")
    fig, ax = plt.subplots()
    ax.imshow(clusters_image)
    ax.axis('off')
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)

    return fig, ax


def visualize(*args, **kwds):
    """Interactive wrapper of :func:`plot_clusters`. Just calls ``plt.show`` at
    the end. Doesn't return ``fig,ax``.
    """
    plot_clusters(*args, **kwds)
    plt.show()


def make_links(clusters, cluster_dr):
    """In `cluster_dr`, create nested dirs with symlinks to image files
    representing `clusters`.

    Parameters
    ----------
    clusters : see :func:`~imagecluster.calc.cluster`
    cluster_dr : str
        path
    """
    print("cluster dir: {}".format(cluster_dr))
    if os.path.exists(cluster_dr):
        shutil.rmtree(cluster_dr)
    for csize, group in clusters.items():
        for iclus, cluster in enumerate(group):
            dr = pj(cluster_dr,
                    'cluster_with_{}'.format(csize),
                    'cluster_{}'.format(iclus))
            for fn in cluster:
                link = pj(dr, os.path.basename(fn))
                os.makedirs(os.path.dirname(link), exist_ok=True)
                os.symlink(os.path.abspath(fn), link)
