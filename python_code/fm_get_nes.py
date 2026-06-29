import os
from load_nii_hdr import load_nii_hdr

def fm_get_nes(data):
    file_code = data['file_code']
    root_dir = data['root_dir']
    readfile_dirs = data['readfile_dirs']
    reform_subdir = data['reform_subdir']

    if file_code in ['SE', 'SCSE']:
        n_echoes = len(readfile_dirs)
    elif file_code in ['SESPM', 'SCSESPM']:
        n_echoes = len(readfile_dirs) // 2
    else:
        if isinstance(readfile_dirs, (list, tuple)):
            dir_name = readfile_dirs[0]
        else:
            dir_name = readfile_dirs

        image_path = os.path.join(root_dir, dir_name, reform_subdir, 'Image.nii')
        hdr, _, _, _ = load_nii_hdr(image_path)

        # hdr.dime.dim[0] represents the number of dimensions (dim(1) in MATLAB)
        # hdr.dime.dim[4] represents the size of the 4th dimension (dim(5) in MATLAB)
        if hdr.dime.dim[0] == 4:
            n_echoes = 1
        else:
            n_echoes = int(hdr.dime.dim[4])

    data['n_echoes'] = int(n_echoes)
    return data
