import numpy as np
from load_nii_hdr import struct

def make_nii(img, voxel_size=None, origin=None, datatype=None, description=""):
    img = np.asarray(img)
    
    if img.ndim > 7:
        raise ValueError("NIfTI only allows a maximum of 7 Dimension matrix.")
        
    dims = list(img.shape)
    dims = [len(dims)] + dims + [1] * 8
    dims = np.array(dims[:8], dtype=np.int16)
    
    # default voxel_size
    v_sz = np.array([0.0] + [1.0] * 7, dtype=np.float32)
    if voxel_size is not None and len(np.atleast_1d(voxel_size)) > 0:
        voxel_size_val = np.atleast_1d(voxel_size)
        v_sz[1:1+len(voxel_size_val)] = voxel_size_val
        
    # default origin
    orig = np.zeros(5, dtype=np.int16)
    if origin is not None and len(np.atleast_1d(origin)) > 0:
        origin_val = np.atleast_1d(origin)
        orig[:len(origin_val)] = origin_val
        
    # default datatype based on img dtype
    if datatype is None:
        if img.dtype == np.uint8:
            datatype = 2
        elif img.dtype == np.int16:
            datatype = 4
        elif img.dtype == np.int32:
            datatype = 8
        elif img.dtype == np.float32:
            datatype = 16
        elif img.dtype == np.float64:
            datatype = 64
        elif img.dtype == np.int8:
            datatype = 256
        elif img.dtype == np.uint16:
            datatype = 512
        elif img.dtype == np.uint32:
            datatype = 768
        else:
            # Fallback to float32 or float64
            if np.iscomplexobj(img):
                datatype = 32 if img.dtype == np.complex64 else 1792
            else:
                datatype = 16
                
    # Typecast img according to datatype
    if datatype == 2:
        img = img.astype(np.uint8)
        bitpix = 8
    elif datatype == 4:
        img = img.astype(np.int16)
        bitpix = 16
    elif datatype == 8:
        img = img.astype(np.int32)
        bitpix = 32
    elif datatype == 16:
        img = img.astype(np.float32)
        bitpix = 32
    elif datatype == 64:
        img = img.astype(np.float64)
        bitpix = 64
    elif datatype == 256:
        img = img.astype(np.int8)
        bitpix = 8
    elif datatype == 512:
        img = img.astype(np.uint16)
        bitpix = 16
    elif datatype == 768:
        img = img.astype(np.uint32)
        bitpix = 32
    elif datatype == 32:
        img = img.astype(np.complex64)
        bitpix = 64
    elif datatype == 1792:
        img = img.astype(np.complex128)
        bitpix = 128
    else:
        raise ValueError(f"Datatype {datatype} is not supported by make_nii.")

    maxval = float(np.real(img).max()) if img.size > 0 else 0.0
    minval = float(np.real(img).min()) if img.size > 0 else 0.0
    
    # Create header structures
    hk = struct(
        sizeof_hdr=348,
        data_type='',
        db_name='',
        extents=0,
        session_error=0,
        regular='r',
        dim_info=0
    )
    
    dime = struct(
        dim=dims,
        intent_p1=0.0,
        intent_p2=0.0,
        intent_p3=0.0,
        intent_code=0,
        datatype=datatype,
        bitpix=bitpix,
        slice_start=0,
        pixdim=v_sz,
        vox_offset=0.0,
        scl_slope=0.0,
        scl_inter=0.0,
        slice_end=0,
        slice_code=0,
        xyzt_units=0,
        cal_max=0.0,
        cal_min=0.0,
        slice_duration=0.0,
        toffset=0.0,
        glmax=maxval,
        glmin=minval
    )
    
    hist = struct(
        descrip=description,
        aux_file='none',
        qform_code=0,
        sform_code=0,
        quatern_b=0.0,
        quatern_c=0.0,
        quatern_d=0.0,
        qoffset_x=0.0,
        qoffset_y=0.0,
        qoffset_z=0.0,
        srow_x=np.zeros(4, dtype=np.float32),
        srow_y=np.zeros(4, dtype=np.float32),
        srow_z=np.zeros(4, dtype=np.float32),
        intent_name='',
        magic='',
        originator=orig
    )
    
    hdr = struct(hk=hk, dime=dime, hist=hist)
    nii = struct(hdr=hdr, img=img)
    return nii
