import os
import sys
import numpy as np
from load_nii import load_nii
from make_nii import make_nii
from centre_and_save_nii import centre_and_save_nii

def fm_make_fieldmaps(data):
    n_channels = data['n_channels']
    fnCurrentFieldmaps = data['fnCurrentFieldmaps']
    fnCurrentPhaseImages = data['fnCurrentPhaseImages']
    TEs = data['TEs']
    nii_pixdim = data['nii_pixdim']
    method = data['method']
    do_all = data.get('do_all_remaing_processing_stages', 'no')

    make_fieldmaps = 'no'
    number_of_fieldmaps_to_calc = 1

    # Check if fieldmaps already exist
    for m in range(n_channels):
        for j in range(number_of_fieldmaps_to_calc):
            fieldmap_file = fnCurrentFieldmaps[m][j]
            if not fieldmap_file or not os.path.exists(fieldmap_file) or do_all == 'yes':
                make_fieldmaps = 'yes'
                data['do_all_remaing_processing_stages'] = 'yes'
                break
        if make_fieldmaps == 'yes':
            break

    if make_fieldmaps == 'yes':
        if n_channels == 1:
            print(' * - calculating fieldmap(s)')
        else:
            print(' * - calculating single-channel fieldmaps')

        if method in ['phase-match', 'sep-channel']:
            for m in range(n_channels):
                for j in range(number_of_fieldmaps_to_calc):
                    unwrapped_phase1_nii = load_nii(fnCurrentPhaseImages[m][j])
                    unwrapped_phase2_nii = load_nii(fnCurrentPhaseImages[m][j+1])
                    fieldmap_nii = unwrapped_phase1_nii
                    
                    # Convert TE difference from microseconds to seconds
                    te_diff_sec = (TEs[j+1] - TEs[j]) / 1000000.0
                    fieldmap_nii.img = (unwrapped_phase2_nii.img - unwrapped_phase1_nii.img) / te_diff_sec
                    centre_and_save_nii(fieldmap_nii, fnCurrentFieldmaps[m][j], nii_pixdim)

        elif method == 'conj-diff':
            phase_diff_unwrapped_nii = load_nii(fnCurrentPhaseImages[0][0])
            fieldmap_nii = phase_diff_unwrapped_nii
            te_diff_sec = (TEs[1] - TEs[0]) / 1000000.0
            fieldmap_nii.img = phase_diff_unwrapped_nii.img / te_diff_sec

            # In MATLAB, m and j are scoped from the previous check loops:
            # m = n_channels, j = number_of_fieldmaps_to_calc
            m_idx = n_channels - 1
            j_idx = number_of_fieldmaps_to_calc - 1
            centre_and_save_nii(fieldmap_nii, fnCurrentFieldmaps[m_idx][j_idx], nii_pixdim)
    else:
        print(' - fieldmaps found')

    data['fnCurrentFieldmaps'] = fnCurrentFieldmaps
    return data
