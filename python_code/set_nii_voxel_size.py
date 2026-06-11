import numpy as np
from load_nii_hdr import struct

def set_nii_voxel_size(old_hdr, pixdim):
    # If a filename string is passed, load the file, update, and save
    if isinstance(old_hdr, str):
        from load_nii import load_nii
        from save_nii import save_nii
        nii = load_nii(old_hdr)
        nii.hdr.dime.pixdim = np.asarray(pixdim, dtype=np.float32)
        save_nii(nii, old_hdr)
        return nii.hdr

    new_hdr = old_hdr
    new_hdr.dime.pixdim = np.asarray(pixdim, dtype=np.float32)
    return new_hdr
