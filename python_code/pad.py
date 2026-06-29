import numpy as np

def pad(*args):
    if len(args) == 0:
        raise ValueError("Too few inputs!")
    
    X = np.asarray(args[0])
    ndim = X.ndim
    
    # defaults
    M = np.ones(ndim, dtype=int)
    N = np.ones(ndim, dtype=int)
    E = 0.0
    
    M_val = 1
    if len(args) > 1:
        M_val = args[1]
    
    if np.isscalar(M_val):
        M = np.full(ndim, M_val, dtype=int)
    else:
        M = np.asarray(M_val, dtype=int).copy()
        
    N = M.copy()
    
    flagN = False
    flagA = False
    i = 2
    while i < len(args):
        arg = args[i]
        if arg == 'a':
            if flagN:
                raise ValueError("Assimetric mode cannot be used together with [Mi] and [Ni] or fixed size.")
            # asymmetric mode: MATLAB ceil(M/2) and floor(N/2)
            # wait, MATLAB N=M copy, then M = ceil(M/2), N = floor(N/2)
            # note that in MATLAB: size(Y) = size(X) + [Mi]
            # so the total padding added is indeed M_original
            # N_new = floor(M_original/2), M_new = ceil(M_original/2)
            N = np.floor(N / 2).astype(int)
            M = np.ceil(M / 2).astype(int)
            flagA = True
            i += 1
        elif arg == 'e':
            E = args[i+1]
            i += 2
        elif arg == 'size':
            # args[1] is target size
            target_size = np.asarray(args[1], dtype=int)
            if target_size.ndim == 0:
                target_size = np.full(ndim, target_size.item())
            diff = target_size - np.array(X.shape)
            if np.any(diff < 0):
                raise ValueError("Cannot specify a size smaller than size(X).")
            M = np.ceil(diff / 2).astype(int)
            N = np.floor(diff / 2).astype(int)
            flagN = True
            if flagA:
                raise ValueError("Cannot use asymmetric mode and fix size.")
            i += 1
        else:
            # this is Ni
            N_val = arg
            if np.isscalar(N_val):
                N = np.full(ndim, N_val, dtype=int)
            else:
                N = np.asarray(N_val, dtype=int).copy()
            flagN = True
            i += 1

    if len(M) != ndim or len(N) != ndim:
        raise ValueError("[Mi], [Ni] and [Si] must have length equal to ndims(X).")
        
    pad_width = [(N[d], M[d]) for d in range(ndim)]
    return np.pad(X, pad_width, mode='constant', constant_values=E)
