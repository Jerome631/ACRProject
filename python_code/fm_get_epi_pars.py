import os
import sys
from search_all_header_func import search_all_header_func

def fm_get_epi_pars(data):
    root_dir = data['root_dir']
    
    epi_dir = data.get('epi_dir', -1)
    rbw = data.get('rbw', -1)

    # get the receiver bandwidth/pix
    if epi_dir != -1 and epi_dir is not None:
        epi_header_file = os.path.join(root_dir, str(epi_dir), 'text_header.txt')
        if os.path.exists(epi_header_file):
            val_str = search_all_header_func(epi_header_file, 'PixelBandwidth')
            try:
                rbw = float(val_str)
            except (ValueError, TypeError):
                rbw = -1.0
        else:
            rbw = -1.0
    elif data.get('rbw', -1) != -1:
        rbw = data['rbw']

    data['rbw'] = rbw

    # determine the phase-encode direction and readout dimension
    if epi_dir != -1 and epi_dir is not None:
        epi_header_file = os.path.join(root_dir, str(epi_dir), 'text_header.txt')
        if os.path.exists(epi_header_file):
            PE_dir = search_all_header_func(epi_header_file, 'InPlanePhaseEncodingDirection')
            if PE_dir == 'COL':
                data['readout_dimension'] = 2
                rot_val = search_all_header_func(epi_header_file, 'dInPlaneRot')
                if rot_val == '-1':
                    PE_dir = 'y-'
                else:
                    PE_dir = 'y'
            elif PE_dir == 'ROW':
                readout_dimension = 3
                rot_val = search_all_header_func(epi_header_file, 'dInPlaneRot')
                if rot_val == '-1':
                    PE_dir = 'x-'
                else:
                    PE_dir = 'x'
            else:
                PE_dir = -1
            data['PE_dir'] = PE_dir

    PE_dir = data.get('PE_dir', -1)
    if PE_dir == '-y':
        PE_dir = 'y-'
        readout_dimension = 2
    elif PE_dir in ['y', 'y-']:
        readout_dimension = 2
    elif PE_dir == '-x':
        PE_dir = 'x-'
        readout_dimension = 3
    elif PE_dir in ['x', 'x-']:
        readout_dimension = 3
    else:
        readout_dimension = -1

    data['readout_dimension'] = readout_dimension
    data['PE_dir'] = PE_dir

    return data
