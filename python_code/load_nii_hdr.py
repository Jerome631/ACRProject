import os
import struct
import numpy as np

class struct(dict):
    def __getattr__(self, name):
        try:
            val = self[name]
            if isinstance(val, dict) and not isinstance(val, struct):
                val = struct(val)
                self[name] = val
            return val
        except KeyError:
            raise AttributeError(name)
    def __setattr__(self, name, value):
        self[name] = value

def load_nii_hdr(fileprefix):
    new_ext = False
    if '.nii' in fileprefix:
        new_ext = True
        fileprefix = fileprefix.replace('.nii', '')
    if '.hdr' in fileprefix:
        fileprefix = fileprefix.replace('.hdr', '')
    if '.img' in fileprefix:
        fileprefix = fileprefix.replace('.img', '')
        
    if new_ext:
        fn = f"{fileprefix}.nii"
        if not os.path.exists(fn):
            raise FileNotFoundError(f"Cannot find file {fn}")
    else:
        fn = f"{fileprefix}.hdr"
        if not os.path.exists(fn):
            fn = f"{fileprefix}.nii"
            if not os.path.exists(fn):
                raise FileNotFoundError(f"Cannot find file {fileprefix}.hdr or {fileprefix}.nii")
                
    with open(fn, 'rb') as f:
        header_data = f.read(348)
        
    if len(header_data) < 348:
        raise ValueError(f"Header in {fn} is too short.")
        
    endian = '<'
    sizeof_hdr, = struct.unpack(endian + 'i', header_data[:4])
    if sizeof_hdr != 348:
        endian = '>'
        sizeof_hdr, = struct.unpack(endian + 'i', header_data[:4])
        if sizeof_hdr != 348:
            raise ValueError(f"File {fn} is corrupted or not a NIfTI-1 file.")
            
    machine = 'ieee-le' if endian == '<' else 'ieee-be'
    
    def clean_str(b):
        return b.split(b'\x00')[0].decode('latin1').strip()
        
    # hk
    hk_fields = struct.unpack(endian + 'i10s18sihcBs', header_data[:40])
    hk = struct(
        sizeof_hdr=hk_fields[0],
        data_type=clean_str(hk_fields[1]),
        db_name=clean_str(hk_fields[2]),
        extents=hk_fields[3],
        session_error=hk_fields[4],
        regular=clean_str(hk_fields[5]),
        dim_info=hk_fields[6]
    )
    
    # dime
    dime_fields = struct.unpack(endian + '8hfffhhhh8fffhBBffffii', header_data[40:148])
    dime = struct(
        dim=np.array(dime_fields[0:8], dtype=np.int16),
        intent_p1=dime_fields[8],
        intent_p2=dime_fields[9],
        intent_p3=dime_fields[10],
        intent_code=dime_fields[11],
        datatype=dime_fields[12],
        bitpix=dime_fields[13],
        slice_start=dime_fields[14],
        pixdim=np.array(dime_fields[15:23], dtype=np.float32),
        vox_offset=dime_fields[23],
        scl_slope=dime_fields[24],
        scl_inter=dime_fields[25],
        slice_end=dime_fields[26],
        slice_code=dime_fields[27],
        xyzt_units=dime_fields[28],
        cal_max=dime_fields[29],
        cal_min=dime_fields[30],
        slice_duration=dime_fields[31],
        toffset=dime_fields[32],
        glmax=dime_fields[33],
        glmin=dime_fields[34]
    )
    
    # hist
    hist_fields = struct.unpack(endian + '80s24shhffffff4f4f4f16s4s', header_data[148:348])
    hist = struct(
        descrip=clean_str(hist_fields[0]),
        aux_file=clean_str(hist_fields[1]),
        qform_code=hist_fields[2],
        sform_code=hist_fields[3],
        quatern_b=hist_fields[4],
        quatern_c=hist_fields[5],
        quatern_d=hist_fields[6],
        qoffset_x=hist_fields[7],
        qoffset_y=hist_fields[8],
        qoffset_z=hist_fields[9],
        srow_x=np.array(hist_fields[10:14], dtype=np.float32),
        srow_y=np.array(hist_fields[14:18], dtype=np.float32),
        srow_z=np.array(hist_fields[18:22], dtype=np.float32),
        intent_name=clean_str(hist_fields[22]),
        magic=clean_str(hist_fields[23])
    )
    
    # originator
    originator_fields = struct.unpack(endian + '5h', header_data[253:263])
    hist.originator = np.array(originator_fields, dtype=np.int16)
    
    hdr = struct(hk=hk, dime=dime, hist=hist)
    
    if hist.magic == 'n+1':
        filetype = 2
    elif hist.magic == 'ni1':
        filetype = 1
    else:
        filetype = 0
        hist.qform_code = 0
        hist.sform_code = 0
        
    return hdr, filetype, fileprefix, machine
