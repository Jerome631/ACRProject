import os
import pydicom
import numpy as np
import matplotlib.pyplot as plt
from matlab_compat import uiputfile, uigetfile, msgbox, xlswrite, fspecial, imfilter, roipoly

def compute(s7_path):
    """Computation for the Percent Signal Ghosting test.

    Args:
        s7_path: path to slice 7 DICOM file (ACR T1 series only)

    Returns:
        results (dict): {'ghosting_ratio': float} : raw ratio (multiply by 100 for %)
        fig:            matplotlib Figure showing highlighted ROIs
    """
    ds = pydicom.dcmread(s7_path)
    I  = ds.pixel_array.astype(float)
    width = float(ds.Rows)
    f     = width / 250.0

    x, y = np.nonzero(I > 500)
    if len(x) == 0:
        return None, None
    maxx, minx = x.max(), x.min()
    maxy, miny = y.max(), y.min()
    midptx = int(np.round(minx + (maxx - minx) / 2.0))
    midpty = int(np.round(miny + (maxy - miny) / 2.0))

    # Horizontal (top/bottom) filter
    h     = fspecial('average', [int(np.round(16.0 * f)), int(np.round(64.0 * f))])
    Ifilt = imfilter(I, h)

    # ROI polygons for top and bottom
    c3 = [midpty - int(np.round(64*f/2)), midpty - int(np.round(64*f/2)),
          midpty + int(np.round(64*f/2)), midpty + int(np.round(64*f/2))]
    r3 = [int(minx/2) - int(np.round(16*f/2)), int(minx/2) + int(np.round(16*f/2)),
          int(minx/2) + int(np.round(16*f/2)), int(minx/2) - int(np.round(16*f/2))]
    BW3 = roipoly(I, c3, r3)

    c4 = [midpty - int(np.round(64*f/2)), midpty - int(np.round(64*f/2)),
          midpty + int(np.round(64*f/2)), midpty + int(np.round(64*f/2))]
    r4 = [int(width - (width - maxx)/2) - int(np.round(16*f/2)),
          int(width - (width - maxx)/2) + int(np.round(16*f/2)),
          int(width - (width - maxx)/2) + int(np.round(16*f/2)),
          int(width - (width - maxx)/2) - int(np.round(16*f/2))]
    BW4 = roipoly(I, c4, r4)

    # Vertical (left/right) filter
    h2     = fspecial('average', [int(np.round(64.0 * f)), int(np.round(16.0 * f))])
    Ifilt2 = imfilter(I, h2)

    c  = [int(miny/2) - int(np.round(16*f/2)), int(miny/2) + int(np.round(16*f/2)),
          int(miny/2) + int(np.round(16*f/2)), int(miny/2) - int(np.round(16*f/2))]
    r  = [midptx - int(np.round(64*f/2)), midptx - int(np.round(64*f/2)),
          midptx + int(np.round(64*f/2)), midptx + int(np.round(64*f/2))]
    BW = roipoly(I, c, r)

    c2 = [int(width - (width - maxy)/2) - int(np.round(16*f/2)),
          int(width - (width - maxy)/2) + int(np.round(16*f/2)),
          int(width - (width - maxy)/2) + int(np.round(16*f/2)),
          int(width - (width - maxy)/2) - int(np.round(16*f/2))]
    r2 = [midptx - int(np.round(64*f/2)), midptx - int(np.round(64*f/2)),
          midptx + int(np.round(64*f/2)), midptx + int(np.round(64*f/2))]
    BW2 = roipoly(I, c2, r2)

    # Large circular filter for phantom centre
    h3     = fspecial('disk', int(np.round(79.0 * f)))
    Ifilt3 = imfilter(I, h3)
    largeROI = Ifilt3[midptx, midpty]

    xtop    = midpty;                                          ytop    = int(np.round(minx / 2.0))
    xbottom = midpty;                                          ybottom = int(np.round(width - (width - maxx) / 2.0))
    xleft   = int(np.round(miny / 2.0));                      yleft   = midptx
    xright  = int(np.round(maxx + (256.0 * f - maxx) / 2.0)); yright  = midptx

    top    = Ifilt[min(ytop,    I.shape[0]-1), xtop]
    bottom = Ifilt[min(ybottom, I.shape[0]-1), xbottom]
    left   = Ifilt2[yleft,  min(xleft,  I.shape[1]-1)]
    right  = Ifilt2[yright, min(xright, I.shape[1]-1)]

    ghostingratio = abs(((top + bottom) - (left + right)) / (2.0 * largeROI))

    # Figure — highlight all ROIs
    BW_all = BW + BW2 + BW3 + BW4
    J = I.copy()
    J[BW_all > 0] += 800.0
    h_idx, w_idx = np.indices(I.shape)
    J[np.hypot(w_idx - midpty, h_idx - midptx) < (79.0 * f)] = 1.0

    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    axes[0].imshow(I, cmap='gray'); axes[0].set_title('Original Image');   axes[0].axis('off')
    axes[1].imshow(J, cmap='gray'); axes[1].set_title('Highlighted ROIs'); axes[1].axis('off')
    plt.tight_layout()

    return {'ghosting_ratio': ghostingratio}, fig


