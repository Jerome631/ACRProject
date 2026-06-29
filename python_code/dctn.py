import numpy as np

def shiftdim(A, n):
    ndim = A.ndim
    if ndim <= 1:
        return A
    n = n % ndim
    axes = list(range(n, ndim)) + list(range(0, n))
    return np.transpose(A, axes)

def dctn(y, w=None):
    y = np.asarray(y, dtype=float)
    sizy = y.shape
    
    # Squeeze
    y_squeezed = np.squeeze(y)
    
    # Handle scalar or single-element array
    if y_squeezed.ndim == 0:
        return y.astype(float), w

    if y_squeezed.ndim == 1:
        dimy = 1
        # Make column vector equivalent
        y_squeezed = y_squeezed.reshape(-1, 1)
    else:
        dimy = y_squeezed.ndim

    if w is None:
        w = [None] * dimy
        for dim in range(dimy):
            # n = (dimy==1)*numel(y) + (dimy>1)*sizy(dim);
            if dimy == 1:
                n = y.size
            else:
                n = sizy[dim]
            w[dim] = np.exp(1j * np.arange(n) * np.pi / (2 * n))

    if not np.isrealobj(y_squeezed):
        real_dct, _ = dctn(np.real(y_squeezed), w)
        imag_dct, _ = dctn(np.imag(y_squeezed), w)
        y_squeezed = real_dct + 1j * imag_dct
    else:
        for dim in range(dimy):
            n = y_squeezed.shape[0]
            idx = np.concatenate([np.arange(0, n, 2), np.arange(2 * (n // 2) - 1, 0, -2)])
            y_squeezed = y_squeezed[idx, ...]
            
            orig_shape = y_squeezed.shape
            y_squeezed = y_squeezed.reshape(n, -1)
            y_squeezed = y_squeezed * np.sqrt(2 * n)
            
            # ifft along axis 0
            y_squeezed = np.fft.ifft(y_squeezed, axis=0)
            # multiply by w[dim]
            y_squeezed = y_squeezed * w[dim][:, np.newaxis]
            y_squeezed = np.real(y_squeezed)
            y_squeezed[0, ...] = y_squeezed[0, ...] / np.sqrt(2)
            
            y_squeezed = y_squeezed.reshape(orig_shape)
            y_squeezed = shiftdim(y_squeezed, 1)

    y_out = y_squeezed.reshape(sizy)
    return y_out, w
