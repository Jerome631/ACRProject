import os
import sys
import numpy as np
from load_nii import load_nii
from make_nii import make_nii
from centre_and_save_nii import centre_and_save_nii
from smoothn import smoothn

def fm_smooth(data):
    extension = data['extension']
    fnCurrentFieldmaps = data['fnCurrentFieldmaps']
    nii_pixdim = data['nii_pixdim']
    do_all = data.get('do_all_remaing_processing_stages', 'no')

    number_of_fms_to_smooth = 1
    
    smooth_fieldmaps = 'no'
    fnCurrentFieldmapsS = [None for _ in range(number_of_fms_to_smooth)]

    for j in range(number_of_fms_to_smooth):
        orig_file = fnCurrentFieldmaps[j]
        s_file = orig_file.replace(extension, f'_s{extension}')
        fnCurrentFieldmapsS[j] = s_file
        if not os.path.exists(s_file) or do_all == 'yes':
            smooth_fieldmaps = 'yes'
            data['do_all_remaing_processing_stages'] = 'yes'

    if smooth_fieldmaps == 'yes':
        smoothing_kernel = data.get('smoothing_kernel', 0)
        print(f" * - smoothing field map(s) using the smoothn function with a {smoothing_kernel} voxel kernel")
        
        for j in range(number_of_fms_to_smooth):
            one_fieldmap_nii = load_nii(fnCurrentFieldmaps[j])
            
            img_data = one_fieldmap_nii.img
            if img_data.ndim > 3:
                vol_3d = img_data[(slice(None), slice(None), slice(None)) + (0,) * (img_data.ndim - 3)]
            else:
                vol_3d = img_data

            # turn zeros to NaN to omit them from smoothing
            one_fieldmap_NaN = vol_3d.astype(float).copy()
            one_fieldmap_NaN[vol_3d == 0] = np.nan
            
            # call smoothn (which handles NaNs automatically)
            smoothed, _, _ = smoothn(one_fieldmap_NaN)
            
            # turn NaNs back to 0s
            smoothed[np.isnan(smoothed)] = 0.0
            
            one_fieldmap_nii.img = smoothed.astype(np.float32)
            centre_and_save_nii(one_fieldmap_nii, fnCurrentFieldmapsS[j], nii_pixdim)
    else:
        print(' - smoothed field map(s) found')

    data['fnCurrentFieldmaps'] = fnCurrentFieldmapsS
    return data
