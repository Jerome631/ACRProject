import os
import pydicom
import matplotlib.pyplot as plt
from matlab_compat import uiputfile, uigetfile, questdlg, msgbox, inputdlg, xlswrite, imcrop, imresize

def get_insert_image(s1_path):
    """Return a zoomed matplotlib Figure of the spatial resolution insert.

    Upper-left array → horizontal resolution.
    Lower-right array → vertical resolution.

    Args:
        s1_path: path to slice 1 DICOM file

    Returns:
        fig: matplotlib Figure (3× magnified crop of the spatial resolution insert)
    """
    ds    = pydicom.dcmread(s1_path)
    I     = ds.pixel_array.astype(float)
    width = float(ds.Rows)
    f     = width / 256.0

    rect = [60.0 * f, 150.0 * f, 130.0 * f, 50.0 * f]
    I2   = imcrop(I, rect)
    I3   = imresize(I2, 3)

    vmin = max(0, I3.mean() - 1.5 * I3.std())
    vmax = I3.mean() + 1.5 * I3.std()

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.imshow(I3, cmap='gray', vmin=vmin, vmax=vmax)
    ax.set_title('Spatial Resolution Insert — 3× Zoom\n'
                 'Upper-left array = Horizontal resolution  |  Lower-right array = Vertical resolution')
    ax.axis('off')
    plt.tight_layout()
    return fig


def main():
    plt.ion()
    
    fname, pathname = uiputfile('*.xlsx;*.xls', 'Please select file to write results to')
    if not fname:
        print("No file selected. Exiting.")
        return
    results_file = os.path.join(pathname, fname)
    
    button_name = questdlg('What series?', 'Spatial Resolution', 'ACR T1 series', 'ACR T2 series', 'ACR T1 series')
    if button_name == 'ACR T1 series':
        cell1 = 'B19'
        cell2 = 'B20'
    elif button_name == 'ACR T2 series':
        cell1 = 'B11'
        cell2 = 'B12'
    else:
        cell1 = 'B19'
        cell2 = 'B20'
        
    s1_fname, s1_pathname = uigetfile('*.dcm', 'Select Slice 1')
    if not s1_fname:
        return
    s1_path = os.path.join(s1_pathname, s1_fname)
    
    ds = pydicom.dcmread(s1_path)
    I = ds.pixel_array.astype(float)
    
    width = float(ds.Rows)
    f = width / 256.0
    
    rect = [60.0 * f, 150.0 * f, 130.0 * f, 50.0 * f]
    I2 = imcrop(I, rect)
    I3 = imresize(I2, 3)
    
    fig = plt.figure(num='Spatial Resolution Insert')
    plt.imshow(I3, cmap='gray')
    plt.title('Cropped and Magnified Spatial Resolution Insert')
    plt.draw()
    plt.pause(1)
    
    msg = ('Adjust the contrast as required. Use the upper left array to determine the horizontal '
           'resolution and the lower right array to determine the vertical resolution. Strike OK to enter results.')
    msgbox(msg, 'MESSAGE')
    
    ans = inputdlg(['Enter the horizontal resolution:', 'Enter the vertical resolution:'], 'Spatial Resolution Results')
    if not ans or len(ans) < 2:
        plt.close(fig)
        return
        
    try:
        horiz = float(ans[0])
        vert = float(ans[1])
    except (ValueError, TypeError):
        horiz, vert = 0.0, 0.0
        
    plt.close(fig)
    
    success1 = xlswrite(results_file, horiz, button_name, cell1)
    success2 = xlswrite(results_file, vert, button_name, cell2)
    
    res_str = f"Horizontal resolution: {horiz} mm. Vertical resolution: {vert} mm. "
    if success1 == 1 and success2 == 1:
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
