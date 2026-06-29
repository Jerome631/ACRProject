import os
import pydicom
import numpy as np
import matplotlib.pyplot as plt
from matlab_compat import uiputfile, uigetfile, questdlg, msgbox, xlswrite, imcrop, imresize

def get_insert_image(dcm_path):
    """Return a zoomed matplotlib Figure of the slice-position bar insert.

    This replaces the ginput() interaction for the web UI: the figure is
    displayed in the browser and the user enters the bar difference manually.

    Args:
        dcm_path: path to a DICOM file (slice 1 or slice 11)

    Returns:
        fig: matplotlib Figure (3× magnified crop of the bar insert)
    """
    ds    = pydicom.dcmread(dcm_path)
    I     = ds.pixel_array.astype(float)
    width = float(ds.Rows)
    f     = width / 250.0

    rect = [round(100*f), round(20*f), round(40*f), round(60*f)]
    I2   = imcrop(I, rect)
    I3   = imresize(I2, 3)

    fig, ax = plt.subplots(figsize=(5, 6))
    ax.imshow(I3, cmap='gray')
    ax.set_title('Bar Insert — 3× Zoom\n(measure bottom of each bar)')
    ax.axis('off')
    plt.tight_layout()
    return fig


def main():
    plt.ion()
    
    fname, pathname = uiputfile('*.xlsx;*.xls', 'Save As')
    if not fname:
        print("No file selected. Exiting.")
        return
    results_file = os.path.join(pathname, fname)
    
    button_name = questdlg('What series?', 'Slice Position Accuracy', 'ACR T1 series', 'ACR T2 series', 'ACR T1 series')
    
    if button_name == 'ACR T1 series':
        cell1 = 'B56'
        cell2 = 'B57'
    elif button_name == 'ACR T2 series':
        cell1 = 'B48'
        cell2 = 'B49'
    else:
        # default fallback
        cell1 = 'B56'
        cell2 = 'B57'

    # --- SLICE 1 ---
    s1_fname, s1_pathname = uigetfile('*.dcm', 'Select Slice 1')
    if not s1_fname:
        return
    s1_path = os.path.join(s1_pathname, s1_fname)
    
    ds = pydicom.dcmread(s1_path)
    I = ds.pixel_array.astype(float)
    width = float(ds.Rows)
    f = width / 250.0
    
    # Crop rect
    rect = [round(100*f), round(20*f), round(40*f), round(60*f)]
    I2 = imcrop(I, rect)
    I3 = imresize(I2, 3)
    
    fig, ax = plt.subplots(num=1, figsize=(6,6))
    ax.imshow(I3, cmap='gray')
    ax.set_title('Slice 1 - Cropped and Zoomed')
    plt.draw()
    plt.pause(1)
    
    msg = ('Adjust the contrast as required. Click on Figure 1 (to make sure it is the active image) '
           'and strike any key when finished. Then, use the mouse to click on the bottom of each bar.')
    msgbox(msg, 'MESSAGE')
    
    # Wait for key press or click
    # In Python, we can just call ginput directly, which waits for two clicks!
    # To mimic MATLAB's pause, we can just do ginput(2) which will block until 2 clicks are received.
    points1 = plt.ginput(2, timeout=0)
    
    # points1 is list of (x, y) coordinates
    if len(points1) >= 2:
        R1 = [points1[0][1], points1[1][1]]
        # difference1 = abs((R1(1)-R1(2))*(250/(256*f)))
        difference1 = abs((R1[0] - R1[1]) * (250.0 / (256.0 * f)))
    else:
        difference1 = 0.0
        
    plt.close(fig)
    
    # --- SLICE 11 ---
    s11_fname, s11_pathname = uigetfile('*.dcm', 'Select Slice 11')
    if not s11_fname:
        return
    s11_path = os.path.join(s11_pathname, s11_fname)
    
    ds11 = pydicom.dcmread(s11_path)
    I11 = ds11.pixel_array.astype(float)
    I12 = imcrop(I11, rect)
    I13 = imresize(I12, 3)
    
    fig, ax = plt.subplots(num=1, figsize=(6,6))
    ax.imshow(I13, cmap='gray')
    ax.set_title('Slice 11 - Cropped and Zoomed')
    plt.draw()
    plt.pause(1)
    
    msgbox('Adjust the contrast as required. Click on Figure 1 and strike any key when finished. Then select the two bar endpoints.', 'MESSAGE')
    
    points2 = plt.ginput(2, timeout=0)
    if len(points2) >= 2:
        R2 = [points2[0][1], points2[1][1]]
        difference2 = abs((R2[0] - R2[1]) * (250.0 / (256.0 * f)))
    else:
        difference2 = 0.0
        
    plt.close(fig)
    
    success1 = xlswrite(results_file, difference1, button_name, cell1)
    success2 = xlswrite(results_file, difference2, button_name, cell2)
    
    res_str = f"Slice 1: The absolute bar length difference is...{difference1:.2f} mm. "
    res_str += f"Slice 11: The absolute bar length difference is...{difference2:.2f} mm. "
    res_str += "Note: The absolute bar length difference should be < 5 mm. "
    if success1 == 1 and success2 == 1:
        res_str += " The results have been successfully written to Excel."
    else:
        res_str += " Error: The results have not been written to Excel."
    msgbox(res_str, 'RESULT')
    
    # Relaunch the QA GUI
    if __name__ == '__main__':
        try:
            import MRI_QA
            MRI_QA.main()
        except ImportError:
            pass

if __name__ == '__main__':
    main()
