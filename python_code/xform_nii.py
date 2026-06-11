import numpy as np
from load_nii_hdr import struct

def xform_nii(nii, tolerance=0.1, preferredForm='s'):
    # save original header
    nii.original = struct(hdr=struct({k: struct(v) if isinstance(v, dict) else (v.copy() if hasattr(v, 'copy') else v) for k, v in nii.hdr.items()}))

    if tolerance <= 0:
        tolerance = 1e-7

    # Voxel scaling (y = slope * x + inter)
    scl_slope = nii.hdr.dime.scl_slope
    scl_inter = nii.hdr.dime.scl_inter
    datatype = nii.hdr.dime.datatype
    
    # Check if datatype is numeric and we need scaling
    if scl_slope != 0 and datatype in [2, 4, 8, 16, 64, 256, 512, 768] and (scl_slope != 1 or scl_inter != 0):
        nii.img = scl_slope * nii.img.astype(float) + scl_inter
        if datatype == 64:
            nii.hdr.dime.datatype = 64
            nii.hdr.dime.bitpix = 64
        else:
            nii.img = nii.img.astype(np.float32)
            nii.hdr.dime.datatype = 16
            nii.hdr.dime.bitpix = 32
        nii.hdr.dime.glmax = float(nii.img.max())
        nii.hdr.dime.glmin = float(nii.img.min())
        nii.hdr.dime.scl_slope = 0.0

    # Complex scaling
    if scl_slope != 0 and datatype in [32, 1792]:
        nii.img = scl_slope * nii.img.astype(complex) + scl_inter
        if datatype == 32:
            nii.img = nii.img.astype(np.complex64)
        nii.hdr.dime.glmax = float(np.real(nii.img).max())
        nii.hdr.dime.glmin = float(np.real(nii.img).min())
        nii.hdr.dime.scl_slope = 0.0

    # Handle Analyze format (.hdr/.img with .mat)
    if nii.filetype == 0:
        # No mat files usually present in this project, just return
        nii.hdr.hist.rot_orient = []
        nii.hdr.hist.flip_orient = []
        return nii

    hdr = nii.hdr
    hdr, orient = change_hdr(hdr, tolerance, preferredForm)

    # Flip and rotate image data
    if not np.array_equal(orient, [1, 2, 3]):
        old_dim = hdr.dime.dim[1:4] # 0-based index: elements 1, 2, 3 correspond to x, y, z
        
        # Calculate rot_orient and flip_orient (1-based to match MATLAB logic)
        rot_orient = np.mod(orient - 1, 3) + 1  # wait, MATLAB: rot_orient = mod(orient + 2, 3) + 1. Since orient is 1-based, mod(orient+2, 3) wraps correctly!
        # Let's verify: mod(1+2, 3)+1 = 1. mod(4+2, 3)+1 = 1. mod(5+2, 3)+1 = 2.
        # Yes, mod(orient+2, 3)+1 is the absolute dimension index 1, 2, 3 (regardless of sign/direction).
        # And flip_orient = orient - rot_orient. If orient < 0 (i.e. sign direction), then orient has values 4, 5, 6.
        # Wait, get_orient returns orient with values 1 to 6.
        # Let's check get_orient:
        # case 1: L to R (value 1)
        # case 2: P to A (value 2)
        # case 3: I to S (value 3)
        # case -1: R to L (value 4)
        # case -2: A to P (value 5)
        # case -3: S to I (value 6)
        # So:
        # rot_orient = mod(orient + 2, 3) + 1.
        # For orient = 1: mod(3, 3)+1 = 1.
        # For orient = 4 (R to L): mod(6, 3)+1 = 1.
        # For orient = 2: mod(4, 3)+1 = 2.
        # For orient = 5 (A to P): mod(7, 3)+1 = 2.
        # For orient = 3: mod(5, 3)+1 = 3.
        # For orient = 6 (S to I): mod(8, 3)+1 = 3.
        # So rot_orient is indeed the spatial dimension index (1 for X, 2 for Y, 3 for Z).
        # flip_orient = orient - rot_orient.
        # If orient is 1, 2, 3, flip_orient is 0.
        # If orient is 4, 5, 6, flip_orient is 3.
        rot_orient = np.mod(orient + 2, 3) + 1
        flip_orient = orient - rot_orient

        # Perform flips (0-based indices for numpy)
        # flip_orient is 3 for flipped axes. So for axis i in 0, 1, 2:
        for i in range(3):
            if flip_orient[i] != 0:
                # flipdim along axis i
                # In numpy, this is np.flip(nii.img, axis=i)
                nii.img = np.flip(nii.img, axis=i)

        # Rotate/Permute dimensions
        # rot_orient tells us the ordering of the first three dimensions.
        # In MATLAB, [tmp rot_orient] = sort(rot_orient).
        # Then we permute. Let's trace carefully:
        # rot_orient contains a permutation of [1, 2, 3].
        # For example, if rot_orient is [2, 1, 3], then the current dimensions [Y, X, Z] must be permuted to [X, Y, Z].
        # In MATLAB, sort(rot_orient) returns the indices to sort it, which corresponds to the inverse permutation!
        # So:
        # idx = argsort(rot_orient).
        # Let's compute this:
        # 1-based sort indices:
        rot_sort_idx = np.argsort(rot_orient) + 1 # wait, argsort returns 0-based indices of sorted elements.
        # For rot_orient = [2, 1, 3], argsort returns [1, 0, 2] (since index 1 is value 1, index 0 is value 2, index 2 is value 3).
        # So sorted indices (1-based) is [2, 1, 3].
        # Let's check:
        # In MATLAB: [tmp rot_orient] = sort(rot_orient).
        # If rot_orient was [2, 1, 3], sort returns sorted values [1, 2, 3] and indices rot_orient = [2, 1, 3].
        # Yes! So the new `rot_orient` is exactly the sorting indices.
        # In Python, this is `rot_orient_sorted_idx = np.argsort(rot_orient)`.
        # Wait, let's write it in 0-based:
        rot_orient_0 = rot_orient - 1
        rot_orient_sort = np.argsort(rot_orient_0)
        
        # update dim and pixdim in header
        new_dim = old_dim[rot_orient_sort]
        hdr.dime.dim[1:4] = new_dim
        
        new_pixdim = hdr.dime.pixdim[1:4]
        new_pixdim = new_pixdim[rot_orient_sort]
        hdr.dime.pixdim[1:4] = new_pixdim
        
        # update originator
        originator = hdr.hist.originator[0:3]
        originator = originator[rot_orient_sort]
        flip_orient_sorted = flip_orient[rot_orient_sort]
        
        for i in range(3):
            if flip_orient_sorted[i] != 0 and originator[i] != 0:
                originator[i] = new_dim[i] - originator[i] + 1
        hdr.hist.originator[0:3] = originator
        
        # Record orientation parameters
        hdr.hist.rot_orient = rot_orient_sort + 1
        hdr.hist.flip_orient = flip_orient_sorted
        
        # Do the actual transpose of image data
        # rot_orient_sort tells us the new axis mapping.
        # In MATLAB: permute(nii.img, rot_orient).
        # In Python, we want to transpose. If we have shape (d1, d2, d3, ...),
        # we transpose the first three dimensions.
        # So the transpose axes will be: list(rot_orient_sort) + list(range(3, nii.img.ndim))
        axes = list(rot_orient_sort) + list(range(3, nii.img.ndim))
        
        # Transpose
        if datatype in [32, 1792]: # Complex
            # nii.img has real and imaginary parts (or it's complex numpy array, which is ndim-dimensional)
            nii.img = np.transpose(nii.img, axes)
        elif datatype in [128, 511]: # RGB
            # nii.img shape has RGB channels at axis 3 (the 4th axis).
            # So standard shape has 8 axes.
            # In MATLAB, permute was done separately on planes 1, 2, 3.
            # In Python, the RGB axis is axis 3.
            # Let's permute the first three axes, keeping axis 3 and rest unchanged.
            # Axes will be: [rot_orient_sort[0], rot_orient_sort[1], rot_orient_sort[2], 3] + list(range(4, nii.img.ndim))
            # Wait! Let's check:
            # If nii.img shape is (d1, d2, d3, 3, d4, d5, d6, d7), then the axes are:
            # 0, 1, 2: spatial
            # 3: RGB
            # 4, 5, 6, 7: rest
            # So transpose axes: [rot_orient_sort[0], rot_orient_sort[1], rot_orient_sort[2], 3] + list(range(4, nii.img.ndim))
            axes = [rot_orient_sort[0], rot_orient_sort[1], rot_orient_sort[2], 3] + list(range(4, nii.img.ndim))
            nii.img = np.transpose(nii.img, axes)
        else:
            nii.img = np.transpose(nii.img, axes)
            
    else:
        hdr.hist.rot_orient = []
        hdr.hist.flip_orient = []
        
    nii.hdr = hdr
    return nii

