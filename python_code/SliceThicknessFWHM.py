import os
import pydicom
import numpy as np
import scipy.ndimage
import matplotlib.pyplot as plt
from matlab_compat import uiputfile, uigetfile, questdlg, msgbox, xlswrite, imcrop, imresize, fspecial, imfilter

def calculate_fwhm(profile):
    profile = np.asarray(profile, dtype=float)
    x = np.arange(1, len(profile) + 1)
    
    p_max = profile.max()
    if p_max == 0:
        return 0.0
    p = profile / p_max
    
    N = len(p)
    lev50 = 0.5
    
    if p[0] < lev50:
        centerindex = np.argmax(p) + 1
    else:
        centerindex = 1
        
    i = 1
    while i < N and np.sign(p[i] - lev50) == np.sign(p[i-1] - lev50):
        i += 1
        
    if i >= N:
        return np.nan
        
    interp = (lev50 - p[i-1]) / (p[i] - p[i-1])
    tlead = x[i-1] + interp * (x[i] - x[i-1])
    
    i = int(centerindex)
    while i < N and np.sign(p[i] - lev50) == np.sign(p[i-1] - lev50):
        i += 1
        
    if i < N:
        interp = (lev50 - p[i-1]) / (p[i] - p[i-1])
        ttrail = x[i-1] + interp * (x[i] - x[i-1])
        width = ttrail - tlead
    else:
        width = np.nan
        
    return width

def main():
    plt.ion()
    
    fname, pathname = uiputfile('*.xlsx;*.xls', 'Save As')
    if not fname:
        print("No file selected. Exiting.")
        return
    results_file = os.path.join(pathname, fname)
    
    button_name = questdlg('What series?', 'Spatial Resolution', 'ACR T1 series', 'ACR T2 series', 'ACR T1 series')
    if button_name == 'ACR T1 series':
        cell = 'B25'
    elif button_name == 'ACR T2 series':
        cell = 'B17'
    else:
        cell = 'B25'
        
    s1_fname, s1_pathname = uigetfile('*.dcm', 'Select Slice 1')
    if not s1_fname:
        return
    s1_path = os.path.join(s1_pathname, s1_fname)
    
    ds = pydicom.dcmread(s1_path)
    I = ds.pixel_array.astype(float)
    width = float(ds.Rows)
    f = width / 250.0
    
    rect = [round(10*f), round(10*f), width - round(20*f), width - round(20*f)]
    I_crop = imcrop(I, rect)
    
    fig1 = plt.figure(num='Original Image')
    plt.imshow(I_crop, cmap='gray')
    plt.title('Original Image - Slice 1 of ACR Phantom')
    plt.draw()
    plt.pause(1)
    
    # edge detection
    gx = scipy.ndimage.sobel(I_crop, axis=1)
    gy = scipy.ndimage.sobel(I_crop, axis=0)
    grad = np.hypot(gx, gy)
    bw = (grad >= grad.max() * 0.1).astype(int)
    
    u, v = np.nonzero(bw == 1)
    maxx, minx = u.max(), u.min()
    midptx = int(np.round((maxx + minx) / 2))
    maxy, miny = v.max(), v.min()
    midpty = int(np.round((maxy + miny) / 2))
    
    # crop ramp regions
    rect_ramp = [int(np.round(midpty - f*60)), int(np.round(midptx - f*10)), int(np.round(f*120)), int(np.round(f*20))]
    I2 = imcrop(I_crop, rect_ramp)
    
    fig2 = plt.figure(num=2)
    plt.imshow(I2, cmap='gray')
    plt.title('Ramp Crop')
    plt.draw()
    plt.pause(1)
    
    # Edge on ramp crop
    gx2 = scipy.ndimage.sobel(I2, axis=1)
    gy2 = scipy.ndimage.sobel(I2, axis=0)
    grad2 = np.hypot(gx2, gy2)
    bw2 = (grad2 >= grad2.max() * 0.1).astype(int)
    
    u2, v2 = np.nonzero(bw2 == 1)
    maxx2, minx2 = u2.max(), u2.min()
    midptx2 = int(np.round((maxx2 + minx2) / 2))
    
    ramp1 = midptx2 - 5
    ramp2 = midptx2 + 5
    
    a3_idx = int(ramp1 + 2)
    a4_idx = int(ramp1 + 3)
    a5_idx = int(ramp1 + 4)
    
    b3_idx = int(ramp2 - 2)
    b4_idx = int(ramp2 - 3)
    b5_idx = int(ramp2 - 4)
    
    # circular filter
    h_kernel = fspecial('disk', f*2)
    I2smooth = imfilter(I2, h_kernel)
    
    a_mean = np.mean(I2smooth[[a3_idx, a4_idx, a5_idx], :], axis=0)
    b_mean = np.mean(I2smooth[[b3_idx, b4_idx, b5_idx], :], axis=0)
    
    # Plot curves
    fig3 = plt.figure(num='FWHM curves')
    plt.plot(a_mean, 'r-', label='Bottom Ramp', linewidth=2)
    plt.plot(b_mean, 'b-', label='Top Ramp', linewidth=2)
    plt.grid(True)
    plt.legend()
    plt.xlabel('Pixel Number')
    plt.ylabel('Pixel Value')
    plt.draw()
    plt.pause(1)
    
    # Highlight lines on I2
    I2_disp = I2.copy()
    I2_disp[a3_idx, :] = 1400.0
    I2_disp[a4_idx, :] = 1400.0
    I2_disp[a5_idx, :] = 1400.0
    I2_disp[b3_idx, :] = 1400.0
    I2_disp[b4_idx, :] = 1400.0
    I2_disp[b5_idx, :] = 1400.0
    
    I3 = imresize(I2_disp, 3)
    fig4 = plt.figure(num='Slice Thickness Insert')
    plt.imshow(I3, cmap='gray')
    plt.title('Magnified Slice Thickness Insert')
    plt.draw()
    plt.pause(1)
    
    # Calculate widths
    width1 = calculate_fwhm(a_mean)
    width2 = calculate_fwhm(b_mean)
    
    width1 = width1 * (250.0 / width)
    width2 = width2 * (250.0 / width)
    slice_thickness = 0.2 * ((width1 * width2) / (width1 + width2))
    
    success1 = xlswrite(results_file, slice_thickness, button_name, cell)
    
    res_str = f"The slice thickness is...{slice_thickness:.2f} mm. Note: The slice thickness should be 5 mm +/- 0.7 mm."
    if success1 == 1:
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
