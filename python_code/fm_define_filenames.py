import os
import sys

def fm_define_filenames(data):
    n_channels = data['n_channels']
    n_echoes = data['n_echoes']
    n_echoes_to_use = data['n_echoes_to_use']
    writefile_dir = data['writefile_dir']
    sep_dir = data['sep_dir']
    extension = data['extension']
    channel_key = data['channel_key']
    echoes_to_use = data['echoes_to_use']
    multi_channel_data = data['multi_channel_data']

    # cell(n_channels, 2)
    fnCurrentFieldmaps = [[None for _ in range(2)] for _ in range(n_channels)]
    # cell(n_channels, n_echoes)
    fnCurrentMagImages = [[None for _ in range(n_echoes)] for _ in range(n_channels)]
    fnRawPhaseImages = [[None for _ in range(n_echoes)] for _ in range(n_channels)]
    fnCurrentPhaseImages = [[None for _ in range(n_echoes)] for _ in range(n_channels)]
    fnCurrentPhaseImagesPC = [[None for _ in range(n_echoes)] for _ in range(n_channels)]
    fnBetMaskSep = [[None for _ in range(n_echoes)] for _ in range(n_channels)]

    # cell(n_channels, 1) -> [None for _ in range(n_channels)]
    fnCurrentPhaseOffsets = [None for _ in range(n_channels)]

    # cell(1, n_echoes) -> [None for _ in range(n_echoes)]
    fnCombPhase = [None for _ in range(n_echoes)]
    fnCombMag = [None for _ in range(n_echoes)]
    fnCombPhaseDiff = [None for _ in range(n_echoes)]
    fnCombMagDiff = [None for _ in range(n_echoes)]

    # cell(n_echoes-1) -> cell(n_echoes_to_use) -> [None for _ in range(n_echoes_to_use)]
    fnMedianFM = [None for _ in range(n_echoes_to_use)]
    fnWMedianFM = [None for _ in range(n_echoes_to_use)]
    fnMedianFiltMedianFM = [None for _ in range(n_echoes_to_use)]
    fnMeanFM = [None for _ in range(n_echoes_to_use)]
    fnWMeanFM = [None for _ in range(n_echoes_to_use)]
    fnTWMeanFM = [None for _ in range(n_echoes_to_use)]
    fnStdFM = [None for _ in range(n_echoes_to_use)]
    fnCVMap = [None for _ in range(n_echoes_to_use)]
    fnNCMap = [None for _ in range(n_echoes_to_use)]
    fnNzMap = [None for _ in range(n_echoes_to_use)]
    fnWMeanPI = [None for _ in range(n_echoes_to_use)]

    for j in range(n_echoes_to_use):
        n = echoes_to_use[j]
        # echoes_to_use is 1-based indices from MATLAB, but let's keep them as values
        fnCombPhase[j] = os.path.join(writefile_dir, f'Combined_phase_{j+1}{extension}')
        fnCombMag[j] = os.path.join(writefile_dir, f'Combined_mag_{j+1}{extension}')
        fnCombPhaseDiff[j] = os.path.join(writefile_dir, f'Combined_phase_diff_{j+1}{extension}')
        fnCombMagDiff[j] = os.path.join(writefile_dir, f'Combined_mag_diff_{j+1}{extension}')
        fnWMeanPI[j] = os.path.join(writefile_dir, f'weighted_mean_phase_{n}{extension}')

        if n_channels == 1:
            mc_filler = ''
        else:
            mc_filler = '_'

        for m in range(n_channels):
            if n_channels == 1:
                channel_number = ''
            else:
                channel_number = str(m + 1)

            if multi_channel_data == 'yes':
                method = data.get('method', '')
                if method in ['phase-match', 'conj-diff']:
                    fnCurrentFieldmaps[m][j] = os.path.join(writefile_dir, f'Fieldmap_{j+1}{extension}')
                elif method == 'sep-channel':
                    fnCurrentFieldmaps[m][j] = os.path.join(writefile_dir, f'Fieldmap_{j+1}_{channel_key}{channel_number}{extension}')
            else:
                fnCurrentFieldmaps[m][j] = os.path.join(writefile_dir, f'Fieldmap_{n}{extension}')

            if j == 0:
                fnCurrentPhaseOffsets[m] = os.path.join(sep_dir, f'Phase-offset_{channel_key}{channel_number}{extension}')

            fnCurrentMagImages[m][j] = os.path.join(sep_dir, f'Image_mag_{channel_key}{channel_number}{mc_filler}echo_{n}{extension}')
            fnRawPhaseImages[m][j] = os.path.join(sep_dir, f'Image_phase_{channel_key}{channel_number}{mc_filler}echo_{n}{extension}')
            fnCurrentPhaseImages[m][j] = os.path.join(sep_dir, f'Image_phase_{channel_key}{channel_number}{mc_filler}echo_{n}{extension}')
            fnCurrentPhaseImagesPC[m][j] = os.path.join(sep_dir, f'Image_phase_{channel_key}{channel_number}{mc_filler}echo_{n}_pc{extension}')
            fnBetMaskSep[m][j] = os.path.join(sep_dir, f'Mask_{channel_key}{channel_number}{mc_filler}echo_{n}_pc{extension}')

    for j in range(n_echoes_to_use):
        fnMedianFM[j] = os.path.join(writefile_dir, f'median_fieldmap_{j+1}{extension}')
        fnWMedianFM[j] = os.path.join(writefile_dir, f'weighted_median_fieldmap_{j+1}{extension}')
        fnMedianFiltMedianFM[j] = os.path.join(writefile_dir, f'median_filtered_median_fieldmap_{j+1}{extension}')
        fnMeanFM[j] = os.path.join(writefile_dir, f'mean_fieldmap_{j+1}{extension}')
        fnWMeanFM[j] = os.path.join(writefile_dir, f'weighted_mean_fieldmap_{j+1}{extension}')
        fnTWMeanFM[j] = os.path.join(writefile_dir, f'trimmed_weighted_mean_fieldmap_{j+1}{extension}')
        fnStdFM[j] = os.path.join(writefile_dir, f'std_map_{j+1}{extension}')
        fnCVMap[j] = os.path.join(writefile_dir, f'cv_map_{j+1}{extension}')
        fnNCMap[j] = os.path.join(writefile_dir, f'nc_map_{j+1}{extension}')
        fnNzMap[j] = os.path.join(writefile_dir, f'Nz_map_{j+1}{extension}')

    if multi_channel_data == 'yes':
        fnReconMag = os.path.join(sep_dir, 'reconstructed_Image.nii')
    else:
        fnReconMag = fnCurrentMagImages[0][0]

    fnAllMags = os.path.join(sep_dir, 'all_magnitude_images.nii')

    fnBetImSmall = fnReconMag.replace(extension, f'_bet-small{extension}')
    fnBetImLarge = fnReconMag.replace(extension, f'_bet-large{extension}')

    is_pc = (sys.platform == 'win32')
    if is_pc:
        fnBetMaskSmall = fnReconMag.replace(extension, f'_bet-small.nii_mask{extension}')
        fnBetMaskLarge = fnReconMag.replace(extension, f'_bet-large.nii_mask{extension}')
    else:
        fnBetMaskSmall = fnReconMag.replace(extension, f'_bet-small_mask{extension}')
        fnBetMaskLarge = fnReconMag.replace(extension, f'_bet-large_mask{extension}')

    data['fnReconMag'] = fnReconMag
    data['fnAllMags'] = fnAllMags
    data['fnMeanFM'] = fnMeanFM
    data['fnWMeanFM'] = fnWMeanFM
    data['fnTWMeanFM'] = fnTWMeanFM
    data['fnMedianFM'] = fnMedianFM
    data['fnWMedianFM'] = fnWMedianFM
    data['fnMedianFiltMedianFM'] = fnMedianFiltMedianFM
    data['fnStdFM'] = fnStdFM
    data['fnCVMap'] = fnCVMap
    data['fnNCMap'] = fnNCMap
    data['fnNzMap'] = fnNzMap
    data['fnBetImSmall'] = fnBetImSmall
    data['fnBetImLarge'] = fnBetImLarge
    data['fnBetMaskSmall'] = fnBetMaskSmall
    data['fnBetMaskLarge'] = fnBetMaskLarge
    data['fnBetMaskSubSmall'] = os.path.join(writefile_dir, 'mask_small.nii')
    data['fnBetMaskSubLarge'] = os.path.join(writefile_dir, 'mask_large.nii')
    data['fnBetMaskSep'] = fnBetMaskSep

    data['fnCurrentFieldmaps'] = fnCurrentFieldmaps
    data['fnCurrentMagImages'] = fnCurrentMagImages
    data['fnRawPhaseImages'] = fnRawPhaseImages
    data['fnCurrentPhaseImages'] = fnCurrentPhaseImages
    data['fnCurrentPhaseImagesPC'] = fnCurrentPhaseImagesPC
    data['fnCurrentPhaseOffsets'] = fnCurrentPhaseOffsets
    data['fnCombPhase'] = fnCombPhase
    data['fnCombMag'] = fnCombMag
    data['fnCombPhaseDiff'] = fnCombPhaseDiff
    data['fnCombMagDiff'] = fnCombMagDiff
    data['fnWMeanPI'] = fnWMeanPI

    return data
