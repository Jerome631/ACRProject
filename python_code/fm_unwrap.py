import os
import sys
import subprocess
from unix_format import unix_format
from load_nii import load_nii
from centre_and_save_nii import centre_and_save_nii

def fm_unwrap(data):
    extension = data['extension']
    n_channels = data['n_channels']
    fnCurrentPhaseImages = data['fnCurrentPhaseImages']
    fnCurrentMagImages = data['fnCurrentMagImages']
    fnReconMag = data['fnReconMag']
    n_echoes = data['n_echoes']
    echoes_to_use = data['echoes_to_use']
    unzip_command = data.get('unzip_command', '')
    unwrap_method = data.get('unwrap_method', 'prelude')
    writefile_dir = data['writefile_dir']
    nii_pixdim = data['nii_pixdim']
    prelude_thresholds = data['prelude_thresholds']
    fsl_prefix = data.get('fsl_prefix', '')
    fsl_suffix = data.get('fsl_suffix', '')
    method = data['method']
    do_all = data.get('do_all_remaing_processing_stages', 'no')

    if method in ['conj-diff', 'phase-imaging']:
        n_phase_images_to_unwrap = 1
        prelude_threshold = prelude_thresholds[0]
    elif method == 'phase-match':
        n_phase_images_to_unwrap = 2
        prelude_threshold = prelude_thresholds[1]
    else:
        if n_echoes > 1:
            n_phase_images_to_unwrap = 2
        else:
            n_phase_images_to_unwrap = 1
        prelude_threshold = prelude_thresholds[0]

    mask_large = data.get('fnBetMaskSubLarge', '')
    if mask_large and os.path.exists(mask_large):
        mask_string = f'-m {mask_large}'
    else:
        mask_string = ''

    # Check if the data has been unwrapped already
    unwrap = 'no'
    fnCurrentPhaseImagesUnwrapped = [[None for _ in range(n_phase_images_to_unwrap)] for _ in range(n_channels)]

    for m in range(n_channels):
        for j in range(n_phase_images_to_unwrap):
            phase_file = fnCurrentPhaseImages[m][j]
            phase_file_unwrapped = phase_file.replace(extension, f'_unwrapped{extension}')
            fnCurrentPhaseImagesUnwrapped[m][j] = phase_file_unwrapped
            if not os.path.exists(phase_file_unwrapped) or do_all == 'yes':
                unwrap = 'yes'
                data['do_all_remaing_processing_stages'] = 'yes'

    if unwrap == 'yes':
        print(' * - unwrapping phase images')
        for m in range(n_channels):
            for j in range(n_phase_images_to_unwrap):
                n = echoes_to_use[j]
                mag_file = fnCurrentMagImages[m][j]
                phase_file = fnCurrentPhaseImages[m][j]
                phase_file_unwrapped = fnCurrentPhaseImagesUnwrapped[m][j]

                if n_channels != 1:
                    print(f"Unwrapping phase images for channel {m + 1}, echo {n}")
                else:
                    print(f"Unwrapping phase echo {n}")

                if unwrap_method == 'prelude':
                    # Prelude command
                    unwrap_command = f'prelude -a {unix_format(mag_file)} -p {unix_format(phase_file)} -o {unix_format(phase_file_unwrapped)} -s -t {int(prelude_threshold)}'
                    env = os.environ.copy()
                    env['LD_LIBRARY_PATH'] = '/usr/lib/fsl:/usr/lib/fsl'
                    
                    if method == 'sep-channel':
                        subprocess.run(unwrap_command, env=env, shell=True, capture_output=True, text=True)
                        print('')
                    else:
                        res_obj = subprocess.run(unwrap_command, env=env, shell=True, capture_output=True, text=True)
                        if res_obj.returncode != 0:
                            raise RuntimeError(f"Couldn't unwrap: {res_obj.stderr}\n{res_obj.stdout}")
                        
                        if unzip_command:
                            res_unzip = subprocess.run(unzip_command, shell=True, capture_output=True, text=True)
                            if res_unzip.returncode != 0:
                                print(f"Warning: Couldn't unzip: {res_unzip.stderr}")

                        # Centre again
                        centre_and_save_nii(load_nii(phase_file_unwrapped), phase_file_unwrapped, nii_pixdim)

                elif unwrap_method == 'phun':
                    unwrap_command = f'phun -2 -n 1 --tq_min 0.02 --polar -o {unix_format(phase_file_unwrapped)} {unix_format(mag_file)} {unix_format(phase_file)}'
                    res_obj = subprocess.run(unwrap_command, shell=True, capture_output=True, text=True)
                    if res_obj.returncode != 0:
                        raise RuntimeError(f"Couldn't unwrap: {res_obj.stderr}\n{res_obj.stdout}")

                elif unwrap_method == 'snaphu':
                    unwrap_command = f'sh /data/simon/scripts/snaphu_script.sh {unix_format(mag_file)} {unix_format(phase_file)}'
                    res_obj = subprocess.run(unwrap_command, shell=True, capture_output=True, text=True)
                    if res_obj.returncode != 0:
                        raise RuntimeError(f"Couldn't unwrap: {res_obj.stderr}\n{res_obj.stdout}")
                else:
                    raise ValueError('No valid unwrap option (unwrap_method) specified')
    else:
        print(' - unwrapped data found')

    data['fnCurrentPhaseImages'] = fnCurrentPhaseImagesUnwrapped
    return data
