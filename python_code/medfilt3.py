import numpy as np
import scipy.ndimage

def medfilt3(A, siz=None, padopt='replicate', chunkfactor=1):
    A = np.asarray(A)
    ndim = A.ndim
    
    if A.size == 0:
        return A.copy()
    if A.size == 1:
        return A.copy()
        
    if siz is None:
        if ndim == 1:
            siz = 3
        else:
            siz = [3] * ndim
            
    # Convert siz to size tuple matching ndim
    if np.isscalar(siz):
        size_tuple = (int(siz),) * ndim
    else:
        # siz is list/array
        size_list = list(siz)
        if len(size_list) < ndim:
            size_list = size_list + [1] * (ndim - len(size_list))
        elif len(size_list) > ndim:
            size_list = size_list[:ndim]
        size_tuple = tuple(int(x) for x in size_list)
        
    # Map padopt
    if isinstance(padopt, str):
        padopt_lower = padopt.lower()
        if padopt_lower == 'replicate':
            mode = 'nearest'
            cval = 0.0
        elif padopt_lower == 'symmetric':
            mode = 'reflect'
            cval = 0.0
        elif padopt_lower == 'circular':
            mode = 'wrap'
            cval = 0.0
        else:
            mode = 'nearest'
            cval = 0.0
    else:
        mode = 'constant'
        cval = float(padopt)
        
    # Check for NaNs
    if np.any(np.isnan(A)):
        # Treat NaNs as missing values using np.nanmedian
        def nan_median_func(buffer):
            return np.nanmedian(buffer)
        return scipy.ndimage.generic_filter(A, nan_median_func, size=size_tuple, mode=mode, cval=cval)
    else:
        return scipy.ndimage.median_filter(A, size=size_tuple, mode=mode, cval=cval)
