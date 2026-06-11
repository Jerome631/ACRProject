import os
import sys
import shutil
import gzip
import subprocess
from unix_format import unix_format
from load_nii import load_nii
from save_nii import save_nii
from centre_header_file import centre_header_file
from set_nii_voxel_size import set_nii_voxel_size

def gunzip_file(filepath):
    # Unzip if filepath.gz exists
    if os.path.exists(filepath + '.gz'):
        with gzip.open(filepath + '.gz', 'rb') as f_in:
            with open(filepath, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        os.remove(filepath + '.gz')
    # Or if it ends in .nii and .nii.gz exists
    elif filepath.endswith('.nii') and os.path.exists(filepath[:-4] + '.nii.gz'):
        with gzip.open(filepath[:-4] + '.nii.gz', 'rb') as f_in:
            with open(filepath, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        os.remove(filepath[:-4] + '.nii.gz')

def fm_make_mask(data):
    fnReconMag = data['fnReconMag']
    fnCurrentMagImages = data['fnCurrentMagImages']
    fnBetImSmall = data['fnBetImSmall']
    fnBetImLarge = data['fnBetImLarge']
    fnBetMaskSmall = data['fnBetMaskSmall']
    fnBetMaskLarge = data['fnBetMaskLarge']
    fnBetMaskSubSmall = data['fnBetMaskSubSmall']
    fnBetMaskSubLarge = data['fnBetMaskSubLarge']
    fnBetMaskSep = data['fnBetMaskSep']
    method = data['method']
    n_channels = data['n_channels']
    n_echoes_to_use = data['n_echoes_to_use']
    echoes_to_use = data['echoes_to_use']
    BET_f_small_mask = data['BET_f_small_mask']
    BET_f_large_mask = data['BET_f_large_mask']
    BET_f_sep_mask = data['BET_f_sep_mask']
    root_dir = data['root_dir']
    unzip_command = data.get('unzip_command', '')
    nii_pixdim = data['nii_pixdim']
    do_all = data.get('do_all_remaing_processing_stages', 'no')

    is_pc = (sys.platform == 'win32')
    if not is_pc:
        # Linux / MacOS
        root_dir = unix_format(root_dir)
        bet_call = 'bet'
    else:
        # Windows
        bet_call = 'bet_32R'

    # Check if mask files already exist
    bet_needed = 'no'
    if not os.path.exists(fnBetMaskSubSmall) or not os.path.exists(fnBetMaskSubLarge) or do_all == 'yes':
        bet_needed = 'yes'

    if bet_needed == 'yes':
        for i in [1, 2]:
            if i == 1:
                print(' * - creating a small brain mask with BET from the first echo magnitude image')
                fnBetIm = fnBetImSmall
                BET_f = BET_f_small_mask;
                fnBetMask = fnBetMaskSmall
                fnBetMaskSub = fnBetMaskSubSmall
            else:
                print(' * - creating a large brain mask with BET from the first echo magnitude image')
                fnBetIm = fnBetImLarge
                BET_f = BET_f_large_mask
                fnBetMask = fnBetMaskLarge
                fnBetMaskSub = fnBetMaskSubLarge

            # FSL bet call
            bet_command = f'/usr/local/fsl/bin/bet {unix_format(fnReconMag)} {unix_format(fnBetIm)} -f {BET_f} -m'
            env = os.environ.copy()
            env['LD_LIBRARY_PATH'] = '/usr/lib/fsl:/usr/lib/fsl'
            subprocess.run(bet_command, env=env, shell=True, capture_output=True, text=True)

            if unzip_command:
                subprocess.run(unzip_command, shell=True, capture_output=True, text=True)

            gunzip_file(fnBetIm)

            # Locate bet mask output and move to fnBetMaskSub
            possible_masks = [
                fnBetMask,
                fnBetMask + '.gz',
                fnBetIm.replace('.nii', '_mask.nii'),
                fnBetIm.replace('.nii', '_mask.nii.gz'),
                fnBetIm + '_mask.nii',
                fnBetIm + '_mask.nii.gz',
                fnBetIm.replace('.nii', '.nii_mask.nii'),
                fnBetIm.replace('.nii', '.nii_mask.nii.gz')
            ]

            mask_found = None
            for pm in possible_masks:
                if os.path.exists(pm):
                    mask_found = pm
                    break

            if mask_found:
                if mask_found.endswith('.gz'):
                    unzipped_mask = mask_found[:-3]
                    with gzip.open(mask_found, 'rb') as f_in:
                        with open(unzipped_mask, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    os.remove(mask_found)
                    mask_found = unzipped_mask
                
                shutil.move(mask_found, fnBetMaskSub)

            if os.path.exists(fnBetIm):
                centre_header_file(fnBetIm)
                set_nii_voxel_size(fnBetIm, nii_pixdim)

            if os.path.exists(fnBetMaskSub):
                centre_header_file(fnBetMaskSub)
                set_nii_voxel_size(fnBetMaskSub, nii_pixdim)
    else:
        print(' - mask found')

    # Check sep-channel masks
    bet_sep_needed = 'no'
    if method in ['sep-channel', 'phase-imaging']:
        for m in range(n_channels):
            for j in range(n_echoes_to_use):
                sep_mask_file = fnBetMaskSep[m][j]
                if not sep_mask_file or not os.path.exists(sep_mask_file) or do_all == 'yes':
                    bet_sep_needed = 'yes'
                    data['do_all_remaing_processing_stages'] = 'yes'
                    break
            if bet_sep_needed == 'yes':
                break

    if bet_sep_needed == 'yes':
        print(' * - creating separate BET masks for each channel')
        global_masked_image_nii = load_nii(fnBetMaskSubLarge)
        for m in range(n_channels):
            for j in range(n_echoes_to_use):
                mag_file = fnCurrentMagImages[m][j]
                mag_file_temp = mag_file.replace('.nii', '_temp.nii')
                mag_file_bet = mag_file.replace('.nii', '_bet.nii')
                mag_file_bet_mask = mag_file.replace('.nii', '_bet_mask.nii')

                one_channel_one_echo_nii = load_nii(mag_file)
                try:
                    mask_bool = (global_masked_image_nii.img == 0)
                    if mask_bool.shape != one_channel_one_echo_nii.img.shape:
                        mask_bool = mask_bool.reshape(one_channel_one_echo_nii.img.shape)
                    one_channel_one_echo_nii.img[mask_bool] = 0
                except Exception as e:
                    print(f"Masking error: {e}")

                save_nii(one_channel_one_echo_nii, mag_file_temp)

                bet_command = f'{bet_call} {unix_format(mag_file_temp)} {unix_format(mag_file_bet)} -f {BET_f_sep_mask} -m'
                env = os.environ.copy()
                env['LD_LIBRARY_PATH'] = '/usr/lib/fsl:/usr/lib/fsl'
                subprocess.run(bet_command, env=env, shell=True, capture_output=True, text=True)

                if unzip_command:
                    subprocess.run(unzip_command, shell=True, capture_output=True, text=True)

                gunzip_file(mag_file_bet)

                sep_mask_dest = fnBetMaskSep[m][j]
                possible_sep_masks = [
                    mag_file_bet_mask,
                    mag_file_bet_mask + '.gz',
                    mag_file_bet.replace('.nii', '_mask.nii'),
                    mag_file_bet.replace('.nii', '_mask.nii.gz'),
                    mag_file_bet + '_mask.nii',
                    mag_file_bet + '_mask.nii.gz',
                    mag_file_bet.replace('.nii', '.nii_mask.nii'),
                    mag_file_bet.replace('.nii', '.nii_mask.nii.gz'),
                    mag_file_temp.replace('_temp.nii', '_bet_mask.nii'),
                    mag_file_temp.replace('_temp.nii', '_bet_mask.nii.gz'),
                    mag_file_temp.replace('_temp.nii', '_bet_temp_mask.nii')
                ]

                sep_mask_found = None
                for sm in possible_sep_masks:
                    if os.path.exists(sm):
                        sep_mask_found = sm
                        break

                if sep_mask_found:
                    if sep_mask_found.endswith('.gz'):
                        unzipped_sm = sep_mask_found[:-3]
                        with gzip.open(sep_mask_found, 'rb') as f_in:
                            with open(unzipped_sm, 'wb') as f_out:
                                shutil.copyfileobj(f_in, f_out)
                        os.remove(sep_mask_found)
                        sep_mask_found = unzipped_sm
                    
                    shutil.move(sep_mask_found, sep_mask_dest)

                # Clean up temporary files
                for tf in [mag_file_bet, mag_file_temp, mag_file_bet.replace('.nii', '.nii.gz'), mag_file_temp.replace('.nii', '.nii.gz')]:
                    if os.path.exists(tf):
                        os.remove(tf)

                if os.path.exists(sep_mask_dest):
                    centre_header_file(sep_mask_dest)
                    set_nii_voxel_size(sep_mask_dest, nii_pixdim)
    else:
        print(' - mask found')

    return data
