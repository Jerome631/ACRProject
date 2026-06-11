import os
import sys
import numpy as np
from load_nii import load_nii
from make_nii import make_nii
from centre_and_save_nii import centre_and_save_nii

def fm_jump_correct_fieldmaps(data):
    extension = data['extension']
    TEs = data['TEs']
    method = data['method']
    n_channels = data['n_channels']
    fnCurrentFieldmaps = data['fnCurrentFieldmaps']
    fnBetMaskSubSmall = data['fnBetMaskSubSmall']
    nii_pixdim = data['nii_pixdim']
    nii_dim = data['nii_dim']
    do_all = data.get('do_all_remaing_processing_stages', 'no')

    n_fieldmaps_to_correct = len(fnCurrentFieldmaps)
    number_of_jcs_to_do = 1

    correct_jumps = 'no'
    fnCurrentFieldmapsJC = [[None for _ in range(number_of_jcs_to_do)] for _ in range(n_fieldmaps_to_correct)]

    for m in range(n_fieldmaps_to_correct):
        for j in range(number_of_jcs_to_do):
            orig_file = fnCurrentFieldmaps[m][j]
            jc_file = orig_file.replace(extension, f'_jc{extension}')
            fnCurrentFieldmapsJC[m][j] = jc_file
            if not os.path.exists(jc_file) or do_all == 'yes':
                correct_jumps = 'yes'
                data['do_all_remaing_processing_stages'] = 'yes'

    if correct_jumps == 'yes':
        any_jumps_corrected = 'no'
        print(' * - checking single-value fieldmaps for different phase jumps in contributing phase maps, slice by slice, on the basis of their difference from the global median fieldmap')

        # Convert TE difference from microseconds to seconds
        one_phase_jump_radsps = (2.0 * np.pi) / ((TEs[1] - TEs[0]) / 1000000.0)

        x = int(nii_dim[1])
        y = int(nii_dim[2])
        z = int(nii_dim[3])

        all_fieldmaps = np.zeros((x, y, z, n_fieldmaps_to_correct, number_of_jcs_to_do))

        for m in range(n_fieldmaps_to_correct):
            for n in range(number_of_jcs_to_do):
                fieldmap_nii = load_nii(fnCurrentFieldmaps[m][n])
                img_data = fieldmap_nii.img
                if img_data.ndim > 3:
                    vol_3d = img_data[(slice(None), slice(None), slice(None)) + (0,) * (img_data.ndim - 3)]
                else:
                    vol_3d = img_data
                all_fieldmaps[:, :, :, m, n] = vol_3d

        mask_nii = load_nii(fnBetMaskSubSmall)
        nz_inds = (mask_nii.img != 0)

        for m in range(n_fieldmaps_to_correct):
            for n in range(number_of_jcs_to_do):
                one_fm = all_fieldmaps[:, :, :, m, n]
                if method == 'sep-channel':
                    nz_inds = (one_fm != 0)
                
                if np.any(nz_inds):
                    mean_one_fm = np.nanmean(one_fm[nz_inds])
                else:
                    mean_one_fm = 0.0

                n_jumps = np.round(mean_one_fm / one_phase_jump_radsps)
                if np.isnan(n_jumps):
                    n_jumps = 0.0

                if n_jumps != 0.0:
                    all_fieldmaps[:, :, :, m, n] = one_fm - n_jumps * one_phase_jump_radsps
                    any_jumps_corrected = 'yes'

        if any_jumps_corrected == 'yes':
            print(' * - jumps were removed')
        else:
            print(' * - no jumps identified')

        for m in range(n_fieldmaps_to_correct):
            for n in range(number_of_jcs_to_do):
                fieldmap_nii = make_nii(all_fieldmaps[:, :, :, m, n].astype(np.float32))
                try:
                    centre_and_save_nii(fieldmap_nii, fnCurrentFieldmapsJC[m][n], nii_pixdim)
                except Exception as e:
                    print(f"Error saving fieldmap: {e}")
    else:
        print(' - jump-corrected fieldmaps found')

    data['fnCurrentFieldmaps'] = fnCurrentFieldmapsJC
    return data
