import os
import pydicom
import matplotlib.pyplot as plt
from matlab_compat import uiputfile, uigetfile, questdlg, msgbox, inputdlg, xlswrite

def get_slice_image(dcm_path):
    """Return a matplotlib Figure of the low-contrast DICOM slice for spoke counting.

    Args:
        dcm_path: path to a DICOM file (slice 8, 9, 10, or 11)

    Returns:
        fig: matplotlib Figure showing full slice + zoomed centre crop
    """
    import numpy as np

    ds = pydicom.dcmread(dcm_path)
    I  = ds.pixel_array.astype(float)
    sl = getattr(ds, 'InstanceNumber', '?')

    # Window the image to enhance low-contrast visibility:
    # Use mean ± 1.5 * std as the display range
    vmin = max(0, I.mean() - 1.5 * I.std())
    vmax = I.mean() + 1.5 * I.std()

    # Compute a centre crop (~40 % of image) to zoom in on the insert
    h, w  = I.shape
    cy, cx = h // 2, w // 2
    r      = int(min(h, w) * 0.30)
    crop   = I[cy - r : cy + r, cx - r : cx + r]

    fig, axes = plt.subplots(1, 2, figsize=(10, 5))

    axes[0].imshow(I,    cmap='gray', vmin=vmin, vmax=vmax)
    axes[0].set_title(f'Slice {sl} — Full Image')
    axes[0].axis('off')

    axes[1].imshow(crop, cmap='gray', vmin=vmin, vmax=vmax)
    axes[1].set_title(f'Slice {sl} — Centre Crop (count spokes here)')
    axes[1].axis('off')

    plt.tight_layout()
    return fig



def main():
    plt.ion()
    
    fname, pathname = uiputfile('*.xlsx;*.xls', 'Please select file to write results to')
    if not fname:
        print("No file selected. Exiting.")
        return
    results_file = os.path.join(pathname, fname)
    
    btn = questdlg('What series?', 'Signal-Noise Ratio', 'ACR series', 'Site series', 'ACR series')
    if btn == 'ACR series':
        button_name = questdlg('What series?', 'Signal-Noise Ratio', 'ACR T1 series', 'ACR T2 series', 'ACR T1 series')
    else:
        button_name = questdlg('What series?', 'Signal-Noise Ratio', 'Site T1 series', 'Site T2 series', 'Site T1 series')
        
    if button_name == 'ACR T1 series':
        cells = ['B104', 'B105', 'B106', 'B107', 'B109']
    elif button_name == 'ACR T2 series':
        cells = ['B91', 'B92', 'B93', 'B94', 'B96']
    elif button_name == 'Site T1 series' or button_name == 'Site T2 series':
        cells = ['B37', 'B38', 'B39', 'B40', 'B42']
    else:
        cells = ['B104', 'B105', 'B106', 'B107', 'B109']
        
    slices = [11, 10, 9, 8]
    answers = []
    
    for i, sl in enumerate(slices):
        sl_fname, sl_pathname = uigetfile('*.dcm', f'Select Slice {sl}')
        if not sl_fname:
            return
        sl_path = os.path.join(sl_pathname, sl_fname)
        
        ds = pydicom.dcmread(sl_path)
        I = ds.pixel_array.astype(float)
        
        fig = plt.figure(num=f"Slice {sl}")
        plt.imshow(I, cmap='gray')
        plt.title(f"Slice {sl}")
        plt.draw()
        plt.pause(1)
        
        msgbox('Adjust the contrast as required (use matplotlib toolbar). Strike OK to enter results.', 'MESSAGE')
        
        ans = inputdlg(['How many complete spokes are resolved?'], 'Low-Contrast Detectability Results')
        try:
            val = float(ans[0])
        except (ValueError, TypeError, IndexError):
            val = 0.0
            
        answers.append(val)
        plt.close(fig)
        
        xlswrite(results_file, val, button_name, cells[i])
        
    total = sum(answers)
    success = xlswrite(results_file, total, button_name, cells[4])
    
    res_str = f"Total spokes resolved: {total}. "
    if success == 1:
        res_str += "The results have been successfully written to Excel."
    else:
        res_str += "Error: Results have NOT been written to Excel."
    msgbox(res_str, 'RESULTS')
    
    # Relaunch the QA GUI
    if __name__ == '__main__':
        try:
            import MRI_QA
            MRI_QA.main()
        except ImportError:
            pass

if __name__ == '__main__':
    main()
