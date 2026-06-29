import struct

def save_nii_ext(ext, fid):
    # fid is a file object open in write-binary ('wb') mode
    if 'extension' not in ext or 'section' not in ext or 'num_ext' not in ext:
        raise ValueError("Wrong header extension")
        
    # Write extension array (4 bytes)
    ext_bytes = bytes(ext.extension)
    fid.write(ext_bytes)
    
    # Write sections
    for i in range(ext.num_ext):
        sec = ext.section[i]
        fid.write(struct.pack('<ii', int(sec.esize), int(sec.ecode)))
        
        # Write edata (can be string or bytes or numpy array)
        if isinstance(sec.edata, str):
            fid.write(sec.edata.encode('latin1'))
        else:
            fid.write(bytes(sec.edata))
