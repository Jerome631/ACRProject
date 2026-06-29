import os
import sys
import numpy as np
from load_nii import load_nii
from make_nii import make_nii
from centre_and_save_nii import centre_and_save_nii

def fm_median_mean_std(data):
    echoes_to_use = data['echoes_to_use']
    fnCurrentFieldmaps = data['fnCurrentFieldmaps']
    fnAllMags = data['fnAllMags']
    fnReconMag = data['fnReconMag']
    fnMeanFM = data['fnMeanFM']
    fnWMeanFM = data['fnWMeanFM']
    fnTWMeanFM = data['fnTWMeanFM']
    fnMedianFM = data['fnMedianFM']
    fnWMedianFM = data['fnWMedianFM']
    fnMedianFiltMedianFM = data['fnMedianFiltMedianFM']
    fnStdFM = data['fnStdFM']
    fnCVMap = data['fnCVMap']
    fnNCMap = data['fnNCMap']
    fnNzMap = data['fnNzMap']
    fnBetMaskSubLarge = data['fnBetMaskSubLarge']
    n_channels = data['n_channels']
    nii_pixdim = data['nii_pixdim']
    do_all = data.get('do_all_remaing_processing_stages', 'no')

    calculate_means = 'no'
    if not os.path.exists(fnTWMeanFM[0]) or not os.path.exists(fnStdFM[0]) or do_all == 'yes':
        calculate_means = 'yes'
        data['do_all_remaing_processing_stages'] = 'yes'

    if calculate_means == 'yes':
        # Load all fieldmaps
        for m in range(n_channels):
            fm_file = fnCurrentFieldmaps[m][0]
            print(f"Loading {fm_file}")
            fieldmap_nii = load_nii(fm_file)
            img_data = fieldmap_nii.img
            if img_data.ndim > 3:
                vol_3d = img_data[(slice(None), slice(None), slice(None)) + (0,) * (img_data.ndim - 3)]
            else:
                vol_3d = img_data

            if m == 0:
                x, y, z = vol_3d.shape
                all_fieldmaps = np.zeros((x, y, z, n_channels))
            all_fieldmaps[:, :, :, m] = vol_3d

        all_mags_nii = load_nii(fnAllMags)
        mags_img = all_mags_nii.img
        # weightings: magnitude values for first echo, shape (x, y, z, n_channels)
        if mags_img.ndim > 4:
            weightings = mags_img[:, :, :, :, 0]
        else:
            weightings = mags_img

        print(' * - sorting fieldmap values and weights')
        # Sort along the 4th dimension (axis 3)
        fm_sort_indices = np.argsort(all_fieldmaps, axis=3)
        all_fieldmaps_sorted = np.sort(all_fieldmaps, axis=3)

        # Vectorized weightings sort matching MATLAB loop
        weightings_sorted = np.take_along_axis(weightings, fm_sort_indices, axis=3)

        # Set the number of channels to use
        if n_channels <= 4:
            cl_py = 0
            ch_py = n_channels
        else:
            cl_py = int(np.round(n_channels / 4.0))
            ch_py = int(np.round(3.0 * n_channels / 4.0))

        print(' * - creating a trimmed, weighted mean fieldmap')
        fms_slice = all_fieldmaps_sorted[:, :, :, cl_py:ch_py]
        weights_slice = weightings_sorted[:, :, :, cl_py:ch_py]

        denom = np.mean(weights_slice, axis=3)
        twmean_fieldmap = np.zeros_like(denom)
        valid_mask = (denom != 0)
        twmean_fieldmap[valid_mask] = np.mean(fms_slice * weights_slice, axis=3)[valid_mask] / denom[valid_mask]

        twmean_fieldmap_nii = make_nii(twmean_fieldmap.astype(np.float32))
        centre_and_save_nii(twmean_fieldmap_nii, fnTWMeanFM[0], nii_pixdim)

        print(' * - creating a map of trimmed std')
        slice_size = ch_py - cl_py
        ddof = 1 if slice_size > 1 else 0
        std_fieldmap = np.std(fms_slice, axis=3, ddof=ddof)

        std_fieldmap_nii = make_nii(std_fieldmap.astype(np.float32))
        centre_and_save_nii(std_fieldmap_nii, fnStdFM[0], nii_pixdim)

    else:
        print(' - found trimmed weighted mean and stdev fieldmaps')

    data['fnCurrentFieldmaps'] = fnTWMeanFM
    return data
