import os
import sys
import numpy as np
from load_nii import load_nii
from make_nii import make_nii
from centre_and_save_nii import centre_and_save_nii

def fm_mask_fm(data):
    extension = data['extension']
    fnBetMaskSubLarge = data['fnBetMaskSubLarge']
    fnCurrentFieldmaps = data['fnCurrentFieldmaps']
    nii_pixdim = data['nii_pixdim']
    do_all = data.get('do_all_remaing_processing_stages', 'no')

    number_of_masks_to_make = 1
    n_fieldmaps_to_correct = 1

    mask = 'no'
    fnCurrentFieldmapsBet = [[None for _ in range(number_of_masks_to_make)] for _ in range(n_fieldmaps_to_correct)]

    for m in range(n_fieldmaps_to_correct):
        for j in range(number_of_masks_to_make):
            orig_file = fnCurrentFieldmaps[m][j]
            bet_file = orig_file.replace(extension, f'_bet{extension}')
            fnCurrentFieldmapsBet[m][j] = bet_file
            if not os.path.exists(bet_file) or do_all == 'yes':
                mask = 'yes'
                data['do_all_remaing_processing_stages'] = 'yes'

    if mask == 'yes':
        print(' * - masking fieldmap(s)')
        mask_nii = load_nii(fnBetMaskSubLarge)
        for m in range(n_fieldmaps_to_correct):
            for j in range(number_of_masks_to_make):
                one_fm_nii = load_nii(fnCurrentFieldmaps[m][j])
                mask_bool = (mask_nii.img == 0)
                if mask_bool.shape != one_fm_nii.img.shape:
                    mask_bool = mask_bool.reshape(one_fm_nii.img.shape)
                one_fm_nii.img[mask_bool] = 0
                centre_and_save_nii(one_fm_nii, fnCurrentFieldmapsBet[m][j], nii_pixdim)
    else:
        print(' - mask found')

    data['fnCurrentFieldmaps'] = fnCurrentFieldmapsBet
    return data
