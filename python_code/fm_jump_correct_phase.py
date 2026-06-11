import os
import sys
import numpy as np
from load_nii import load_nii
from make_nii import make_nii
from centre_and_save_nii import centre_and_save_nii

def fm_jump_correct_phase(data):
    extension = data['extension']
    n_channels = data['n_channels']
    fnCurrentPhaseImages = data['fnCurrentPhaseImages']
    fnCurrentMagImages = data['fnCurrentMagImages']
    fnBetMaskSubSmall = data['fnBetMaskSubSmall']
    fnBetMaskSep = data['fnBetMaskSep']
    nii_pixdim = data['nii_pixdim']
    nii_dim = data['nii_dim']
    echoes_to_use = data['echoes_to_use']
    method = data['method']

    if method in ['conj-diff', 'phase-imaging']:
        n_phase_images_to_jc = 1
    else:
        if data['n_echoes'] > 1:
            n_phase_images_to_jc = 2
        else:
            n_phase_images_to_jc = 1

    correct_jumps = 'no'
    fnCurrentPhaseImagesJC = [[None for _ in range(n_phase_images_to_jc)] for _ in range(n_channels)]

    for m in range(n_channels):
        for j in range(n_phase_images_to_jc):
            orig_file = fnCurrentPhaseImages[m][j]
            jc_file = orig_file.replace(extension, f'_jc{extension}')
            fnCurrentPhaseImagesJC[m][j] = jc_file
            if not os.path.exists(jc_file) or data.get('do_all_remaing_processing_stages', 'no') == 'yes':
                correct_jumps = 'yes'
                data['do_all_remaing_processing_stages'] = 'yes'

    if correct_jumps == 'yes':
        print(' * - correcting for 2PI jumps in between slices')
        any_jumps_corrected = 'no'

        # Traversal order (0-based)
        ns = int(nii_dim[3])
        mid = int(np.ceil(ns / 2.0)) - 1
        slice_check_order = list(range(mid, ns)) + list(range(mid, -1, -1))

        for j in range(n_phase_images_to_jc):
            for m in range(n_channels):
                phase_nii = load_nii(fnCurrentPhaseImages[m][j])
                
                # Check method for mask selection
                if method == 'sep-channel':
                    mask_nii = load_nii(fnBetMaskSep[m][j])
                else:
                    mask_nii = load_nii(fnBetMaskSubSmall)

                one_phase_jump_rads = 2.0 * np.pi
                
                for i in range(ns):
                    curr_slice_idx = slice_check_order[i]
                    next_slice_idx = slice_check_order[i + 1]

                    if curr_slice_idx != ns - 1: # Don't compare top slice to bottom
                        this_slice = phase_nii.img[:, :, curr_slice_idx]
                        next_slice = phase_nii.img[:, :, next_slice_idx].copy()

                        mask_this = mask_nii.img[:, :, curr_slice_idx]
                        mask_next = mask_nii.img[:, :, next_slice_idx]

                        nz_inds_this = (mask_this != 0)
                        nz_inds_next = (mask_next != 0)

                        if np.any(nz_inds_this):
                            mean_this_slice = np.nanmedian(this_slice[nz_inds_this])
                        else:
                            mean_this_slice = np.nan

                        if np.any(nz_inds_next):
                            mean_next_slice = np.nanmedian(next_slice[nz_inds_next])
                        else:
                            mean_next_slice = np.nan

                        n_two_pi_jumps = np.round((mean_this_slice - mean_next_slice) / one_phase_jump_rads)
                        if np.isnan(n_two_pi_jumps):
                            n_two_pi_jumps = 0.0

                        if n_two_pi_jumps != 0.0:
                            next_slice[next_slice != 0] += n_two_pi_jumps * one_phase_jump_rads
                            phase_nii.img[:, :, next_slice_idx] = next_slice
                            any_jumps_corrected = 'yes'

                centre_and_save_nii(phase_nii, fnCurrentPhaseImagesJC[m][j], nii_pixdim)

        if any_jumps_corrected == 'yes':
            print(' * - jumps were removed, writing out amended phase images')
        else:
            print(' - no jumps identified')
    else:
        print(' - jump-corrected phase images found')

    data['fnCurrentPhaseImages'] = fnCurrentPhaseImagesJC
    return data
