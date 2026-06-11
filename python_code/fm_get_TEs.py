import os
import numpy as np
from search_text_header_func import search_text_header_func

def fm_get_TEs(data):
    echoes_to_use = data['echoes_to_use']
    n_echoes_to_use = data['n_echoes_to_use']
    root_dir = data['root_dir']
    readfile_dirs = data['readfile_dirs']
    file_code = data['file_code']

    TEs = np.zeros(n_echoes_to_use)

    if file_code in ['SE', 'SCSE']:
        for j in range(n_echoes_to_use):
            i = echoes_to_use[j]
            # Convert 1-based index i to 0-based for list lookup
            header_file = os.path.join(root_dir, readfile_dirs[i - 1], 'text_header.txt')
            if os.path.exists(header_file):
                TEs[j] = float(search_text_header_func(header_file, 'alTE[0]'))
            else:
                raise FileNotFoundError(f"Could not find {header_file}")
    elif file_code in ['SESPM', 'SCSESPM']:
        for j in range(n_echoes_to_use):
            i = echoes_to_use[j]
            # Convert 1-based index 2*i-1 to 0-based: 2*i-2
            header_file = os.path.join(root_dir, readfile_dirs[2 * i - 2], 'text_header.txt')
            if os.path.exists(header_file):
                TEs[j] = float(search_text_header_func(header_file, 'alTE[0]'))
            else:
                raise FileNotFoundError(f"Could not find {header_file}")
    else:
        if isinstance(readfile_dirs, (list, tuple)):
            header_file = os.path.join(root_dir, readfile_dirs[0], 'text_header.txt')
        else:
            header_file = os.path.join(root_dir, readfile_dirs, 'text_header.txt')

        if os.path.exists(header_file):
            for j in range(n_echoes_to_use):
                i = echoes_to_use[j]
                val_str = search_text_header_func(header_file, f'alTE[{i - 1}]')
                TEs[j] = float(val_str)
        else:
            raise FileNotFoundError(f"Could not find {header_file}")

    data['TEs'] = TEs
    return data
