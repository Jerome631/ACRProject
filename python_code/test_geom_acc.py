import os
import pydicom
import numpy as np
import scipy.ndimage
import matplotlib.pyplot as plt
from matlab_compat import uiputfile, uigetfile, msgbox, xlswrite, imcrop, imrotate, imresize

def edge_sobel(I, threshold=None):
    gx = scipy.ndimage.sobel(I, axis=1)
    gy = scipy.ndimage.sobel(I, axis=0)
    grad = np.hypot(gx, gy)
    if threshold is None:
        threshold = grad.max() * 0.1
    return (grad >= threshold).astype(int)

def compute(loc_path, s1_path, s5_path):
    """Computation for geometric accuracy

    Args:
        loc_path: path to localizer DICOM file
        s1_path:  path to slice 1 DICOM file
        s5_path:  path to slice 5 DICOM file

    Returns:
        results (dict): localizer_length, slice1_vertical, slice1_horizontal,
                        slice5_vertical, slice5_horizontal, slice5_diag1, slice5_diag2
        figs (list):    [fig_localizer, fig_slices] : matplotlib Figure objects
    """
    from matlab_compat import imcrop, imrotate

    # ── Localizer ──────────────────────────────────────────
    ds = pydicom.dcmread(loc_path)
    I  = ds.pixel_array.astype(float)
    bw = edge_sobel(I, 100)

    u, v = np.nonzero(bw == 1)
    Nbin = max(int(u.max() - u.min()), 1)
    counts, _ = np.histogram(u, bins=Nbin, range=(u.min(), u.max()))
    y_indices  = np.where(counts > counts.max() / 2)[0]

    # Use actual DICOM pixel spacing for accurate mm conversion
    ps = getattr(ds, 'PixelSpacing', None)
    if ps is not None and float(ps[0]) > 0:
        loc_pixel_spacing = float(ps[0])
    else:
        # Fallback to scale factor if PixelSpacing tag is missing
        width = float(ds.Rows)
        loc_pixel_spacing = 250.0 / width
    dist  = (y_indices[-1] - y_indices[0]) * loc_pixel_spacing if len(y_indices) >= 2 else 0.0

    fig_loc, axes_loc = plt.subplots(1, 2, figsize=(10, 4))
    axes_loc[0].imshow(I,  cmap='gray'); axes_loc[0].set_title('Localizer — Original'); axes_loc[0].axis('off')
    axes_loc[1].imshow(bw, cmap='gray'); axes_loc[1].set_title('Localizer — Edge Map'); axes_loc[1].axis('off')
    plt.tight_layout()

    # ── Slice 1 ────────────────────────────────────────────
    ds2 = pydicom.dcmread(s1_path)
    I2  = ds2.pixel_array.astype(float)
    width = float(ds2.Rows); f = width / 250.0

    rect     = [round(10*f), round(10*f), width - round(20*f), width - round(20*f)]
    I2_crop  = imcrop(I2, rect)
    bw2      = edge_sobel(I2_crop)
    u2, v2   = np.nonzero(bw2 == 1)
    maxy2, miny2 = u2.max(), u2.min()
    maxx2, minx2 = v2.max(), v2.min()
    midpty = miny2 + (maxy2 - miny2) / 2.0
    midptx = minx2 + (maxx2 - minx2) / 2.0

    disttopbotSlice1    = (maxy2 - miny2) / f
    distleftrightSlice1 = (maxx2 - minx2) / f

    # ── Slice 5 ────────────────────────────────────────────
    ds3      = pydicom.dcmread(s5_path)
    I3       = ds3.pixel_array.astype(float)
    I3_crop  = imcrop(I3, rect)
    bw3      = edge_sobel(I3_crop)
    u3, v3   = np.nonzero(bw3 == 1)
    maxy3, miny3 = u3.max(), u3.min()
    maxx3, minx3 = v3.max(), v3.min()
    midpty3  = miny3 + (maxy3 - miny3) / 2.0
    midptx3  = minx3 + (maxx3 - minx3) / 2.0

    disttopbotSlice5    = (maxy3 - miny3) / f
    distleftrightSlice5 = (maxx3 - minx3) / f

    # Diagonals — original MATLAB code reuses Slice 1 edge indices
    I4       = imrotate(I3_crop, 45, 'bilinear')
    bw4      = edge_sobel(I4)
    distdiag1 = (maxx2 - minx2) / f
    distdiag2 = (maxy2 - miny2) / f

    fig_slices, axes_s = plt.subplots(1, 3, figsize=(15, 4))
    axes_s[0].imshow(I2_crop, cmap='gray')
    axes_s[0].plot([midptx, midptx], [miny2, maxy2], 'r-', lw=2)
    axes_s[0].plot([minx2, maxx2], [midpty, midpty], 'r-', lw=2)
    axes_s[0].set_title('Slice 1 — Diameters'); axes_s[0].axis('off')
    axes_s[1].imshow(I3_crop, cmap='gray')
    axes_s[1].plot([midptx3, midptx3], [miny3, maxy3], 'r-', lw=2)
    axes_s[1].plot([minx3, maxx3], [midpty3, midpty3], 'r-', lw=2)
    axes_s[1].set_title('Slice 5 — Diameters'); axes_s[1].axis('off')
    axes_s[2].imshow(I4, cmap='gray'); axes_s[2].set_title('Slice 5 — Rotated 45°'); axes_s[2].axis('off')
    plt.tight_layout()

    results = {
        'localizer_length':     dist,
        'slice1_vertical':      disttopbotSlice1,
        'slice1_horizontal':    distleftrightSlice1,
        'slice5_vertical':      disttopbotSlice5,
        'slice5_horizontal':    distleftrightSlice5,
        'slice5_diag1':         distdiag1,
        'slice5_diag2':         distdiag2,
    }
    return results, [fig_loc, fig_slices]