def change_hdr(hdr, tolerance, preferredForm):
    orient = np.array([1, 2, 3])
    affine_transform = False
    useForm = None

    if preferredForm == 'S':
        if hdr.hist.sform_code == 0:
            raise ValueError("User requires sform, sform not set in header")
        useForm = 's'
    elif preferredForm == 'Q':
        if hdr.hist.qform_code == 0:
            raise ValueError("User requires qform, qform not set in header")
        useForm = 'q'
    elif preferredForm == 's':
        if hdr.hist.sform_code > 0:
            useForm = 's'
        elif hdr.hist.qform_code > 0:
            useForm = 'q'
    elif preferredForm == 'q':
        if hdr.hist.qform_code > 0:
            useForm = 'q'
        elif hdr.hist.sform_code > 0:
            useForm = 's'

    if useForm == 's':
        R = np.array([
            hdr.hist.srow_x[0:3],
            hdr.hist.srow_y[0:3],
            hdr.hist.srow_z[0:3]
        ])
        T = np.array([
            hdr.hist.srow_x[3],
            hdr.hist.srow_y[3],
            hdr.hist.srow_z[3]
        ])
        
        # Check orthogonality
        # det(R) == 0 or non-orthogonal check.
        # In MATLAB: ~isequal(R(find(R)), sum(R)')
        # In python: R(find(R)) is the list of non-zero elements.
        # Let's check if the non-zero elements match the column-wise sum.
        # If it's a diagonal/permutation matrix (orthogonal with scaling),
        # there is exactly one non-zero element per row and column.
        # We can implement this check:
        det_R = np.linalg.det(R)
        is_orthogonal = True
        # For each column, count non-zeroes
        for c in range(3):
            if np.sum(np.abs(R[:, c]) > 0) != 1:
                is_orthogonal = False
                
        if abs(det_R) < 1e-5 or not is_orthogonal:
            # Try thresholding small elements
            hdr.hist.old_affine = np.vstack([np.hstack([R, T[:, np.newaxis]]), [0, 0, 0, 1]])
            R_abs = np.sort(np.abs(R.flatten()))
            threshold = tolerance * R_abs[-3]
            R_clean = R.copy()
            R_clean[np.abs(R) < threshold] = 0.0
            hdr.hist.new_affine = np.vstack([np.hstack([R_clean, T[:, np.newaxis]]), [0, 0, 0, 1]])
            
            # Recheck
            det_R_clean = np.linalg.det(R_clean)
            is_orthogonal_clean = True
            for c in range(3):
                if np.sum(np.abs(R_clean[:, c]) > 0) != 1:
                    is_orthogonal_clean = False
            if abs(det_R_clean) < 1e-5 or not is_orthogonal_clean:
                raise ValueError("Non-orthogonal rotation or shearing found inside the affine matrix in this NIfTI file.")
            R = R_clean
            
        affine_transform = True

    elif useForm == 'q':
        b = hdr.hist.quatern_b
        c = hdr.hist.quatern_c
        d = hdr.hist.quatern_d
        
        val = 1.0 - (b*b + c*c + d*d)
        if val < 0:
            if abs(val) < 1e-5:
                a = 0.0
            else:
                raise ValueError("Incorrect quaternion values in this NIFTI data.")
        else:
            a = np.sqrt(val)
            
        qfac = hdr.dime.pixdim[0]
        if qfac == 0:
            qfac = 1.0
            
        i_vox = hdr.dime.pixdim[1]
        j_vox = hdr.dime.pixdim[2]
        k_vox = qfac * hdr.dime.pixdim[3]
        
        R = np.array([
            [a*a+b*b-c*c-d*d,     2*b*c-2*a*d,        2*b*d+2*a*c],
            [2*b*c+2*a*d,         a*a+c*c-b*b-d*d,    2*c*d-2*a*b],
            [2*b*d-2*a*c,         2*c*d+2*a*b,        a*a+d*d-c*c-b*b]
        ])
        
        T = np.array([
            hdr.hist.qoffset_x,
            hdr.hist.qoffset_y,
            hdr.hist.qoffset_z
        ])
        
        # Check orthogonality
        is_orthogonal = True
        for col_idx in range(3):
            if np.sum(np.abs(R[:, col_idx]) > 0) != 1:
                is_orthogonal = False
                
        if np.linalg.det(R) == 0 or not is_orthogonal:
            hdr.hist.old_affine = np.vstack([np.hstack([R * np.array([i_vox, j_vox, k_vox]), T[:, np.newaxis]]), [0, 0, 0, 1]])
            R_abs = np.sort(np.abs(R.flatten()))
            threshold = tolerance * R_abs[-3]
            R_clean = R.copy()
            R_clean[np.abs(R) < threshold] = 0.0
            R_scaled = R_clean * np.array([i_vox, j_vox, k_vox])
            hdr.hist.new_affine = np.vstack([np.hstack([R_scaled, T[:, np.newaxis]]), [0, 0, 0, 1]])
            
            is_orthogonal_clean = True
            for col_idx in range(3):
                if np.sum(np.abs(R_clean[:, col_idx]) > 0) != 1:
                    is_orthogonal_clean = False
            if np.linalg.det(R_clean) == 0 or not is_orthogonal_clean:
                raise ValueError("Non-orthogonal rotation or shearing found inside the affine matrix in this NIfTI file.")
            R = R_scaled
        else:
            R = R * np.array([i_vox, j_vox, k_vox])
            
        affine_transform = True

    if affine_transform:
        voxel_size = np.abs(np.sum(R, axis=0))
        inv_R = np.linalg.inv(R)
        originator = np.dot(inv_R, -T) + 1.0
        orient = get_orient(inv_R)
        
        hdr.dime.pixdim[1:4] = voxel_size
        hdr.hist.originator[0:3] = originator
        hdr.hist.qform_code = 0
        hdr.hist.sform_code = 0

    space_unit, time_unit = get_units(hdr)
    if space_unit != 1:
        hdr.dime.pixdim[1:4] = hdr.dime.pixdim[1:4] * space_unit
        # Reset xyzt_units to mm
        # xyzt_units is 1 byte, bit 0 to 2 for space, bit 3 to 5 for time.
        # bitset(xyzt_units, 1, 0) -> clear bit 0
        # bitset(xyzt_units, 2, 1) -> set bit 1
        # bitset(xyzt_units, 3, 0) -> clear bit 2
        # (This represents value 2, which is NIFTI_UNITS_MM)
        val = int(hdr.dime.xyzt_units)
        val = (val & ~1) # clear bit 0
        val = (val | 2)  # set bit 1
        val = (val & ~4) # clear bit 2
        hdr.dime.xyzt_units = val

    hdr.dime.pixdim = np.abs(hdr.dime.pixdim)
    return hdr, orient

