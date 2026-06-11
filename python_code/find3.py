import numpy as np

def find3(arr):
    arr = np.asarray(arr)
    x, y, z = np.nonzero(arr)
    v = arr[x, y, z].astype(float)
    return x, y, z, v
