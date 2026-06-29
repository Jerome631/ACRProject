import math
from load_nii import load_nii
from save_nii import save_nii

def centre_header_file(filename):
    nii = load_nii(filename)
    nii.hdr.hist.originator[0] = math.ceil(nii.hdr.dime.dim[1] / 2)
    nii.hdr.hist.originator[1] = math.ceil(nii.hdr.dime.dim[2] / 2)
    nii.hdr.hist.originator[2] = math.ceil(nii.hdr.dime.dim[3] / 2)
    nii.hdr.hist.originator[3] = 0
    nii.hdr.hist.originator[4] = 0
    save_nii(nii, filename)
