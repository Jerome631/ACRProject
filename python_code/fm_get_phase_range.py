import os
import sys
import numpy as np
from load_nii import load_nii
from load_nii_hdr import load_nii_hdr
from vector import vector

def fm_get_phase_range(data):
    root_dir = data['root_dir']
    readfile_dirs = data['readfile_dirs']
    nii_dim = data['nii_dim']
    file_code = data['file_code']
    reform_subdir = data['reform_subdir']

    if isinstance(readfile_dirs, (list, tuple)):
        dir1 = readfile_dirs[0]
        dir2 = readfile_dirs[1] if len(readfile_dirs) > 1 else readfile_dirs[0]
    else:
        dir1 = readfile_dirs
        dir2 = readfile_dirs

    if file_code in ['SE', 'SCSE']:
        # (1:1:nii_dim(5)) -> img_idx = np.arange(1, nii_dim[4]+1)
        # 2 -> dim5_idx = 2
        one_echo_nii = load_nii(
            os.path.join(root_dir, dir1, reform_subdir, 'Image.nii'),
            img_idx=np.arange(1, int(nii_dim[4]) + 1),
            dim5_idx=2
        )
    elif file_code in ['SPM', 'SCSPM']:
        hdr, _, _, _ = load_nii_hdr(os.path.join(root_dir, dir1, reform_subdir, 'Image.nii'))
        dim1 = hdr.dime.dim[0]
        if dim1 == 3:
            one_echo_nii = load_nii(os.path.join(root_dir, dir2, reform_subdir, 'Image.nii'))
        elif dim1 == 4:
            one_echo_nii = load_nii(
                os.path.join(root_dir, dir2, reform_subdir, 'Image.nii'),
                img_idx=np.arange(1, int(nii_dim[4]) + 1)
            )
        elif dim1 == 5:
            one_echo_nii = load_nii(
                os.path.join(root_dir, dir2, reform_subdir, 'Image.nii'),
                img_idx=2,
                dim5_idx=np.arange(1, int(nii_dim[5]) + 1)
            )
        else:
            one_echo_nii = load_nii(os.path.join(root_dir, dir2, reform_subdir, 'Image.nii'))
    elif file_code in ['SESPM', 'SCSESPM']:
        one_echo_nii = load_nii(os.path.join(root_dir, dir2, reform_subdir, 'Image.nii'))
    else:
        if isinstance(readfile_dirs, (list, tuple)):
            dir_path = os.path.join(root_dir, readfile_dirs[0], reform_subdir, 'Image.nii')
        else:
            dir_path = os.path.join(root_dir, readfile_dirs, reform_subdir, 'Image.nii')

        one_echo_nii = load_nii(
            dir_path,
            img_idx=1,
            dim5_idx=np.arange(1, int(nii_dim[5]) + 1),
            dim6_idx=2
        )

    img_data = one_echo_nii.img
    # Safely index first channel/echo from multidimensional image
    if img_data.ndim > 3:
        one_echo_one_channel = img_data[(slice(None), slice(None), slice(None)) + (0,) * (img_data.ndim - 3)]
    else:
        one_echo_one_channel = img_data

    val_min = np.min(vector(one_echo_one_channel))
    val_max = np.max(vector(one_echo_one_channel))

    phase_range = [
        float(np.round(val_min / 2048.0) * 2048.0),
        float(np.round(val_max / 2048.0) * 2048.0)
    ]
    data['phase_range'] = phase_range
    print(f"   - the phase range in the data is {int(phase_range[0])} -> {int(phase_range[1])}")

    return data
