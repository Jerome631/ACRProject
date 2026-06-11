import os
from load_nii_hdr import load_nii_hdr

def fm_get_voxel_dimensions(data):
    root_dir = data['root_dir']
    readfile_dirs = data['readfile_dirs']
    reform_subdir = data['reform_subdir']

    if isinstance(readfile_dirs, (list, tuple)):
        dir_name = readfile_dirs[0]
    else:
        dir_name = readfile_dirs

    image_path = os.path.join(root_dir, dir_name, reform_subdir, 'Image.nii')
    hdr, _, _, _ = load_nii_hdr(image_path)

    data['nii_dim'] = hdr.dime.dim
    data['nii_pixdim'] = hdr.dime.pixdim
    return data
