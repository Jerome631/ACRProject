import os
import pydicom
import numpy as np
import matplotlib.pyplot as plt
from matlab_compat import uiputfile, uigetfile, questdlg, msgbox, xlswrite, fspecial, imfilter

def compute(s7_path):
    """Computation for the Image Intensity Uniformity test

    Args:
        s7_path: path to slice 7 DICOM file

    Returns:
        results (dict): {'PIU': float} : Percent Integral Uniformity (%)
        fig:            matplotlib Figure showing the 200 cm² ROI
    """
    ds = pydicom.dcmread(s7_path)
    I  = ds.pixel_array.astype(float)
    width = float(ds.Rows)
    f     = width / 250.0

    h     = fspecial('disk', 6.0 * f)
    Ifilt = imfilter(I, h)

    x, y = np.nonzero(I > 500)
    if len(x) == 0:
        return None, None
    maxx, minx = x.max(), x.min()
    maxy, miny = y.max(), y.min()
    midptx = minx + (maxx - minx) / 2.0
    midpty = miny + (maxy - miny) / 2.0

    h_idx, w_idx = np.indices(I.shape)
    dist     = np.hypot(h_idx - midptx, w_idx - midpty)
    roi_mask = dist < (73.0 * f)
    intensity = Ifilt[roi_mask]

    if intensity.size == 0:
        return None, None

    high = intensity.max()
    low  = intensity.min()
    if (high + low) == 0:
        return None, None

    PIU = 100.0 * (1.0 - ((high - low) / (high + low)))

    I_roi_viz = I.copy()
    I_roi_viz[dist < (79.0 * f)] = 0.0

    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    axes[0].imshow(I, cmap='gray');         axes[0].set_title('Original Image — Slice 7');              axes[0].axis('off')
    axes[1].imshow(I_roi_viz, cmap='gray'); axes[1].set_title('200 cm² ROI (black disc = selected area)'); axes[1].axis('off')
    plt.tight_layout()

    return {'PIU': PIU}, fig


def main():
    plt.ion()
    
    fname, pathname = uiputfile('*.xlsx;*.xls', 'Save As')
    if not fname:
        print("No file selected. Exiting.")
        return
    results_file = os.path.join(pathname, fname)
    
    button_name = questdlg('What series?', 'Uniformity', 'ACR T1 series', 'ACR T2 series', 'ACR T1 series')
    if button_name == 'ACR T1 series':
        cell = 'B62'
    elif button_name == 'ACR T2 series':
        cell = 'B54'
    else:
        cell = 'B62'
        
    s7_fname, s7_pathname = uigetfile('*.dcm', 'Select Slice 7')
    if not s7_fname:
        return
    s7_path = os.path.join(s7_pathname, s7_fname)
    
    ds = pydicom.dcmread(s7_path)
    I = ds.pixel_array.astype(float)
    width = float(ds.Rows)
    f = width / 250.0
    
    fig1 = plt.figure(num='Original Image - Slice 7')
    plt.imshow(I, cmap='gray')
    plt.title('Original Image - Slice 7 of ACR Phantom')
    plt.draw()
    plt.pause(1)
    
    # Filter image with 1cm^2 disk filter (6mm radius = 6*f pixels)
    h = fspecial('disk', 6.0 * f)
    Ifilt = imfilter(I, h)
    
    fig2 = plt.figure(num='Filtered Image')
    plt.imshow(Ifilt, cmap='gray')
    plt.title('Filtered Image - 1cm^2 Circular Averaging Filter')
    plt.draw()
    plt.pause(1)
    
    # Midpoint and distance calculation
    x, y = np.nonzero(I > 500)
    maxx, minx = x.max(), x.min()
    maxy, miny = y.max(), y.min()
    midptx = minx + (maxx - minx) / 2.0
    midpty = miny + (maxy - miny) / 2.0
    
    # 200 cm^2 ROI (73 mm radius)
    h_idx, w_idx = np.indices(I.shape)
    dist = np.hypot(h_idx - midptx, w_idx - midpty)
    roi_mask = dist < (73.0 * f)
    
    intensity = Ifilt[roi_mask]
    high = intensity.max()
    low = intensity.min()
    
    # Black disc visualization (79 mm radius disc to highlight ROI, setting values to 0)
    I_roi_viz = I.copy()
    viz_mask = dist < (79.0 * f)
    I_roi_viz[viz_mask] = 0.0
    
    fig3 = plt.figure(num='ROI')
    plt.imshow(I_roi_viz, cmap='gray')
    plt.title('Black disc shows selected 200cm^2 region of interest')
    plt.draw()
    plt.pause(1)
    
    PIU = 100.0 * (1.0 - ((high - low) / (high + low)))
    success = xlswrite(results_file, PIU, button_name, cell)
    
    res_str = f"The uniformity is....{PIU:.2f}%. Note: The uniformity should be >= 87.5%."
    if success == 1:
        res_str += " The result has been successfully written to Excel."
    else:
        res_str += " Error: The result has not been written to Excel."
    msgbox(res_str, 'RESULT')
    
    plt.close('all')
    
    # Relaunch the QA GUI
    if __name__ == '__main__':
        try:
            import MRI_QA
            MRI_QA.main()
        except ImportError:
            pass

if __name__ == '__main__':
    main()
