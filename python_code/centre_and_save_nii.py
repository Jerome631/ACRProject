from centre_header import centre_header
from set_nii_voxel_size import set_nii_voxel_size
from save_nii import save_nii

def centre_and_save_nii(image_nii, filename, pixdim):
    image_nii.hdr = centre_header(image_nii.hdr)
    image_nii.hdr = set_nii_voxel_size(image_nii.hdr, pixdim)
    save_nii(image_nii, filename)
