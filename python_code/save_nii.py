import os
import struct
import numpy as np
import scipy.io as sio
from load_nii_hdr import struct as Bunch
from verify_nii_ext import verify_nii_ext
from save_nii_ext import save_nii_ext
from save_nii_hdr import save_nii_hdr

def save_nii(nii, fileprefix, old_RGB=0):
    if not isinstance(nii, dict) or 'hdr' not in nii or 'img' not in nii:
        raise ValueError("Usage: save_nii(nii, filename, [old_RGB])")
        
    nii = Bunch(nii)
    fileprefix = str(fileprefix)
    
    filetype = 1
    if '.nii' in fileprefix:
        filetype = 2
        fileprefix = fileprefix.replace('.nii', '')
    if '.hdr' in fileprefix:
        fileprefix = fileprefix.replace('.hdr', '')
    if '.img' in fileprefix:
        fileprefix = fileprefix.replace('.img', '')
        
    write_nii(nii, filetype, fileprefix, old_RGB)
    
    if filetype == 1:
        # Save SPM compatible .mat file
        diag_vals = nii.hdr.dime.pixdim[1:4]
        originator = nii.hdr.hist.originator[0:3]
        M = np.eye(4)
        M[0:3, 0:3] = np.diag(diag_vals)
        M[0:3, 3] = -(originator * diag_vals)
        sio.savemat(f"{fileprefix}.mat", {'M': M})

def write_nii(nii, filetype, fileprefix, old_RGB):
    hdr = Bunch(nii.hdr)
    img = np.asarray(nii.img)
    
    if 'ext' in nii and nii.ext:
        ext, esize_total = verify_nii_ext(nii.ext)
    else:
        ext = None
        esize_total = 0
        
    dt = int(hdr.dime.datatype)
    if dt == 1:
        hdr.dime.bitpix = 1
        precision = 'uint8'
    elif dt == 2:
        hdr.dime.bitpix = 8
        precision = 'uint8'
    elif dt == 4:
        hdr.dime.bitpix = 16
        precision = 'int16'
    elif dt == 8:
        hdr.dime.bitpix = 32
        precision = 'int32'
    elif dt == 16:
        hdr.dime.bitpix = 32
        precision = 'float32'
    elif dt == 32:
        hdr.dime.bitpix = 64
        precision = 'float32'
    elif dt == 64:
        hdr.dime.bitpix = 64
        precision = 'float64'
    elif dt == 128:
        hdr.dime.bitpix = 24
        precision = 'uint8'
    elif dt == 256:
        hdr.dime.bitpix = 8
        precision = 'int8'
    elif dt == 512:
        hdr.dime.bitpix = 16
        precision = 'uint16'
    elif dt == 768:
        hdr.dime.bitpix = 32
        precision = 'uint32'
    elif dt == 1024:
        hdr.dime.bitpix = 64
        precision = 'int64'
    elif dt == 1280:
        hdr.dime.bitpix = 64
        precision = 'uint64'
    elif dt == 1792:
        hdr.dime.bitpix = 128
        precision = 'float64'
    else:
        raise ValueError(f"Datatype {dt} is not supported")
        
    hdr.dime.glmax = float(np.real(img).max()) if img.size > 0 else 0.0
    hdr.dime.glmin = float(np.real(img).min()) if img.size > 0 else 0.0
    
    if filetype == 2:
        fn = f"{fileprefix}.nii"
        fid = open(fn, 'wb')
        hdr.dime.vox_offset = 352.0
        if ext:
            hdr.dime.vox_offset += esize_total
        hdr.hist.magic = 'n+1'
        save_nii_hdr(hdr, fid)
        if ext:
            save_nii_ext(ext, fid)
    else:
        fn_hdr = f"{fileprefix}.hdr"
        fid = open(fn_hdr, 'wb')
        hdr.dime.vox_offset = 0.0
        hdr.hist.magic = 'ni1'
        save_nii_hdr(hdr, fid)
        if ext:
            save_nii_ext(ext, fid)
        fid.close()
        
        fn_img = f"{fileprefix}.img"
        fid = open(fn_img, 'wb')
        
    skip_bytes = int(hdr.dime.vox_offset) - 348 if filetype == 2 and not ext else 0
    
    # RGB formatting
    if dt == 128:
        # permute RGB planes
        if old_RGB:
            img = np.transpose(img, (0, 1, 3, 2, 4, 5, 6, 7))
        else:
            img = np.transpose(img, (1, 2, 3, 0, 4, 5, 6, 7))
            
    # Complex formatting
    if dt in [32, 1792]:
        real_img = np.real(img.flatten())
        imag_img = np.imag(img.flatten())
        # Interleave real and imag
        img_interleaved = np.empty(real_img.size * 2, dtype=real_img.dtype)
        img_interleaved[0::2] = real_img
        img_interleaved[1::2] = imag_img
        img = img_interleaved
        
    if skip_bytes > 0:
        fid.write(b'\x00' * skip_bytes)
        
    # Write image data
    # Convert numpy dtype to target precision
    if precision == 'int8':
        dtype_str = 'int8'
    elif precision == 'uint8':
        dtype_str = 'uint8'
    elif precision == 'int16':
        dtype_str = 'int16'
    elif precision == 'uint16':
        dtype_str = 'uint16'
    elif precision == 'int32':
        dtype_str = 'int32'
    elif precision == 'uint32':
        dtype_str = 'uint32'
    elif precision == 'int64':
        dtype_str = 'int64'
    elif precision == 'uint64':
        dtype_str = 'uint64'
    elif precision == 'float32':
        dtype_str = 'float32'
    elif precision == 'float64':
        dtype_str = 'float64'
        
    fid.write(img.astype(dtype_str).tobytes())
    fid.close()
