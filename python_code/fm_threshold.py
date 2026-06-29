import os
import sys
import numpy as np
from load_nii import load_nii
from make_nii import make_nii
from centre_and_save_nii import centre_and_save_nii
from medfilt3 import medfilt3

def fm_threshold(data):
    extension = data['extension']
    fnCurrentFieldmaps = data['fnCurrentFieldmaps']
    nii_pixdim = data['nii_pixdim']
    gradient_thresh = data['gradient_thresh']
    rbw = data['rbw']
    PE_dir = data['PE_dir']
    readout_dimension = data['readout_dimension']
    do_all = data.get('do_all_remaing_processing_stages', 'no')

    number_of_dss_to_do = 1

    threshold_fieldmaps = 'no'
    fnCurrentFieldmapsTh = [None for _ in range(number_of_dss_to_do)]

    for j in range(number_of_dss_to_do):
        orig_file = fnCurrentFieldmaps[j]
        th_file = orig_file.replace(extension, f'_th{extension}')
        fnCurrentFieldmapsTh[j] = th_file
        if not os.path.exists(th_file) or do_all == 'yes':
            threshold_fieldmaps = 'yes'
            data['do_all_remaing_processing_stages'] = 'yes'

    if threshold_fieldmaps == 'yes':
        print(f" * - thresholding field map(s) to limit voxel shift gradients to {gradient_thresh}")
        fieldmap_nii = load_nii(fnCurrentFieldmaps[0])
        img_data = fieldmap_nii.img
        if img_data.ndim > 3:
            vol_3d = img_data[(slice(None), slice(None), slice(None)) + (0,) * (img_data.ndim - 3)]
        else:
            vol_3d = img_data

        # smooth the fieldmap
        vol_3d_nan = vol_3d.astype(float).copy()
        vol_3d_nan[vol_3d == 0] = np.nan
        smoothed = medfilt3(vol_3d_nan, [5, 5, 5])
        smoothed[np.isnan(smoothed)] = 0.0

        x, y, z = smoothed.shape

        # convert the fieldmaps to a voxel-shift map (vsm)
        # readout_dimension - 1 is the axis in Python (1 for X, 2 for Y)
        # fieldmap_nii.hdr.dime.dim[readout_dimension - 1] is equivalent to MATLAB dim(readout_dimension)
        dim_size = fieldmap_nii.hdr.dime.dim[readout_dimension - 1]
        vsm = smoothed * (dim_size / (2.0 * np.pi * rbw))

        vsm_fn = os.path.join(data['writefile_dir'], 'vsm.nii')
        centre_and_save_nii(make_nii(vsm.astype(np.float32)), vsm_fn, nii_pixdim)

        # Calculate voxel shift gradient along PE direction
        if PE_dir in ['y', 'y-']:
            # Equivalent to: circshift(pad(diff(vsm,1,2),[0 1 0],0),[0 1 0])
            vsm_grad_PE = np.zeros_like(vsm)
            vsm_grad_PE[:, 1:, :] = np.diff(vsm, axis=1)
        elif PE_dir in ['x', 'x-']:
            # Equivalent to: circshift(pad(diff(vsm,1,1),[1 0 0],0),[1 0 0])
            vsm_grad_PE = np.zeros_like(vsm)
            vsm_grad_PE[1:, :, :] = np.diff(vsm, axis=0)
        else:
            raise ValueError('Phase-encode direction could not be determined')

        vsm_grad_PE_excess = np.zeros_like(vsm_grad_PE)
        pos_mask = (vsm_grad_PE > gradient_thresh)
        neg_mask = (vsm_grad_PE < -gradient_thresh)
        vsm_grad_PE_excess[pos_mask] = vsm_grad_PE[pos_mask] - gradient_thresh
        vsm_grad_PE_excess[neg_mask] = vsm_grad_PE[neg_mask] + gradient_thresh

        # smooth the excess
        vsm_grad_PE_excess = medfilt3(vsm_grad_PE_excess, [5, 1, 3])

        # normalise vsm_grad_PE_excess
        for i in range(x):
            for k in range(z):
                one_line_excess = vsm_grad_PE_excess[i, :, k].copy()
                one_line_excess_sum = np.sum(one_line_excess)
                nz_mask = (one_line_excess != 0)
                nz_count = np.sum(nz_mask)
                if nz_count > 0:
                    one_line_excess[nz_mask] -= one_line_excess_sum / nz_count
                vsm_grad_PE_excess[i, :, k] = np.cumsum(one_line_excess)

        vsm_thresh = vsm - vsm_grad_PE_excess
        vsm_reduced_fn = os.path.join(data['writefile_dir'], 'vsm_reduced.nii')
        centre_and_save_nii(make_nii(vsm_thresh.astype(np.float32)), vsm_reduced_fn, nii_pixdim)

        # Convert VSM back to fieldmap (using dim[1] which is dim(2) in MATLAB)
        fieldmap_nii.img = (vsm_thresh / (fieldmap_nii.hdr.dime.dim[1] / (2.0 * np.pi * rbw))).astype(np.float32)
        
        for n in range(number_of_dss_to_do):
            centre_and_save_nii(fieldmap_nii, fnCurrentFieldmapsTh[0], nii_pixdim)
    else:
        print(' - thresholded field map(s) found')

    data['fnCurrentFieldmaps'] = fnCurrentFieldmapsTh
    return data
