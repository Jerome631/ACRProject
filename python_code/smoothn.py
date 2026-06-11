import numpy as np
import scipy.ndimage
from scipy.optimize import fminbound
from dctn import dctn
from idctn import idctn

def smoothn(y, s=None, W=None, robust=False, TolZ=1e-3, MaxIter=100, over=False, under=False):
    y = np.asarray(y, dtype=float)
    sizy = y.shape
    noe = y.size
    
    if noe < 2:
        return y.copy(), s, True

    if W is None:
        W = np.ones(sizy, dtype=float)
    else:
        W = np.asarray(W, dtype=float).copy()
        
    if s is not None:
        s = float(s)
        if s < 0:
            raise ValueError("The smoothing parameter must be >= 0")

    IsFinite = np.isfinite(y)
    nof = np.sum(IsFinite)
    W = W * IsFinite
    
    if np.any(W < 0):
        raise ValueError("Weights must all be >= 0")
    else:
        w_max = np.max(W)
        if w_max > 0:
            W = W / w_max

    isweighted = np.any(W < 1)
    isauto = (s is None)

    # 1. Lambda tensor
    d = y.ndim
    Lambda = np.zeros(sizy)
    for i in range(d):
        shape = [1] * d
        shape[i] = sizy[i]
        arr = np.cos(np.pi * np.arange(sizy[i]).reshape(shape) / sizy[i])
        Lambda = Lambda + arr
    Lambda = -2 * (d - Lambda)

    if s is not None:
        Gamma = 1.0 / (1.0 + s * Lambda**2)

    # Upper/lower bounds
    N_rank = np.sum(np.array(sizy) != 1)
    if N_rank == 0:
        N_rank = 1
    hMin = 1e-6
    hMax = 0.99
    sMinBnd = (((1 + np.sqrt(1 + 8 * hMax**(2/N_rank))) / 4 / hMax**(2/N_rank))**2 - 1) / 16
    sMaxBnd = (((1 + np.sqrt(1 + 8 * hMin**(2/N_rank))) / 4 / hMin**(2/N_rank))**2 - 1) / 16

    # 2. Initial guess
    if isweighted:
        z = InitialGuess(y, IsFinite)
    else:
        z = np.zeros(sizy)

    z0 = z.copy()
    y_clean = y.copy()
    y_clean[~IsFinite] = 0.0  # arbitrary value for missing data

    tol = 1.0
    RobustIterativeProcess = True
    RobustStep = 0
    nit = 0
    errp = 0.1
    RF = 1.0 + 0.75 * isweighted

    DCTy = None
    Wtot = W.copy()

    # GCV function
    def gcv(p):
        nonlocal s, Gamma
        s = 10**p
        Gamma = 1.0 / (1.0 + s * Lambda**2)
        if aow > 0.9:
            RSS = np.sum((DCTy * (Gamma - 1.0))**2)
        else:
            yhat, _ = idctn(Gamma * DCTy)
            RSS = np.sum(Wtot[IsFinite] * (y_clean[IsFinite] - yhat[IsFinite])**2)
        TrH = np.sum(Gamma)
        score = RSS / nof / (1.0 - TrH / noe)**2
        return score

    while RobustIterativeProcess:
        aow = np.sum(Wtot) / noe
        
        while tol > TolZ and nit < MaxIter:
            nit += 1
            DCTy, _ = dctn(Wtot * (y_clean - z) + z)
            
            if isauto and (nit == 1 or np.log2(nit).is_integer()):
                # optimize GCV
                opt_p = fminbound(gcv, np.log10(sMinBnd), np.log10(sMaxBnd), xtol=errp)
                s = 10**opt_p
                Gamma = 1.0 / (1.0 + s * Lambda**2)
                
            GammaDCTy = Gamma * DCTy
            z_new, _ = idctn(GammaDCTy)
            z = RF * z_new + (1.0 - RF) * z
            
            if isweighted:
                tol = np.linalg.norm(z0 - z) / np.linalg.norm(z)
            else:
                tol = 0.0
                
            z0 = z.copy()
            
        exitflag = (nit < MaxIter)
        
        if robust:
            # studentized residuals
            h = np.sqrt(1 + 16 * s)
            h = np.sqrt(1 + h) / np.sqrt(2) / h
            h = h**N_rank
            
            r = y_clean - z
            MAD = np.median(np.abs(r[IsFinite] - np.median(r[IsFinite])))
            if MAD == 0:
                MAD = 1e-6
            u = np.abs(r / (1.4826 * MAD) / np.sqrt(1.0 - h))
            c = 4.685
            RobustW = (1.0 - (u / c)**2)**2 * (u / c < 1.0)
            RobustW[np.isnan(RobustW)] = 0.0
            
            Wtot = W * RobustW
            isweighted = True
            tol = 1.0
            nit = 0
            RobustStep += 1
            RobustIterativeProcess = (RobustStep < 3)
        else:
            RobustIterativeProcess = False

    if under or over:
        s = s / 100.0 if under else s * 100.0
        Gamma = 1.0 / (1.0 + s * Lambda**2)
        GammaDCTy = Gamma * DCTy
        z, _ = idctn(GammaDCTy)

    return z, s, exitflag

def InitialGuess(y, I):
    z = y.copy()
    if np.any(~I):
        # bwdist equivalent
        distances, indices = scipy.ndimage.distance_transform_edt(~I, return_indices=True)
        coords = tuple(indices[dim][~I] for dim in range(y.ndim))
        z[~I] = y[coords]
        
    # fast coarse smoothing
    sizy = z.shape
    z, _ = dctn(z)
    for k in range(z.ndim):
        cutoff = int(np.ceil(sizy[k] / 10))
        slices = [slice(None)] * z.ndim
        slices[k] = slice(cutoff, None)
        z[tuple(slices)] = 0.0
    z, _ = idctn(z)
    return z
