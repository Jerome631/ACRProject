import os
import sys
import shutil
import time
import numpy as np

from fm_get_nes import fm_get_nes
from fm_get_TEs import fm_get_TEs
from fm_define_filenames import fm_define_filenames
from fm_get_voxel_dimensions import fm_get_voxel_dimensions
from fm_get_phase_range import fm_get_phase_range
from fm_split_rescale import fm_split_rescale
from fm_recon_mags import fm_recon_mags
from fm_phase_match import fm_phase_match
from fm_conj_diff_new import fm_conj_diff_new
from fm_unwrap import fm_unwrap
from fm_make_mask import fm_make_mask
from fm_jump_correct_phase import fm_jump_correct_phase
from fm_make_fieldmaps import fm_make_fieldmaps
from fm_jump_correct_fieldmaps import fm_jump_correct_fieldmaps
from fm_median_mean_std import fm_median_mean_std
from fm_mask_fm import fm_mask_fm
from fm_despeckle import fm_despeckle
from fm_smooth import fm_smooth
from fm_get_epi_pars import fm_get_epi_pars
from fm_threshold import fm_threshold
from secs2hms import secs2hms
from unix_format import unix_format

def fm_calc_main(data_from_caller):
    # Set default parameters
    data = {
        'multi_channel_data': 'yes',
        'processing_option': 'all_at_once',
        'gradient_thresh': 0.8,
        'cleanup': 'no',
        'extension': '.nii',
        'prelude_thresholds': [8, 20],
        'smoothing_kernel': [7, 7, 7],
        'BET_f_sep_mask': 0.3,
        'BET_f_small_mask': 0.5,
        'BET_f_large_mask': 0.4,
        'unwrap_method': 'prelude',
        'method': 'sep-channel',
        'phase_cor_method': 'hammond',
        'do_all_remaing_processing_stages': 'no',
        'epi_dir': -1,
        'rbw': -1,
        'PE_dir': -1
    }

    # Override defaults with caller settings
    data.update(data_from_caller)

    start_time = time.time()

    is_pc = (sys.platform == 'win32')
    fsl_prefix = data.get('fsl_prefix', 'avw' if is_pc else 'fsl')
    fsl_suffix = data.get('fsl_suffix', '.exe' if is_pc else '')
    data['fsl_prefix'] = fsl_prefix
    data['fsl_suffix'] = fsl_suffix

    # Classify by file_code
    file_code = ''
    if data['multi_channel_data'] == 'yes':
        file_code += 'SC'
    if data.get('sep_files_for_echoes', 'no') == 'yes':
        file_code += 'SE'
    if data.get('sep_files_for_pm', 'no') == 'yes':
        file_code += 'SPM'
    data['file_code'] = file_code

    # Check for reform subdir
    dir1 = data['readfile_dirs'][0] if isinstance(data['readfile_dirs'], (list, tuple)) else data['readfile_dirs']
    reformdirtemp = os.path.join(data['root_dir'], str(dir1), 'reform')
    if os.path.isdir(reformdirtemp):
        reform_subdir = 'reform'
    else:
        reform_subdir = ''
    data['reform_subdir'] = reform_subdir

    # Make results directory
    os.makedirs(data['writefile_dir'], exist_ok=True)

    # Prepare gunzip command
    unzip_command = f'for i in `find {unix_format(os.path.join(data["writefile_dir"], ""))} -name "*.gz"` ; do gunzip -d -f -q $i ; done'
    data['unzip_command'] = unzip_command

    # Separate channels directory
    sep_dir = os.path.join(data['writefile_dir'], f'sep_{data["unwrap_method"]}')
    os.makedirs(sep_dir, exist_ok=True)
    data['sep_dir'] = sep_dir

    # Output directory name based on method and unwrap_method
    if data['multi_channel_data'] == 'yes':
        if data['method'] == 'phase-match':
            fm_dir = f'fm_phase-match_{data["phase_cor_method"]}'
        elif data['method'] == 'sep-channel':
            fm_dir = 'fm_sep-channel'
        elif data['method'] == 'conj-diff':
            fm_dir = 'fm_conj-diff'
        else:
            raise ValueError(f"No valid method specified: {data['method']}")
    else:
        fm_dir = 'fm'

    fm_dir += f'_{data["unwrap_method"]}'
    writefile_dir_store = data['writefile_dir']
    data['writefile_dir'] = os.path.join(data['writefile_dir'], fm_dir)
    os.makedirs(data['writefile_dir'], exist_ok=True)

    if data['multi_channel_data'] == 'yes':
        channel_key = 'channel_'
    else:
        data['n_channels'] = 1
        channel_key = ''
    data['channel_key'] = channel_key

    # Retrieve echo count
    data = fm_get_nes(data)

    if data['n_echoes'] > 2:
        data['n_echoes_to_use'] = 2
        data['echoes_to_use'] = [1, 3]
    elif data['n_echoes'] == 2:
        data['n_echoes_to_use'] = 2
        data['echoes_to_use'] = [1, 2]
    else:
        print(f"Warning: At least 2 phase images are needed; only {data['n_echoes']} found.")
        print("Will process the first echo then exit later.")
        data['n_echoes_to_use'] = 1
        data['echoes_to_use'] = [1]

    # Verify if text headers are present
    if data['file_code'] in ['SE', 'SESPM', 'SCSESPM']:
        data['text_header'] = 'yes'
        for j in range(data['n_echoes_to_use']):
            header_file = os.path.join(data['root_dir'], data['readfile_dirs'][j], 'text_header.txt')
            if not os.path.exists(header_file):
                data['text_header'] = 'no'
                break
    else:
        dir_name = data['readfile_dirs'][0] if isinstance(data['readfile_dirs'], (list, tuple)) else data['readfile_dirs']
        header_file = os.path.join(data['root_dir'], dir_name, 'text_header.txt')
        data['text_header'] = 'yes' if os.path.exists(header_file) else 'no'

    # Get TEs
    if data['text_header'] == 'yes':
        data = fm_get_TEs(data)
    else:
        if 'TEs' not in data:
            raise ValueError('TEs need to be defined in caller.')
    
    # Sort TEs
    data['TE_sorted_indices'] = np.argsort(data['TEs'])
    data['TEs'] = np.sort(data['TEs'])

    # File names setup
    data = fm_define_filenames(data)
    fnReconMag = data['fnReconMag']
    fnAllMags = data['fnAllMags']

    # Get voxel dimensions and phase range
    data = fm_get_voxel_dimensions(data)
    data = fm_get_phase_range(data)

    # Split magnitude and phase images
    data = fm_split_rescale(data)

    # Reconstruct magnitude images
    if data['multi_channel_data'] == 'yes':
        data = fm_recon_mags(data)
    else:
        shutil.copyfile(data['fnCurrentMagImages'][0][0], data['fnReconMag'])

    # Multi-channel phase combinations
    if data['multi_channel_data'] == 'yes':
        if data['method'] == 'phase-match':
            data = fm_phase_match(data)
        elif data['method'] == 'conj-diff':
            data = fm_conj_diff_new(data)
            data['n_echoes_to_use'] = 1
    else:
        print("Single-channel data, ignoring specified phase combination method")

    if data['method'] in ['phase-match', 'conj-diff'] or data['multi_channel_data'] == 'no':
        data['n_channels'] = 1
        data['despeckle_method'] = 'EXTREMES'
    else:
        data['despeckle_method'] = 'STD'

    # Phase unwrapping
    data = fm_unwrap(data)

    # Brain/phantom mask creation
    data = fm_make_mask(data)

    # Slice jump correction
    data = fm_jump_correct_phase(data)

    if data['n_echoes'] < 2:
        print("Warning: There were not enough echoes to make fieldmaps, quitting here")
        return

    # Calculate fieldmaps and echo jump correction
    data = fm_make_fieldmaps(data)
    data = fm_jump_correct_fieldmaps(data)

    # Sep-channel intermediate stats
    if data['multi_channel_data'] == 'yes' and data['method'] == 'sep-channel':
        data = fm_median_mean_std(data)

    print(f"Calculation of fieldmaps took {secs2hms(time.time() - start_time)}")

    # Final mask, despeckling, and smoothing
    data = fm_mask_fm(data)
    data = fm_despeckle(data)
    data = fm_smooth(data)

    # EPI parameters & Voxel shift thresholding
    data = fm_get_epi_pars(data)
    if data.get('do_gradient_thresholding', 'no') == 'yes':
        data = fm_threshold(data)

    print(f"Calculation of denoised fieldmaps took {secs2hms(time.time() - start_time)}")

    fieldmap_to_use = data['fnCurrentFieldmaps'][0][0]

    # Cleanup of temporary files
    if data['cleanup'] == 'yes':
        final_fm_fn = os.path.join(writefile_dir_store, f"fieldmap{data['extension']}")
        shutil.copyfile(fieldmap_to_use, final_fm_fn)
        shutil.rmtree(data['writefile_dir'])
        shutil.rmtree(sep_dir)
    else:
        final_fm_fn = os.path.join(data['writefile_dir'], f"fieldmap{data['extension']}")
        shutil.copyfile(fieldmap_to_use, final_fm_fn)

    print(f"Took {secs2hms(time.time() - start_time)} to calculate")
    print(f"Written final fieldmap to {final_fm_fn}")

    # Generate suggested FUGUE command for user reference
    if data['epi_dir'] == -1:
        epi = 'epi'
        epi_output = 'epi_output'
    else:
        epi = os.path.join(data['root_dir'], str(data['epi_dir']), 'Image.nii')
        epi_output = os.path.join(data['root_dir'], str(data['epi_dir']), 'Image_dc.nii')

    if data['rbw'] == -1:
        dwell_time = '1/rbw'
    else:
        dwell_time = f"{1.0/data['rbw']:.6f}"

    if data['PE_dir'] == -1:
        PE_dir_str = '[phase-encode-direction]'
    else:
        PE_dir_str = data['PE_dir']

    unwarp_command = f"fugue -i {epi} --dwell={dwell_time} --loadfmap={final_fm_fn} -u {epi_output} --unwarpdir={PE_dir_str} -v"
    print("Unwarp command is something like :")
    print(unwarp_command)
    print("")
