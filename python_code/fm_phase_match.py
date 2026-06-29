import os
import numpy as np
from load_nii import load_nii
from make_nii import make_nii
from centre_and_save_nii import centre_and_save_nii
from vector import vector

def fm_phase_match(data):
    n_channels = data['n_channels']
    echoes_to_use = data['echoes_to_use']
    n_echoes_to_use = data['n_echoes_to_use']
    fnCurrentPhaseImages = data['fnCurrentPhaseImages']
    fnCurrentPhaseImagesPC = data['fnCurrentPhaseImagesPC']
    fnCurrentPhaseOffsets = data['fnCurrentPhaseOffsets']
    fnCombPhase = data['fnCombPhase']
    fnCombMag = data['fnCombMag']
    fnAllMags = data['fnAllMags']
    nii_pixdim = data['nii_pixdim']
    nii_dim = data['nii_dim']
    phase_cor_method = data.get('phase_cor_method', 'hammond')
    do_all = data.get('do_all_remaing_processing_stages', 'no')

    match_phase = 'no'
    for m in range(n_channels):
        for j in range(n_echoes_to_use):
            pc_file = fnCurrentPhaseImagesPC[m][j]
            comb_phase_file = fnCombPhase[j]
            comb_mag_file = fnCombMag[j]
            if not pc_file or not os.path.exists(pc_file) or \
               not comb_phase_file or not os.path.exists(comb_phase_file) or \
               not comb_mag_file or not os.path.exists(comb_mag_file) or \
               do_all == 'yes':
                match_phase = 'yes'
                data['do_all_remaing_processing_stages'] = 'yes'
                break
        if match_phase == 'yes':
            break

    if match_phase == 'yes':
        print(' * - matching the phase images at the first echo time and creating a combined phase image')
        all_mags_nii = load_nii(fnAllMags)

        x = int(nii_dim[1])
        y = int(nii_dim[2])
        z = int(nii_dim[3])

        all_phase_images = np.zeros((x, y, z, n_channels, n_echoes_to_use))

        for m in range(n_channels):
            for j in range(n_echoes_to_use):
                one_echo_one_channel_p_nii = load_nii(fnCurrentPhaseImages[m][j])
                vol_3d = one_echo_one_channel_p_nii.img
                if vol_3d.ndim > 3:
                    vol_3d = vol_3d[(slice(None), slice(None), slice(None)) + (0,) * (vol_3d.ndim - 3)]
                all_phase_images[:, :, :, m, j] = vol_3d

        # Balance the channel phases
        for m in range(n_channels):
            for j in range(n_echoes_to_use):
                if phase_cor_method == 'hammond':
                    if j == 0:
                        COM = [x // 2, y // 2, z // 2]
                        first_echo_one_channel_p = all_phase_images[:, :, :, m, 0]
                    # Hammond: cROI is 3x3x3 around the center
                    phase_in_cROI = np.mean(vector(first_echo_one_channel_p[COM[0]-1:COM[0]+2, COM[1]-1:COM[1]+2, COM[2]-1:COM[2]+2]))
                    all_phase_images[:, :, :, m, j] -= phase_in_cROI

                elif phase_cor_method == 'schaefer':
                    if j == 0 and m == 0:
                        product = np.ones((x, y, z))
                        for mm in range(n_channels):
                            mag_img = all_mags_nii.img
                            if mag_img.ndim > 4:
                                mag_vol = mag_img[:, :, :, mm, 0]
                            else:
                                mag_vol = mag_img[:, :, :, mm]
                            product = product * mag_vol
                        linindex = np.argmax(vector(product))
                        indx, indy, indz = np.unravel_index(linindex, product.shape)
                        COM = [indx, indy, indz]
                    if j == 0:
                        first_echo_one_channel_p = all_phase_images[:, :, :, m, 0]
                    phase_in_cROI = first_echo_one_channel_p[COM[0], COM[1], COM[2]]
                    all_phase_images[:, :, :, m, j] -= phase_in_cROI

                elif phase_cor_method == 'robinson':
                    if j == 0:
                        pi_offsets_nii = load_nii(fnCurrentPhaseOffsets[m])
                    pi_offsets_img = pi_offsets_nii.img
                    if pi_offsets_img.ndim > 3:
                        pi_offsets_img = pi_offsets_img[(slice(None), slice(None), slice(None)) + (0,) * (pi_offsets_img.ndim - 3)]
                    all_phase_images[:, :, :, m, j] -= pi_offsets_img
                else:
                    # Not correcting for phase offsets
                    pass

        # Create combined complex images
        # Ensure all_mags_nii.img has proper shape matching all_phase_images
        mag_data = all_mags_nii.img
        # If mag_data is 3D or 4D, expand/reshape it to match (x, y, z, n_channels, n_echoes_to_use)
        if mag_data.ndim == 3:
            # Broadcast to channels and echoes
            mag_data_exp = np.tile(mag_data[:, :, :, np.newaxis, np.newaxis], (1, 1, 1, n_channels, n_echoes_to_use))
        elif mag_data.ndim == 4:
            # 4D is usually (x, y, z, channels)
            mag_data_exp = np.tile(mag_data[:, :, :, :, np.newaxis], (1, 1, 1, 1, n_echoes_to_use))
        else:
            mag_data_exp = mag_data

        all_complex = mag_data_exp * np.exp(1j * all_phase_images)

        # Combined phase - weighted mean (summing over axis 3 (channels))
        summed_complex = np.sum(all_complex, axis=3)
        wm_phase = np.angle(summed_complex)
        wm_mag = np.abs(summed_complex)

        for j in range(n_echoes_to_use):
            wm_phase_nii = make_nii(wm_phase[:, :, :, j].astype(np.float32))
            wm_mag_nii = make_nii(wm_mag[:, :, :, j].astype(np.float32))
            
            # Rescale the phase images 0 -> 2*PI (shifting by PI)
            wm_phase_nii.img = wm_phase_nii.img + np.pi
            
            centre_and_save_nii(wm_phase_nii, fnCombPhase[j], nii_pixdim)
            centre_and_save_nii(wm_mag_nii, fnCombMag[j], nii_pixdim)

        # Write out single channel corrected phase images
        for j in range(n_echoes_to_use):
            for m in range(n_channels):
                corr_phase_img = np.angle(all_complex[:, :, :, m, j])
                min_val = np.min(vector(corr_phase_img))
                max_val = np.max(vector(corr_phase_img))
                denom = max_val - min_val
                if denom != 0:
                    corr_phase_img = 2.0 * np.pi * (corr_phase_img - min_val) / denom
                else:
                    corr_phase_img = np.zeros_like(corr_phase_img)
                one_phase_corrected_nii = make_nii(corr_phase_img.astype(np.float32))
                centre_and_save_nii(one_phase_corrected_nii, fnCurrentPhaseImagesPC[m][j], nii_pixdim)
    else:
        print(' - phase-corrected data found')

    data['fnCurrentPhaseImages'] = fnCombPhase
    data['fnCurrentMagImages'] = fnCombMag

    return data
