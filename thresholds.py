# DESCRIPTION: sets the fixed thresholds
import numpy as np
import settings
import sys
from math import log10
import resolution


def fixed():
    """Get the fixed thresholds from the settings file

    Returns:
        tuple: the fixed thresholds
    """
    # TODO: this might be unnecessary
    fixed_sunny_threshold = settings.fixed_sunny_threshold
    fixed_thin_threshold = settings.fixed_thin_threshold

    return fixed_sunny_threshold, fixed_thin_threshold


def min_cross_entropy(data, nbins):
    """Minimum cross entropy algorithm to determine the minimum of a histogram

    Args:
        data (foat): the image data (e.g. blue/red ratio) to be used in the histogram
        nbins (int): number of histogram bins

    Returns:
        float: the MCE threshold
    """
    # create the histogram and determine length
    hist, bins = np.histogram(data, nbins)
    L = len(hist)

    thresholdList = []

    # catch zeros which cause error if not changed to one
    if hist[1] == 0:
        hist[1] = 1
    if hist[L - 2] == 0:
        hist[L - 2] = 1

    for iThreshold in range(2, L):
        m1 = 0
        m2 = 0
        mu1 = 0
        mu2 = 0

        for i in range(1, iThreshold):
            m1 += i * hist[i]
            mu1 += hist[i]

        for i in range(iThreshold, L):
            m2 += i * hist[i]
            mu2 += hist[i]

        mu1 = m1 / mu1
        mu2 = m2 / mu2

        thresholdList.append(-m1 * log10(mu1) - m2 * log10(mu2))

    # minimum of the list is the threshold
    threshold = bins[np.argmin(thresholdList)]

    # catch miscalculation
    if threshold <= 0:
        print('histogram data:', hist)
        print('ERROR threshold (', threshold, ') smaller or equal to 0')

    return threshold


def flatten_clean_array(img):
    """Convert 2D masked image to 1D flattened array to be used in MCE algorithm

    Args:
        img (int): masked image

    Returns:
        float: normalized, 1D, flattened masked red/blue ratio array
    """
    # TODO: clean up, can replace ratioBR with masked numpy arrays
    ratioBR = np.zeros([resolution.y, resolution.x], dtype=float)

    # extract blue and red bands
    B = np.zeros((resolution.x, resolution.y), dtype=int)
    R = np.zeros((resolution.x, resolution.y), dtype=int)
    B = img[:, :, 0].astype(int)
    R = img[:, :, 2].astype(int)

    # calculate the blue/red ratio
    for i in range(0, resolution.y):
        for j in range(0, resolution.x):
            if R[i, j] != 0 and B[i, j] != 0:
                ratioBR[i, j] = B[i, j] / R[i, j]

    # normalized B/R ratio
    ratioBR_norm = np.zeros(ratioBR.shape, dtype=float)

    # catch Nan
    if np.argwhere(np.isnan(ratioBR_norm)).any() == True:
        sys.exit('NaN found in B/R ratios')

    for i in range(0, resolution.y):
        for j in range(0, resolution.x):
            if ratioBR[i, j] != 0:
                ratioBR_norm[i, j] = (ratioBR[i, j] - 1) / (ratioBR[i, j] + 1)
    # catch Nan
    if np.argwhere(np.isnan(ratioBR_norm)).any() == True:
        sys.exit('NaN found in normalized B/R ratios')

    # convert 2D array to 1D array
    ratioBR_norm_1d = ratioBR_norm.flatten()

    # remove zeros from 1D array
    ratioBR_norm_1d_nz = ratioBR_norm_1d[np.nonzero(ratioBR_norm_1d)]

    return ratioBR_norm_1d_nz


def hybrid(img):
    """Decide between fixed or MCE thresholding as part of hybrid thresholding algorithm

    Args:
        img (int): masked image

    Returns:
        tuple: normalized 1D flattened masked red/blue ratio array, standard deviation of the image and hybrid threshold
    """
    ratioBR_norm_1d_nz = flatten_clean_array(img)

    # calculate standard deviation
    stDev = np.std(ratioBR_norm_1d_nz)

    # decide which thresholding needs to be used
    if stDev <= settings.deviation_threshold:
        # fixed thresholding
        threshold = settings.fixed_threshold
    else:
        # MCE thresholding
        threshold = min_cross_entropy(ratioBR_norm_1d_nz, settings.nbins_hybrid)

    return ratioBR_norm_1d_nz, stDev, threshold
