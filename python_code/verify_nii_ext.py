import numpy as np
from load_nii_hdr import struct

def verify_nii_ext(ext):
    if not isinstance(ext, dict):
        raise ValueError("Incorrect NIFTI header extension structure.")
        
    ext_struct = struct(ext)
    
    if 'section' not in ext_struct:
        raise ValueError("Incorrect NIFTI header extension structure.")
        
    if 'num_ext' not in ext_struct:
        ext_struct.num_ext = len(ext_struct.section)
        
    if 'extension' not in ext_struct:
        ext_struct.extension = np.array([1, 0, 0, 0], dtype=np.uint8)
        
    esize_total = 0
    for i in range(ext_struct.num_ext):
        sec = struct(ext_struct.section[i])
        if 'ecode' not in sec or 'edata' not in sec:
            raise ValueError("Incorrect NIFTI header extension structure.")
            
        edata_len = len(sec.edata)
        sec.esize = int(np.ceil((edata_len + 8) / 16.0) * 16)
        
        # pad edata with zeros
        pad_len = sec.esize - edata_len - 8
        if pad_len > 0:
            if isinstance(sec.edata, str):
                sec.edata = sec.edata + '\x00' * pad_len
            else:
                sec.edata = np.concatenate([sec.edata, np.zeros(pad_len, dtype=np.uint8)])
                
        esize_total += sec.esize
        ext_struct.section[i] = sec
        
    return ext_struct, esize_total
