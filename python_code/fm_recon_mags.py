import os
import numpy as np
from load_nii import load_nii
from make_nii import make_nii
from centre_and_save_nii import centre_and_save_nii

def fm_recon_mags(data):
    fnReconMag = data['fnReconMag']
    fnAllMags = data['fnAllMags']
    n_channels = data['n_channels']
    n_echoes_to_use = data['n_echoes_to_use']
    fnCurrentMagImages = data['fnCurrentMagImages']
    do_all = data.get('do_all_remaing_processing_stages', 'no')

    reco_mag = 'no'
    if not os.path.exists(fnReconMag) or not os.path.exists(fnAllMags) or do_all == 'yes':
        reco_mag = 'yes'
        data['do_all_remaing_processing_stages'] = 'yes'

    if reco_mag == 'yes':
        print(' * - reconstructing magnitude image')
        nii_pixdim = data['nii_pixdim']
        nii_dim = data['nii_dim']
        x = int(nii_dim[1])
        y = int(nii_dim[2])
        z = int(nii_dim[3])

        reco_image = np.zeros((x, y, z))
        all_mags = np.zeros((x, y, z, n_channels, n_echoes_to_use))

        for j in range(n_echoes_to_use):
            for m in range(n_channels):
                one_mag_file = fnCurrentMagImages[m][j]
                one_mag_nii = load_nii(one_mag_file)
                img_data = one_mag_nii.img

                if img_data.ndim > 3:
                    vol_3d = img_data[(slice(None), slice(None), slice(None)) + (0,) * (img_data.ndim - 3)]
                else:
                    vol_3d = img_data

                all_mags[:, :, :, m, j] = vol_3d.astype(float)
                if j == 0:
                    reco_image += (vol_3d.astype(float) ** 2)

        reco_image = reco_image ** 0.5
        reco_image_nii = make_nii(reco_image.astype(np.float32))
        all_mags_nii = make_nii(all_mags.astype(np.float32))

        centre_and_save_nii(reco_image_nii, fnReconMag, nii_pixdim)
        centre_and_save_nii(all_mags_nii, fnAllMags, nii_pixdim)
    else:
        print(' - reconstructed magnitude image found')

    return data
