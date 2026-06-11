import os
import sys
import numpy as np
import subprocess
from scipy.ndimage import distance_transform_edt
from load_nii import load_nii
from make_nii import make_nii
from centre_and_save_nii import centre_and_save_nii
from centre_header_file import centre_header_file
from set_nii_voxel_size import set_nii_voxel_size
from medfilt3 import medfilt3
from vector import vector
from unix_format import unix_format

def nearest_neighbor_interpolate_3d(M):
    mask = (M != 0)
    if not np.any(mask):
        return M
    # Find indices of nearest non-zero elements
    indices = distance_transform_edt(~mask, return_distances=False, return_indices=True)
    return M[indices[0], indices[1], indices[2]]

def fm_despeckle(data):
    extension = data['extension']
    fnCurrentFieldmaps = data['fnCurrentFieldmaps']
    fnStdFM = data['fnStdFM']
    fnBetMaskSubLarge = data['fnBetMaskSubLarge']
    nii_pixdim = data['nii_pixdim']
    do_all = data.get('do_all_remaing_processing_stages', 'no')

    number_of_dss_to_do = 1

    despeckle_fieldmaps = 'no'
    fnCurrentFieldmapsDs = [None for _ in range(number_of_dss_to_do)]

    for j in range(number_of_dss_to_do):
        orig_file = fnCurrentFieldmaps[j]
        ds_file = orig_file.replace(extension, f'_ds{extension}')
        fnCurrentFieldmapsDs[j] = ds_file
        if not os.path.exists(ds_file) or do_all == 'yes':
            despeckle_fieldmaps = 'yes'
            data['do_all_remaing_processing_stages'] = 'yes'

    if despeckle_fieldmaps == 'yes':
        for j in range(number_of_dss_to_do):
            despeckle_method = data['despeckle_method']
            unzip_command = data.get('unzip_command', '')

            if despeckle_method == 'STD':
                print(' * - despeckling field map(s) using the standard deviation to threshold')
                current_fieldmap_nii = load_nii(fnCurrentFieldmaps[0])
                std_fieldmap_nii = load_nii(fnStdFM[0])
                mask_nii = load_nii(fnBetMaskSubLarge)

                mask_voxels = std_fieldmap_nii.img[mask_nii.img == 1]
                std_thresh = 3.0 * np.median(vector(mask_voxels))
                
                ds_fieldmap_nii = current_fieldmap_nii
                ds_fieldmap_nii.img[std_fieldmap_nii.img > std_thresh] = 0.0
                centre_and_save_nii(ds_fieldmap_nii, fnCurrentFieldmapsDs[j], nii_pixdim)

            elif despeckle_method == 'FUGUE':
                print(" * - despeckling field map(s) with FSL's FUGUE (removing rogue pixels)")
                despeckle_threshold = 0.1
                fmap_in = fnCurrentFieldmaps[j]
                fmap_out = fnCurrentFieldmapsDs[j]
                despeckle_command = f'fugue --loadfmap={unix_format(fmap_in)} --despike --despikethreshold={despeckle_threshold} --savefmap={unix_format(fmap_out)}'
                
                env = os.environ.copy()
                env['LD_LIBRARY_PATH'] = '/usr/lib/fsl:/usr/lib/fsl'
                res_obj = subprocess.run(despeckle_command, env=env, shell=True, capture_output=True, text=True)
                if res_obj.returncode != 0:
                    raise RuntimeError(f"Couldn't despeckle: {res_obj.stderr}\n{res_obj.stdout}")

            elif despeckle_method == 'EXTREMES':
                print(' * - despeckling field map(s) by replacing extremes by local median of non-zero values')
                fieldmap_nii = load_nii(fnCurrentFieldmaps[j])
                img_data = fieldmap_nii.img
                if img_data.ndim > 3:
                    vol_3d = img_data[(slice(None), slice(None), slice(None)) + (0,) * (img_data.ndim - 3)]
                else:
                    vol_3d = img_data

                smoothed_fm = medfilt3(vol_3d)
                pct_limits = np.percentile(vector(vol_3d), [5, 95])
                
                ds_img = vol_3d.copy()
                # Use smoothed values for outliers
                ds_img[vol_3d < pct_limits[0]] = smoothed_fm[vol_3d < pct_limits[0]]
                ds_img[vol_3d > pct_limits[1]] = smoothed_fm[vol_3d > pct_limits[1]]
                
                # Restore original zeros if they were changed
                ds_img[vol_3d == 0] = 0.0

                ds_fieldmap_nii = make_nii(ds_img.astype(np.float32))
                centre_and_save_nii(ds_fieldmap_nii, fnCurrentFieldmapsDs[j], nii_pixdim)

            elif despeckle_method == 'INTERP':
                print(' * - despeckling field map(s) with the INTERP/griddata3 method (removing rogue pixels)')
                fieldmap_nii = load_nii(fnCurrentFieldmaps[j])
                img_data = fieldmap_nii.img
                if img_data.ndim > 3:
                    vol_3d = img_data[(slice(None), slice(None), slice(None)) + (0,) * (img_data.ndim - 3)]
                else:
                    vol_3d = img_data

                # Perform optimized fast nearest-neighbor 3D interpolation
                interpolated = nearest_neighbor_interpolate_3d(vol_3d)
                
                ds_fieldmap_nii = make_nii(interpolated.astype(np.float32))
                centre_and_save_nii(ds_fieldmap_nii, fnCurrentFieldmapsDs[j], nii_pixdim)

            if unzip_command:
                subprocess.run(unzip_command, shell=True, capture_output=True, text=True)

            if os.path.exists(fnCurrentFieldmapsDs[j]):
                centre_header_file(fnCurrentFieldmapsDs[j])
                set_nii_voxel_size(fnCurrentFieldmapsDs[j], nii_pixdim)
    else:
        print(' - despeckled field map(s) found')

    data['fnCurrentFieldmaps'] = fnCurrentFieldmapsDs
    return data
