import os
import sys
import time
import numpy as np
from load_nii import load_nii
from make_nii import make_nii
from centre_and_save_nii import centre_and_save_nii
from secs2hms import secs2hms

def fm_conj_diff_new(data):
    n_channels = data['n_channels']
    fnCurrentPhaseImages = data['fnCurrentPhaseImages']
    fnCurrentMagImages = data['fnCurrentMagImages']
    fnCombPhaseDiff = data['fnCombPhaseDiff']
    fnCombMagDiff = data['fnCombMagDiff']
    nii_pixdim = data['nii_pixdim']
    nii_dim = data['nii_dim']
    processing_option = data.get('processing_option', 'all_at_once')
    n_echoes_to_use = data['n_echoes_to_use']
    do_all = data.get('do_all_remaing_processing_stages', 'no')

    conj_diff = 'no'
    for n in range(n_echoes_to_use - 1):
        phase_diff_file = fnCombPhaseDiff[n]
        mag_diff_file = fnCombMagDiff[n]
        if not phase_diff_file or not os.path.exists(phase_diff_file) or \
           not mag_diff_file or not os.path.exists(mag_diff_file) or \
           do_all == 'yes':
            conj_diff = 'yes'
            data['do_all_remaing_processing_stages'] = 'yes'
            break

    x = int(nii_dim[1])
    y = int(nii_dim[2])
    z = int(nii_dim[3])

    if conj_diff == 'yes':
        print(' * - creating a combined phase difference image')
        if processing_option == 'slice_by_slice':
            print('   -- not enough memory to process all slices at once')
            ns = z
            for n in range(n_echoes_to_use - 1):
                start_time = time.time()
                wm_phase = np.zeros((x, y, ns))
                wm_mag = np.zeros((x, y, ns))
                
                for k in range(ns):
                    print(f'   -- processing slice {k + 1}')
                    # Prepare all channels/coils for echo n and n+1 on slice k
                    all_phase_images_one_slice = np.zeros((x, y, n_channels, 2))
                    all_mag_images_one_slice = np.zeros((x, y, n_channels, 2))

                    for m in range(n_channels):
                        for j_val in [0, 1]:
                            one_echo_one_channel_m_nii = load_nii(fnCurrentMagImages[m][n + j_val])
                            one_echo_one_channel_p_nii = load_nii(fnCurrentPhaseImages[m][n + j_val])

                            m_img = one_echo_one_channel_m_nii.img
                            p_img = one_echo_one_channel_p_nii.img

                            if m_img.ndim > 3:
                                m_vol = m_img[(slice(None), slice(None), slice(None)) + (0,) * (m_img.ndim - 3)]
                            else:
                                m_vol = m_img

                            if p_img.ndim > 3:
                                p_vol = p_img[(slice(None), slice(None), slice(None)) + (0,) * (p_img.ndim - 3)]
                            else:
                                p_vol = p_img

                            all_phase_images_one_slice[:, :, m, j_val] = p_vol[:, :, k]
                            all_mag_images_one_slice[:, :, m, j_val] = m_vol[:, :, k]

                    # Complex conjugate difference combination across channels
                    # wm_phase = angle(sum(exp(1i*(echo2 - echo1)), axis=3/channels))
                    phase_diff_slice = all_phase_images_one_slice[:, :, :, 1] - all_phase_images_one_slice[:, :, :, 0]
                    wm_phase[:, :, k] = np.angle(np.sum(np.exp(1j * phase_diff_slice), axis=2))
                    
                    # wm_mag = abs(sum((echo2 - echo1), axis=3/channels))
                    mag_diff_slice = all_mag_images_one_slice[:, :, :, 1] - all_mag_images_one_slice[:, :, :, 0]
                    wm_mag[:, :, k] = np.abs(np.sum(mag_diff_slice, axis=2))

                centre_and_save_nii(make_nii(wm_phase.astype(np.float32)), fnCombPhaseDiff[n], nii_pixdim)
                centre_and_save_nii(make_nii(wm_mag.astype(np.float32)), fnCombMagDiff[n], nii_pixdim)
                elapsed = time.time() - start_time
                print(f"Time to create conj-diff phase image = {secs2hms(elapsed)}")

        else: # 'all_at_once'
            for n in range(n_echoes_to_use - 1):
                start_time = time.time()
                all_phase_images = np.zeros((x, y, z, n_channels, 2))
                all_mag_images = np.zeros((x, y, z, n_channels, 2))

                for m in range(n_channels):
                    for j_val in [0, 1]:
                        one_echo_one_channel_p_nii = load_nii(fnCurrentPhaseImages[m][n + j_val])
                        one_echo_one_channel_m_nii = load_nii(fnCurrentMagImages[m][n + j_val])

                        p_img = one_echo_one_channel_p_nii.img
                        m_img = one_echo_one_channel_m_nii.img

                        if p_img.ndim > 3:
                            p_vol = p_img[(slice(None), slice(None), slice(None)) + (0,) * (p_img.ndim - 3)]
                        else:
                            p_vol = p_img

                        if m_img.ndim > 3:
                            m_vol = m_img[(slice(None), slice(None), slice(None)) + (0,) * (m_img.ndim - 3)]
                        else:
                            m_vol = m_img

                        all_phase_images[:, :, :, m, j_val] = p_vol
                        all_mag_images[:, :, :, m, j_val] = m_vol

                # Combined complex conjugate difference
                phase_diff = all_phase_images[:, :, :, :, 1] - all_phase_images[:, :, :, :, 0]
                wm_phase = np.angle(np.sum(np.exp(1j * phase_diff), axis=3))
                
                mag_diff = all_mag_images[:, :, :, :, 1] - all_mag_images[:, :, :, :, 0]
                wm_mag = np.abs(np.sum(mag_diff, axis=3))

                centre_and_save_nii(make_nii(wm_phase.astype(np.float32)), fnCombPhaseDiff[n], nii_pixdim)
                centre_and_save_nii(make_nii(wm_mag.astype(np.float32)), fnCombMagDiff[n], nii_pixdim)
    else:
        print(' - conj-diff data found')

    data['fnCurrentPhaseImages'] = fnCombPhaseDiff
    data['fnCurrentMagImages'] = fnCombMagDiff

    return data
