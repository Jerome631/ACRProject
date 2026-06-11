from load_nii_hdr import load_nii_hdr, struct
from load_nii_img import load_nii_img
from xform_nii import xform_nii

def load_nii(filename, img_idx=None, dim5_idx=None, dim6_idx=None, dim7_idx=None, old_RGB=0, tolerance=0.1, preferredForm='s'):
    hdr, filetype, fileprefix, machine = load_nii_hdr(filename)
    img, hdr = load_nii_img(hdr, filetype, fileprefix, machine, img_idx, dim5_idx, dim6_idx, dim7_idx, old_RGB)
    
    nii = struct(
        hdr=hdr,
        filetype=filetype,
        fileprefix=fileprefix,
        machine=machine,
        img=img
    )
    nii = xform_nii(nii, tolerance, preferredForm)
    return nii
