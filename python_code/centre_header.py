import math

def centre_header(nii_hdr):
    nii_hdr.hist.originator[0] = math.ceil(nii_hdr.dime.dim[1] / 2)
    nii_hdr.hist.originator[1] = math.ceil(nii_hdr.dime.dim[2] / 2)
    nii_hdr.hist.originator[2] = math.ceil(nii_hdr.dime.dim[3] / 2)
    nii_hdr.hist.originator[3] = 0
    nii_hdr.hist.originator[4] = 0
    return nii_hdr
