import os
import pydicom
import numpy as np
import matplotlib.pyplot as plt
from matlab_compat import uiputfile, uigetfile, questdlg, msgbox, xlswrite, fspecial, imfilter

def compute(s7_path):
    """Computation for the SNR test

    Args:
        s7_path: path to slice 7 DICOM file

    Returns:
        results (dict): {'snr': float}
        fig:            matplotlib Figure showing signal and noise ROIs
    """
    ds = pydicom.dcmread(s7_path)
    I  = ds.pixel_array.astype(float)

    x, y = np.nonzero(I > 500)
    if len(x) == 0:
        return None, None
    maxx, minx = x.max(), x.min()
    maxy, miny = y.max(), y.min()
    midptx = int(np.round(minx + (maxx - minx) / 2.0))
    midpty = int(np.round(miny + (maxy - miny) / 2.0))

    width = float(ds.Rows)
    f     = width / 256.0

    h      = fspecial('disk', int(np.round(79.0 * f)))
    Ifilt  = imfilter(I, h)
    intensity = Ifilt[midptx, midpty]

    bg_u, bg_v = np.nonzero(I < 500)

    def get_noise_pixels(center_x, center_y):
        dist = np.hypot(bg_v - center_y, bg_u - center_x)
        mask = dist < int(np.round(20.0 * f))
        return I[bg_u[mask], bg_v[mask]]

    noisex  = int(width - np.round(30.0 * f));  noisey  = int(width - np.round(30.0 * f))
    noisex1 = int(np.round(30.0 * f));           noisey1 = int(np.round(30.0 * f))
    noisex2 = int(np.round(30.0 * f));           noisey2 = int(width - np.round(30.0 * f))
    noisex3 = int(width - np.round(30.0 * f));   noisey3 = int(np.round(30.0 * f))

    noise  = get_noise_pixels(noisex,  noisey)
    noise1 = get_noise_pixels(noisex1, noisey1)
    noise2 = get_noise_pixels(noisex2, noisey2)
    noise3 = get_noise_pixels(noisex3, noisey3)

    SD1 = np.std(noise,  ddof=1) if len(noise)  > 1 else 0.0
    SD2 = np.std(noise1, ddof=1) if len(noise1) > 1 else 0.0
    SD3 = np.std(noise2, ddof=1) if len(noise2) > 1 else 0.0
    SD4 = np.std(noise3, ddof=1) if len(noise3) > 1 else 0.0
    SD  = (SD1 + SD2 + SD3 + SD4) / 4.0

    if SD == 0:
        return None, None

    SignalNoiseRatio = 0.655 * (intensity / SD)

    # Build highlighted image for display
    I_highlight = I.copy()
    h_idx, w_idx = np.indices(I.shape)
    for cx, cy in [(noisex, noisey), (noisex1, noisey1), (noisex2, noisey2), (noisex3, noisey3)]:
        mask = np.hypot(w_idx - cy, h_idx - cx) < int(np.round(20.0 * f))
        I_highlight[mask & (I < 500)] = 2000.0
    I_highlight[np.hypot(w_idx - midpty, h_idx - midptx) < int(np.round(79.0 * f))] = 2000.0

    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    axes[0].imshow(I, cmap='gray');           axes[0].set_title('Original Image');      axes[0].axis('off')
    axes[1].imshow(I_highlight, cmap='gray'); axes[1].set_title('SNR ROI Highlighted'); axes[1].axis('off')
    plt.tight_layout()

    return {'snr': SignalNoiseRatio}, fig


