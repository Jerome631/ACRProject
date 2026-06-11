import numpy as np
from dctn import shiftdim

def idctn(y, w=None):
    y = np.asarray(y, dtype=float)
    sizy = y.shape
    
    # Squeeze
    y_squeezed = np.squeeze(y)
    
    if y_squeezed.ndim == 0:
        return y.astype(float), w

    if y_squeezed.ndim == 1:
        dimy = 1
        y_squeezed = y_squeezed.reshape(-1, 1)
    else:
        dimy = y_squeezed.ndim

    if w is None:
        w = [None] * dimy
        for dim in range(dimy):
            if dimy == 1:
                n = y.size
            else:
                n = sizy[dim]
            w[dim] = np.exp(1j * np.arange(n) * np.pi / (2 * n))

    # In idctn, the input y can be complex.
    # But wait, even if y is real, y * w[dim] makes it complex!
    # Let's check:
    # If the input y is complex initially (e.g. from complex operations),
    # we decompose into real and imaginary parts.
    # Otherwise, we do the computation. Note that the computation uses complex arrays
    # internally (because w{dim} is complex) and then takes the real part.
    # Therefore, we should only branch if the input y starts as complex.
    if np.iscomplexobj(y_squeezed):
        real_idct, _ = idctn(np.real(y_squeezed), w)
        imag_idct, _ = idctn(np.imag(y_squeezed), w)
        y_squeezed = real_idct + 1j * imag_idct
    else:
        for dim in range(dimy):
            n = y_squeezed.shape[0]
            orig_shape = y_squeezed.shape
            y_squeezed = y_squeezed.reshape(n, -1)
            
            # y = bsxfun(@times,y,w{dim});
            y_comp = y_squeezed * w[dim][:, np.newaxis]
            y_comp[0, ...] = y_comp[0, ...] / np.sqrt(2)
            
            # y = ifft(y,[],1);
            y_comp = np.fft.ifft(y_comp, axis=0)
            
            # y = real(y*sqrt(2*n));
            y_squeezed = np.real(y_comp * np.sqrt(2 * n))
            
            # Reorder indices:
            # I = (1:n)*0.5+0.5;
            # I(2:2:end) = n-I(1:2:end-1)+1;
            idx = np.empty(n, dtype=int)
            idx[0::2] = np.arange(0, (n + 1) // 2)
            idx[1::2] = np.arange(n - 1, n - 1 - n // 2, -1)
            
            y_squeezed = y_squeezed[idx, ...]
            
            y_squeezed = y_squeezed.reshape(orig_shape)
            y_squeezed = shiftdim(y_squeezed, 1)

    y_out = y_squeezed.reshape(sizy)
    return y_out, w