def main():
    plt.ion() # interactive mode
    
    fname, pathname = uiputfile('*.xlsx;*.xls', 'Select file to write results to:')
    if not fname:
        print("No file selected. Exiting.")
        return
    results_file = os.path.join(pathname, fname)
    
    msgbox('This test should only be performed on the ACR T1 series', 'GEOMETRIC ACCURACY')
    
    # --- LOCALIZER ---
    loc_fname, loc_pathname = uigetfile('*.dcm', 'Select Localizer Image')
    if not loc_fname:
        return
    loc_path = os.path.join(loc_pathname, loc_fname)
    
    ds = pydicom.dcmread(loc_path)
    I = ds.pixel_array.astype(float)
    
    fig, ax = plt.subplots(num=1, figsize=(6,6))
    ax.imshow(I, cmap='gray')
    ax.set_title('Original Image')
    plt.draw()
    plt.pause(1)
    
    bw = edge_sobel(I, 100)
    ax.clear()
    ax.imshow(bw, cmap='gray')
    ax.set_title('Edge Image')
    plt.draw()
    plt.pause(1)
    
    u, v = np.nonzero(bw == 1)
    Nbin = int(u.max() - u.min())
    if Nbin < 1:
        Nbin = 1
        
    # histogram of row coordinates
    counts, bin_edges = np.histogram(u, bins=Nbin, range=(u.min(), u.max()))
    max_count = counts.max()
    y_indices = np.where(counts > (max_count / 2))[0]
    
    width = float(ds.Rows) # Width/Rows
    f = width / 250.0
    
    # dist = (y[1] - y[0]) / f
    if len(y_indices) >= 2:
        dist = (y_indices[-1] - y_indices[0]) / f
    else:
        dist = 0.0
        
    success1 = xlswrite(results_file, dist, 'ACR T1 series', 'B10')
    
    res_str = f"The Localizer end-to-end length is....{dist:.2f} mm. It should be 148mm +/- 2mm. "
    if success1 == 1:
        res_str += " The result has been successfully written to Excel."
    else:
        res_str += " Error: The result has not been written to Excel."
    msgbox(res_str, 'RESULT')
    
    # --- SLICE 1 ---
    s1_fname, s1_pathname = uigetfile('*.dcm', 'Select Slice 1:')
    if not s1_fname:
        return
    s1_path = os.path.join(s1_pathname, s1_fname)
    
    ds2 = pydicom.dcmread(s1_path)
    I2 = ds2.pixel_array.astype(float)
    width = float(ds2.Rows)
    f = width / 250.0
    
    # crop rect = [10*f, 10*f, width - 20*f, width - 20*f]
    rect = [round(10*f), round(10*f), width - round(20*f), width - round(20*f)]
    I2_crop = imcrop(I2, rect)
    
    ax.clear()
    ax.imshow(I2_crop, cmap='gray')
    ax.set_title('Cropped Slice 1')
    plt.draw()
    plt.pause(1)
    
    bw2 = edge_sobel(I2_crop)
    ax.clear()
    ax.imshow(bw2, cmap='gray')
    ax.set_title('Edge Slice 1')
    
    u2, v2 = np.nonzero(bw2 == 1)
    maxy2, miny2 = u2.max(), u2.min()
    midpty = miny2 + (maxy2 - miny2)/2.0
    maxx2, minx2 = v2.max(), v2.min()
    midptx = minx2 + (maxx2 - minx2)/2.0
    
    # plot horizontal and vertical diameters
    ax.plot([midptx, midptx], [miny2, maxy2], 'r-', linewidth=2)
    ax.plot([minx2, maxx2], [midpty, midpty], 'r-', linewidth=2)
    plt.draw()
    plt.pause(1)
    
    disttopbotSlice1 = (maxy2 - miny2) / f
    distleftrightSlice1 = (maxx2 - minx2) / f
    
    success2 = xlswrite(results_file, disttopbotSlice1, 'ACR T1 series', 'B12')
    success3 = xlswrite(results_file, distleftrightSlice1, 'ACR T1 series', 'C12')
    
    res_str2 = (f"The vertical diameter of Slice 1 is....{disttopbotSlice1:.2f} mm. "
                f"The horizontal diameter of Slice 1 is....{distleftrightSlice1:.2f} mm. "
                f"The diameter should be 190 mm +/- 2 mm. ")
    if success2 == 1 and success3 == 1:
        res_str2 += " Results have been successfully written to Excel."
    else:
        res_str2 += " Error: Results have not been written to Excel."
    msgbox(res_str2, 'RESULT')
    
    # --- SLICE 5 ---
    s5_fname, s5_pathname = uigetfile('*.dcm', 'Select Slice 5:')
    if not s5_fname:
        return
    s5_path = os.path.join(s5_pathname, s5_fname)
    
    ds3 = pydicom.dcmread(s5_path)
    I3 = ds3.pixel_array.astype(float)
    I3_crop = imcrop(I3, rect)
    
    ax.clear()
    ax.imshow(I3_crop, cmap='gray')
    ax.set_title('Cropped Slice 5')
    plt.draw()
    plt.pause(1)
    
    bw3 = edge_sobel(I3_crop)
    ax.clear()
    ax.imshow(bw3, cmap='gray')
    ax.set_title('Edge Slice 5')
    
    u3, v3 = np.nonzero(bw3 == 1)
    maxy3, miny3 = u3.max(), u3.min()
    midpty3 = miny3 + (maxy3 - miny3)/2.0
    maxx3, minx3 = v3.max(), v3.min()
    midptx3 = minx3 + (maxx3 - minx3)/2.0
    
    ax.plot([midptx3, midptx3], [miny3, maxy3], 'r-', linewidth=2)
    ax.plot([minx3, maxx3], [midpty3, midpty3], 'r-', linewidth=2)
    plt.draw()
    plt.pause(1)
    
    disttopbotSlice5 = (maxy3 - miny3) / f
    distleftrightSlice5 = (maxx3 - minx3) / f
    
    success4 = xlswrite(results_file, disttopbotSlice5, 'ACR T1 series', 'B14')
    success5 = xlswrite(results_file, distleftrightSlice5, 'ACR T1 series', 'C14')
    
    # Rotate by 45 degrees
    I4 = imrotate(I3_crop, 45, 'bilinear')
    bw4 = edge_sobel(I4)
    
    ax.clear()
    ax.imshow(bw4, cmap='gray')
    ax.set_title('Rotated Slice 5 Edges')
    
    u4, v4 = np.nonzero(bw4 == 1)
    maxy4, miny4 = u4.max(), u4.min()
    midpty4 = miny4 + (maxy4 - miny4)/2.0
    maxx4, minx4 = v4.max(), v4.min()
    midptx4 = minx4 + (maxx4 - minx4)/2.0
    
    ax.plot([midptx4, midptx4], [miny4, maxy4], 'r-', linewidth=2)
    ax.plot([minx4, maxx4], [midpty4, midpty4], 'r-', linewidth=2)
    plt.draw()
    plt.pause(1)
    
    # MATLAB uses maxx2, minx2, maxy2, miny2 (Slice 1 values) for diagonal computations
    distdiag1 = (maxx2 - minx2) / f
    distdiag2 = (maxy2 - miny2) / f
    
    success6 = xlswrite(results_file, distdiag1, 'ACR T1 series', 'D14')
    success7 = xlswrite(results_file, distdiag2, 'ACR T1 series', 'E14')
    
    res_str3 = (f"The vertical diameter of Slice 5 is....{disttopbotSlice5:.2f} mm. "
                f"The horizontal diameter of Slice 5 is....{distleftrightSlice5:.2f} mm. "
                f"The first diagonal diameter of Slice 5 is....{distdiag1:.2f} mm. "
                f"The second diagonal diameter of Slice 5 is....{distdiag2:.2f} mm. "
                f"The diameter should be 190 mm +/- 2 mm. ")
    if success4 == 1 and success5 == 1 and success6 == 1 and success7 == 1:
        res_str3 += " Results have been successfully written to Excel."
    else:
        res_str3 += " Error: Results have not been written to Excel."
    msgbox(res_str3, 'RESULT')
    
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