def main():
    plt.ion()
    
    fname, pathname = uiputfile('*.xlsx;*.xls', 'Select file to write results to:')
    if not fname:
        print("No file selected. Exiting.")
        return
    results_file = os.path.join(pathname, fname)
    
    button_name = questdlg('What series?', 'Signal-Noise Ratio', 'ACR series', 'Site series', 'ACR series')
    if button_name == 'ACR series':
        button_name = questdlg('What series?', 'Signal-Noise Ratio', 'ACR T1 series', 'ACR T2 series', 'ACR T1 series')
    else:
        button_name = questdlg('What series?', 'Signal-Noise Ratio', 'Site T1 series', 'Site T2 series', 'Site T1 series')
        
    if button_name == 'ACR T1 series':
        cell = 'B99'
    elif button_name == 'ACR T2 series':
        cell = 'B86'
    elif button_name == 'Site T1 series' or button_name == 'Site T2 series':
        cell = 'B10'
    else:
        cell = 'B99'
        
    s7_fname, s7_pathname = uigetfile('*.dcm', 'Select Slice 7')
    if not s7_fname:
        return
    s7_path = os.path.join(s7_pathname, s7_fname)
    
    ds = pydicom.dcmread(s7_path)
    I = ds.pixel_array.astype(float)
    
    fig1 = plt.figure(num='Original Image')
    plt.imshow(I, cmap='gray')
    plt.title('Original Image')
    plt.draw()
    plt.pause(1)
    
    x, y = np.nonzero(I > 500)
    maxx, minx = x.max(), x.min()
    maxy, miny = y.max(), y.min()
    midptx = int(np.round(minx + (maxx - minx) / 2.0))
    midpty = int(np.round(miny + (maxy - miny) / 2.0))
    
    width = float(ds.Rows)
    f = width / 256.0
    
    # Filter with disk of radius 79*f
    h = fspecial('disk', int(np.round(79.0 * f)))
    Ifilt = imfilter(I, h)
    
    fig1.clear()
    plt.imshow(Ifilt, cmap='gray')
    plt.title('Filtered Image')
    plt.draw()
    plt.pause(1)
    
    intensity = Ifilt[midptx, midpty]
    
    # Noise center coordinates
    noisex = int(width - np.round(30.0 * f))
    noisey = int(width - np.round(30.0 * f))
    noisex1 = int(np.round(30.0 * f))
    noisey1 = int(np.round(30.0 * f))
    noisex2 = int(np.round(30.0 * f))
    noisey2 = int(width - np.round(30.0 * f))
    noisex3 = int(width - np.round(30.0 * f))
    noisey3 = int(np.round(30.0 * f))
    
    # Background pixels (I < 500)
    bg_u, bg_v = np.nonzero(I < 500)
    
    def get_noise_pixels(center_x, center_y):
        dist = np.hypot(bg_v - center_y, bg_u - center_x)
        mask = dist < int(np.round(20.0 * f))
        return I[bg_u[mask], bg_v[mask]]
        
    noise = get_noise_pixels(noisex, noisey)
    noise1 = get_noise_pixels(noisex1, noisey1)
    noise2 = get_noise_pixels(noisex2, noisey2)
    noise3 = get_noise_pixels(noisex3, noisey3)
    
    # Standard deviations (degrees of freedom = 1 as standard std)
    SD1 = np.std(noise, ddof=1) if len(noise) > 1 else 0.0
    SD2 = np.std(noise1, ddof=1) if len(noise1) > 1 else 0.0
    SD3 = np.std(noise2, ddof=1) if len(noise2) > 1 else 0.0
    SD4 = np.std(noise3, ddof=1) if len(noise3) > 1 else 0.0
    
    SD = (SD1 + SD2 + SD3 + SD4) / 4.0
    
    SignalNoiseRatio = 0.655 * (intensity / SD)
    success = xlswrite(results_file, SignalNoiseRatio, button_name, cell)
    
    # Highlight ROI for display
    I_highlight = I.copy()
    # set the four noise regions to 2000
    h_idx, w_idx = np.indices(I.shape)
    for cx, cy in [(noisex, noisey), (noisex1, noisey1), (noisex2, noisey2), (noisex3, noisey3)]:
        mask = np.hypot(w_idx - cy, h_idx - cx) < int(np.round(20.0 * f))
        I_highlight[mask & (I < 500)] = 2000.0
        
    # set the large circle region to 2000
    large_circle_mask = np.hypot(w_idx - midpty, h_idx - midptx) < int(np.round(79.0 * f))
    I_highlight[large_circle_mask] = 2000.0
    
    fig1.clear()
    plt.imshow(I_highlight, cmap='gray')
    plt.title('SNR ROI Highlighted')
    plt.draw()
    plt.pause(5)
    plt.close('all')
    
    res_str = f"The Signal-Noise Ratio is....{SignalNoiseRatio:.2f}."
    if success == 1:
        res_str += " The result has been successfully written to Excel."
    else:
        res_str += " Error: The result has not been written to Excel."
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