def get_orient(R):
    orient = []
    for i in range(3):
        # find non-zero column
        row = R[i, :]
        nz_idx = np.where(np.abs(row) > 0)[0]
        if len(nz_idx) == 0:
            val = 1
        else:
            val = nz_idx[0] + 1  # 1-based index
            
        sign_val = np.sign(np.sum(row))
        code = val * sign_val
        
        if code == 1:
            orient.append(1)  # Left to Right
        elif code == 2:
            orient.append(2)  # Posterior to Anterior
        elif code == 3:
            orient.append(3)  # Inferior to Superior
        elif code == -1:
            orient.append(4)  # Right to Left
        elif code == -2:
            orient.append(5)  # Anterior to Posterior
        elif code == -3:
            orient.append(6)  # Superior to Inferior
        else:
            orient.append(1) # fallback
            
    return np.array(orient)

def get_units(hdr):
    units = int(hdr.dime.xyzt_units)
    space_code = units & 7
    if space_code == 1:
        space_unit = 1e+3  # meter
    elif space_code == 3:
        space_unit = 1e-3  # micrometer
    else:
        space_unit = 1.0   # millimeter
        
    time_code = units & 56
    if time_code == 16:
        time_unit = 1e-3  # millisecond
    elif time_code == 24:
        time_unit = 1e-6  # microsecond
    else:
        time_unit = 1.0   # second
        
    return space_unit, time_unit
