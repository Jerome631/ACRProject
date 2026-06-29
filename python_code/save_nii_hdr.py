import struct
import numpy as np

def save_nii_hdr(hdr, fid):
    if hdr.hk.sizeof_hdr != 348:
        raise ValueError("hdr.hk.sizeof_hdr must be 348.")
        
    if hdr.hist.qform_code == 0 and hdr.hist.sform_code == 0:
        hdr.hist.sform_code = 1
        hdr.hist.srow_x = np.array([hdr.dime.pixdim[1], 0.0, 0.0, (1.0 - hdr.hist.originator[0]) * hdr.dime.pixdim[1]], dtype=np.float32)
        hdr.hist.srow_y = np.array([0.0, hdr.dime.pixdim[2], 0.0, (1.0 - hdr.hist.originator[2]) * hdr.dime.pixdim[2]], dtype=np.float32) # wait, MATLAB code has originator(2) here, wait:
        # In MATLAB line 39:
        # hdr.hist.srow_y(4) = (1-hdr.hist.originator(2))*hdr.dime.pixdim(3);
        # Wait, originator(2) is the y originator, which maps to originator[1]!
        # Let's fix that. MATLAB 1-based indices to Python 0-based indices:
        # originator(1) -> originator[0]
        # originator(2) -> originator[1]
        # originator(3) -> originator[2]
        # pixdim(2) -> pixdim[1]
        # pixdim(3) -> pixdim[2]
        # pixdim(4) -> pixdim[3]
        # Let's double check. Yes, that is correct!
        hdr.hist.srow_y = np.array([0.0, hdr.dime.pixdim[2], 0.0, (1.0 - hdr.hist.originator[1]) * hdr.dime.pixdim[2]], dtype=np.float32)
        hdr.hist.srow_z = np.array([0.0, 0.0, hdr.dime.pixdim[3], (1.0 - hdr.hist.originator[2]) * hdr.dime.pixdim[3]], dtype=np.float32)

    # Pack hk
    def pack_str(s, length):
        if s is None:
            s = ""
        s_bytes = s.encode('latin1') if isinstance(s, str) else bytes(s)
        return s_bytes[:length].ljust(length, b'\x00')
        
    regular_byte = pack_str(hdr.hk.regular, 1)
    hk_packed = struct.pack(
        '<i10s18sihcB',
        int(hdr.hk.sizeof_hdr),
        pack_str(hdr.hk.data_type, 10),
        pack_str(hdr.hk.db_name, 18),
        int(hdr.hk.extents),
        int(hdr.hk.session_error),
        regular_byte,
        int(hdr.hk.dim_info)
    )
    
    # Pack dime
    dime_packed = struct.pack(
        '<8hfffhhhh8fffhBBffffii',
        *[int(x) for x in hdr.dime.dim],
        float(hdr.dime.intent_p1),
        float(hdr.dime.intent_p2),
        float(hdr.dime.intent_p3),
        int(hdr.dime.intent_code),
        int(hdr.dime.datatype),
        int(hdr.dime.bitpix),
        int(hdr.dime.slice_start),
        *[float(x) for x in hdr.dime.pixdim],
        float(hdr.dime.vox_offset),
        float(hdr.dime.scl_slope),
        float(hdr.dime.scl_inter),
        int(hdr.dime.slice_end),
        int(hdr.dime.slice_code),
        int(hdr.dime.xyzt_units),
        float(hdr.dime.cal_max),
        float(hdr.dime.cal_min),
        float(hdr.dime.slice_duration),
        float(hdr.dime.toffset),
        int(hdr.dime.glmax),
        int(hdr.dime.glmin)
    )
    
    # Pack hist
    hist_packed = struct.pack(
        '<80s24shhffffff4f4f4f16s4s',
        pack_str(hdr.hist.descrip, 80),
        pack_str(hdr.hist.aux_file, 24),
        int(hdr.hist.qform_code),
        int(hdr.hist.sform_code),
        float(hdr.hist.quatern_b),
        float(hdr.hist.quatern_c),
        float(hdr.hist.quatern_d),
        float(hdr.hist.qoffset_x),
        float(hdr.hist.qoffset_y),
        float(hdr.hist.qoffset_z),
        *[float(x) for x in hdr.hist.srow_x],
        *[float(x) for x in hdr.hist.srow_y],
        *[float(x) for x in hdr.hist.srow_z],
        pack_str(hdr.hist.intent_name, 16),
        pack_str(hdr.hist.magic, 4)
    )
    
    # Write to file
    fid.seek(0)
    fid.write(hk_packed)
    fid.write(dime_packed)
    fid.write(hist_packed)
    
    # In Analyze files, we check if originator is written? No, NIfTI standard save_nii_hdr doesn't write originator to header since it overlaps,
    # but MATLAB's save_nii saves it separately in a .mat file for SPM compatibility, which is handled in save_nii.py.
    # We will verify that file size is 348 bytes
    fbytes = fid.tell()
    if fbytes != 348:
        print(f"Warning: Header size is {fbytes} bytes (expected 348)")