def main():
    plt.ion()
    
    msgbox('This test should only be performed on the ACR T1 series', 'PERCENT-SIGNAL GHOSTING')
    
    fname, pathname = uiputfile('*.xlsx;*.xls', 'Please select files to write results to')
    if not fname:
        print("No file selected. Exiting.")
        return
    results_file = os.path.join(pathname, fname)
    
    s7_fname, s7_pathname = uigetfile('*.dcm', 'Select Slice 7')
    if not s7_fname:
        return
    s7_path = os.path.join(s7_pathname, s7_fname)
    
    ds = pydicom.dcmread(s7_path)
    I = ds.pixel_array.astype(float)
    
    fig, ax = plt.subplots(num=1, figsize=(6,6))
    ax.imshow(I, cmap='gray')
    ax.set_title('Original Slice 7')
    plt.draw()
    plt.pause(1)
    
    width = float(ds.Rows)
    f = width / 250.0
    
    # Threshold to find phantom bounds
    x, y = np.nonzero(I > 500)
    maxx, minx = x.max(), x.min()
    maxy, miny = y.max(), y.min()
    midptx = int(np.round(minx + (maxx - minx) / 2.0))
    midpty = int(np.round(miny + (maxy - miny) / 2.0))
    
    # Horizontal average filter for top and bottom background regions
    h = fspecial('average', [int(np.round(16.0 * f)), int(np.round(64.0 * f))])
    Ifilt = imfilter(I, h)
    
    # Define top (BW3) and bottom (BW4) ROIs
    c3 = [midpty - int(np.round(64*f/2)), midpty - int(np.round(64*f/2)), midpty + int(np.round(64*f/2)), midpty + int(np.round(64*f/2))]
    r3 = [int(minx/2) - int(np.round(16*f/2)), int(minx/2) + int(np.round(16*f/2)), int(minx/2) + int(np.round(16*f/2)), int(minx/2) - int(np.round(16*f/2))]
    BW3 = roipoly(I, c3, r3)
    
    c4 = [midpty - int(np.round(64*f/2)), midpty - int(np.round(64*f/2)), midpty + int(np.round(64*f/2)), midpty + int(np.round(64*f/2))]
    r4 = [int(width - (width - maxx)/2) - int(np.round(16*f/2)), int(width - (width - maxx)/2) + int(np.round(16*f/2)), int(width - (width - maxx)/2) + int(np.round(16*f/2)), int(width - (width - maxx)/2) - int(np.round(16*f/2))]
    BW4 = roipoly(I, c4, r4)
    
    # Vertical average filter for left and right background regions
    h2 = fspecial('average', [int(np.round(64.0 * f)), int(np.round(16.0 * f))])
    Ifilt2 = imfilter(I, h2)
    
    # Define left (BW) and right (BW2) ROIs
    c = [int(miny/2) - int(np.round(16*f/2)), int(miny/2) + int(np.round(16*f/2)), int(miny/2) + int(np.round(16*f/2)), int(miny/2) - int(np.round(16*f/2))]
    r = [midptx - int(np.round(64*f/2)), midptx - int(np.round(64*f/2)), midptx + int(np.round(64*f/2)), midptx + int(np.round(64*f/2))]
    BW = roipoly(I, c, r)
    
    c2 = [int(width - (width - maxy)/2) - int(np.round(16*f/2)), int(width - (width - maxy)/2) + int(np.round(16*f/2)), int(width - (width - maxy)/2) + int(np.round(16*f/2)), int(width - (width - maxy)/2) - int(np.round(16*f/2))]
    r2 = [midptx - int(np.round(64*f/2)), midptx - int(np.round(64*f/2)), midptx + int(np.round(64*f/2)), midptx + int(np.round(64*f/2))]
    BW2 = roipoly(I, c2, r2)
    
    # Combine masks and highlight regions
    BW_all = BW + BW2 + BW3 + BW4
    J = I.copy()
    J[BW_all > 0] += 800.0
    
    # Large circular average filter
    h3 = fspecial('disk', int(np.round(79.0 * f)))
    Ifilt3 = imfilter(I, h3)
    
    largeROI = Ifilt3[midptx, midpty]
    
    xtop = midpty
    ytop = int(np.round(minx / 2.0))
    top = Ifilt[ytop, xtop]
    
    xbottom = midpty
    ybottom = int(np.round(width - (width - maxx) / 2.0))
    bottom = Ifilt[ybottom, xbottom]
    
    xleft = int(np.round(miny / 2.0))
    yleft = midptx
    left = Ifilt2[yleft, xleft]
    
    xright = int(np.round(maxx + (256.0 * f - maxx) / 2.0))
    yright = midptx
    right = Ifilt2[yright, xright]
    
    ghostingratio = abs(((top + bottom) - (left + right)) / (2.0 * largeROI))
    success = xlswrite(results_file, ghostingratio, 'ACR T1 series', 'B67')
    
    # Highlight large circular ROI
    h_idx, w_idx = np.indices(I.shape)
    dist = np.hypot(w_idx - midpty, h_idx - midptx)
    J[dist < (79.0 * f)] = 1.0
    
    ax.clear()
    ax.imshow(J, cmap='gray')
    ax.set_title('Highlighted ROIs')
    plt.draw()
    plt.pause(1)
    
    res_str = f"The Ghosting Ratio is....{ghostingratio:.4f}."
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
