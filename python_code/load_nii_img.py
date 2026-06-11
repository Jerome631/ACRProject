import os
import numpy as np
from load_nii_hdr import struct

def load_nii_img(hdr, filetype, fileprefix, machine, img_idx=None, dim5_idx=None, dim6_idx=None, dim7_idx=None, old_RGB=0):
    if filetype in [0, 1]:
        fn = f"{fileprefix}.img"
    else:
        fn = f"{fileprefix}.nii"
        
    if not os.path.exists(fn):
        raise FileNotFoundError(f"Cannot find file {fn}")
        
    endian = '<' if machine == 'ieee-le' else '>'
    
    dt = hdr.dime.datatype
    if dt == 1:
        precision = 'uint8'
        nbits = 1
    elif dt == 2:
        precision = 'uint8'
        nbits = 8
    elif dt == 4:
        precision = 'int16'
        nbits = 16
    elif dt == 8:
        precision = 'int32'
        nbits = 32
    elif dt == 16:
        precision = 'float32'
        nbits = 32
    elif dt == 32:
        precision = 'float32'
        nbits = 64
    elif dt == 64:
        precision = 'float64'
        nbits = 64
    elif dt == 128:
        precision = 'uint8'
        nbits = 24
    elif dt == 256:
        precision = 'int8'
        nbits = 8
    elif dt == 511:
        precision = 'float32'
        nbits = 96
    elif dt == 512:
        precision = 'uint16'
        nbits = 16
    elif dt == 768:
        precision = 'uint32'
        nbits = 32
    elif dt == 1024:
        precision = 'int64'
        nbits = 64
    elif dt == 1280:
        precision = 'uint64'
        nbits = 64
    elif dt == 1792:
        precision = 'float64'
        nbits = 128
    else:
        raise ValueError(f"Datatype {dt} is not supported")
        
    hdr.dime.bitpix = nbits
    
    dims = np.array(hdr.dime.dim)
    dims[dims < 1] = 1
    hdr.dime.dim = dims
    
    d1, d2, d3, d4, d5, d6, d7 = dims[1:8]
    
    img_siz = int(np.prod(dims[1:8]))
    if dt in [32, 1792]:
        img_siz *= 2
    elif dt in [128, 511]:
        img_siz *= 3
        
    offset = int(hdr.dime.vox_offset) if filetype == 2 else 0
    with open(fn, 'rb') as f:
        f.seek(offset)
        if dt == 1:
            total_bytes = int(np.ceil(img_siz / 8))
            raw_bytes = f.read(total_bytes)
            img = np.unpackbits(np.frombuffer(raw_bytes, dtype=np.uint8))[:img_siz].astype(float)
        else:
            bytes_per_elem = nbits // 8
            if dt in [32, 1792]:
                bytes_per_elem = 8 if dt == 1792 else 4
            elif dt in [128, 511]:
                bytes_per_elem = 4 if dt == 511 else 1
            total_bytes = img_siz * bytes_per_elem
            raw_bytes = f.read(total_bytes)
            
            # NumPy format string
            if precision == 'int8':
                dtype_str = 'int8'
            elif precision == 'uint8':
                dtype_str = 'uint8'
            elif precision == 'int16':
                dtype_str = f"{endian}i2"
            elif precision == 'uint16':
                dtype_str = f"{endian}u2"
            elif precision == 'int32':
                dtype_str = f"{endian}i4"
            elif precision == 'uint32':
                dtype_str = f"{endian}u4"
            elif precision == 'int64':
                dtype_str = f"{endian}i8"
            elif precision == 'uint64':
                dtype_str = f"{endian}u8"
            elif precision == 'float32':
                dtype_str = f"{endian}f4"
            elif precision == 'float64':
                dtype_str = f"{endian}f8"
                
            img = np.frombuffer(raw_bytes, dtype=dtype_str).copy()
            
    if dt in [32, 1792]:
        img = img.reshape(2, -1)
        img = img[0, :] + 1j * img[1, :]
        
    hdr.dime.glmax = float(np.real(img).max()) if img.size > 0 else 0.0
    hdr.dime.glmin = float(np.real(img).min()) if img.size > 0 else 0.0
    
    if old_RGB and dt == 128:
        img = img.reshape(d1, d2, 3, d3, d4, d5, d6, d7)
        img = np.transpose(img, (0, 1, 3, 2, 4, 5, 6, 7))
    elif dt == 128 or dt == 511:
        if dt == 511:
            img = img.astype(float)
            img_min = img.min()
            img_max = img.max()
            if img_max > img_min:
                img = (img - img_min) / (img_max - img_min)
        img = img.reshape(3, d1, d2, d3, d4, d5, d6, d7)
        img = np.transpose(img, (1, 2, 3, 0, 4, 5, 6, 7))
    else:
        img = img.reshape(d1, d2, d3, d4, d5, d6, d7)
        
    # Helper to slice subset
    def get_indices(idx, size):
        if idx is None or len(np.atleast_1d(idx)) == 0:
            return slice(None)
        idx_arr = np.atleast_1d(idx) - 1
        return idx_arr
        
    idx_4 = get_indices(img_idx, d4)
    idx_5 = get_indices(dim5_idx, d5)
    idx_6 = get_indices(dim6_idx, d6)
    idx_7 = get_indices(dim7_idx, d7)
    
    if img.ndim == 7:
        img = img[:, :, :, idx_4, idx_5, idx_6, idx_7]
    elif img.ndim == 8:
        img = img[:, :, :, :, idx_4, idx_5, idx_6, idx_7]
        
    if img_idx is not None and len(np.atleast_1d(img_idx)) > 0:
        hdr.dime.dim[4] = len(np.atleast_1d(img_idx))
    if dim5_idx is not None and len(np.atleast_1d(dim5_idx)) > 0:
        hdr.dime.dim[5] = len(np.atleast_1d(dim5_idx))
    if dim6_idx is not None and len(np.atleast_1d(dim6_idx)) > 0:
        hdr.dime.dim[6] = len(np.atleast_1d(dim6_idx))
    if dim7_idx is not None and len(np.atleast_1d(dim7_idx)) > 0:
        hdr.dime.dim[7] = len(np.atleast_1d(dim7_idx))
        
    return img, hdr
