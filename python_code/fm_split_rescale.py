import os
import sys
import numpy as np
from load_nii import load_nii
from load_nii_hdr import load_nii_hdr
from make_nii import make_nii
from centre_and_save_nii import centre_and_save_nii

def extract_3d_volume(img_data, m_idx, j_idx, p_idx, file_code, dim1):
    if img_data.ndim == 3:
        return img_data

    # For 7D arrays from load_nii_img
    if file_code in ['SE', 'SCSE']:
        # shape is (d1, d2, d3, 1, 1, channels, 1)
        return img_data[:, :, :, 0, 0, p_idx, 0]
    elif file_code in ['SESPM', 'SCSESPM']:
        # shape is (d1, d2, d3, 1, 1, channels, 1)
        return img_data[:, :, :, 0, 0, p_idx, 0]
    elif file_code in ['SPM', 'SCSPM']:
        if dim1 == 3:
            return img_data[:, :, :, 0, 0, 0, 0]
        elif dim1 == 4:
            # Replicates MATLAB's one_echo_nii.img(:,:,:,p)
            return img_data[:, :, :, p_idx, 0, 0, 0]
        elif dim1 == 5:
            # shape is (d1, d2, d3, 1, channels, 1, 1)
            return img_data[:, :, :, 0, p_idx, 0, 0]
        else:
            return img_data[:, :, :, 0, 0, 0, 0]
    else:
        # shape is (d1, d2, d3, 1, channels, 1, 1)
        return img_data[:, :, :, 0, p_idx, 0, 0]

def fm_split_rescale(data):
    file_code = data['file_code']
    root_dir = data['root_dir']
    readfile_dirs = data['readfile_dirs']
    n_channels = data['n_channels']
    phase_range = data['phase_range']
    echoes_to_use = data['echoes_to_use']
    n_echoes_to_use = data['n_echoes_to_use']
    fnCurrentMagImages = data['fnCurrentMagImages']
    fnCurrentPhaseImages = data['fnCurrentPhaseImages']
    nii_pixdim = data['nii_pixdim']
    nii_dim = data['nii_dim']
    reform_subdir = data['reform_subdir']

    if file_code in ['SESPM', 'SCSPM', 'SPM']:
        pm = 2
    else:
        pm = 1

    # Check that data exists to be split
    for m in range(1, pm + 1):
        for j in range(n_echoes_to_use):
            n = echoes_to_use[j]
            if file_code in ['SE', 'SCSE']:
                readfile_dir = readfile_dirs[n - 1]
            elif file_code in ['SESPM', 'SCSESPM']:
                readfile_dir = readfile_dirs[2 * (n - 1) + m - 1]
            elif file_code in ['SPM', 'SCSPM']:
                readfile_dir = readfile_dirs[m - 1]
            else:
                readfile_dir = readfile_dirs[0] if isinstance(readfile_dirs, (list, tuple)) else readfile_dirs

            readfile = os.path.join(root_dir, readfile_dir, reform_subdir, 'Image.nii')
            if not os.path.exists(readfile):
                raise FileNotFoundError(f"Couldn't find {readfile}")
            else:
                print(f"Analysing {readfile}")

    print(f"Writing fieldmaps to {data['writefile_dir']}")

    split = 'no'
    do_all = data.get('do_all_remaing_processing_stages', 'no')
    # Determine if files already exist
    for j in range(n_echoes_to_use):
        for m in range(n_channels):
            mag_file = fnCurrentMagImages[m][j]
            phase_file = fnCurrentPhaseImages[m][j]
            if not mag_file or not os.path.exists(mag_file) or not phase_file or not os.path.exists(phase_file) or do_all == 'yes':
                split = 'yes'
                data['do_all_remaing_processing_stages'] = 'yes'
                break
        if split == 'yes':
            break

    if split == 'yes':
        print(' * - separating echoes and phase and magnitude data')
        for m in [1, 2]: # m=1 magnitude, m=2 phase
            for j in range(n_echoes_to_use):
                n = echoes_to_use[j]
                if file_code in ['SE', 'SCSE']:
                    readfile_dir = readfile_dirs[n - 1]
                elif file_code in ['SESPM', 'SCSESPM']:
                    readfile_dir = readfile_dirs[2 * (n - 1) + m - 1]
                elif file_code in ['SPM', 'SCSPM']:
                    readfile_dir = readfile_dirs[m - 1]
                else:
                    readfile_dir = readfile_dirs[0] if isinstance(readfile_dirs, (list, tuple)) else readfile_dirs

                readfile = os.path.join(root_dir, readfile_dir, reform_subdir, 'Image.nii')

                if file_code in ['SE', 'SCSE']:
                    one_echo_nii = load_nii(
                        readfile,
                        img_idx=np.arange(1, int(nii_dim[4]) + 1),
                        dim5_idx=m
                    )
                elif file_code in ['SPM', 'SCSPM']:
                    dir_name = readfile_dirs[0] if isinstance(readfile_dirs, (list, tuple)) else readfile_dirs
                    hdr, _, _, _ = load_nii_hdr(os.path.join(root_dir, dir_name, reform_subdir, 'Image.nii'))
                    dim1 = hdr.dime.dim[0]
                    if dim1 == 3:
                        one_echo_nii = load_nii(readfile)
                    elif dim1 == 4:
                        one_echo_nii = load_nii(
                            readfile,
                            img_idx=np.arange(1, int(nii_dim[4]) + 1)
                        )
                    elif dim1 == 5:
                        one_echo_nii = load_nii(
                            readfile,
                            img_idx=n,
                            dim5_idx=np.arange(1, int(nii_dim[5]) + 1)
                        )
                    else:
                        one_echo_nii = load_nii(readfile)
                elif file_code in ['SESPM', 'SCSESPM']:
                    one_echo_nii = load_nii(readfile)
                else:
                    if isinstance(readfile_dirs, (list, tuple)):
                        dir_path = os.path.join(root_dir, readfile_dirs[0], reform_subdir, 'Image.nii')
                    else:
                        dir_path = os.path.join(root_dir, readfile_dirs, reform_subdir, 'Image.nii')
                    one_echo_nii = load_nii(
                        dir_path,
                        img_idx=n,
                        dim5_idx=np.arange(1, int(nii_dim[5]) + 1),
                        dim6_idx=m
                    )

                hdr_full, _, _, _ = load_nii_hdr(readfile)
                dim1 = hdr_full.dime.dim[0]

                for p in range(n_channels):
                    img_data = one_echo_nii.img
                    vol_3d = extract_3d_volume(img_data, m, j, p, file_code, dim1)
                    
                    one_echo_one_channel_PorM_nii = make_nii(vol_3d.astype(np.float32))

                    if m == 2:
                        # Rescale phase to 0 -> 2*PI
                        denom = phase_range[1] - phase_range[0]
                        if denom != 0:
                            one_echo_one_channel_PorM_nii.img = 2.0 * np.pi * (one_echo_one_channel_PorM_nii.img - phase_range[0]) / denom
                        else:
                            one_echo_one_channel_PorM_nii.img = np.zeros_like(one_echo_one_channel_PorM_nii.img)
                        centre_and_save_nii(one_echo_one_channel_PorM_nii, fnCurrentPhaseImages[p][j], nii_pixdim)
                    else:
                        centre_and_save_nii(one_echo_one_channel_PorM_nii, fnCurrentMagImages[p][j], nii_pixdim)
    else:
        print(' - separated data found')

    return data
