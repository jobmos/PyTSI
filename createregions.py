import cv2 as cv2
from math import cos, sin, sqrt, tan, pi
import numpy as np
import resolution
import settings


def large_circle(regions, labels, outlines):
    """Draw a circle centered in the middle of the image.

    This circle has a radius slightly smaller than that of the mirror.

    Args:
        regions (int): RGB representation of the segmented image
        labels (int): Scalar (1,2,3,4) representation of the segmented image
        outlines (int): RGB array of the segment outlines

    Returns:
        tuple: regions, labels, outlines
    """
    cv2.circle(regions, (int(int(resolution.x / 2)), int(int(resolution.y / 2))), settings.radius_circle, settings.red, -1)
    cv2.circle(labels, (int(int(resolution.x / 2)), int(int(resolution.y / 2))), settings.radius_circle, 1, -1)
    cv2.circle(outlines, (int(int(resolution.x / 2)), int(int(resolution.y / 2))), settings.radius_circle, settings.red,
               settings.outline_thickness)

    return regions, labels, outlines


def draw_horizon_area(azimuth, regions, labels, outlines):
    """Draw polygon which (when combined with other segments) makes up the horizon area

    Args:
        azimuth (float): solar azimuth in degrees from North
        regions (int): RGB representation of the segmented image
        labels (int): Scalar (1,2,3,4) representation of the segmented image
        outlines (int): RGB array of the segment outlines

    Returns:
        tuple: Regions, labels, outlines and angle :math:`\\theta` describing the azimuth measured from the East
    """
    # angle from the east in stead of north
    azimuth_from_east = azimuth - 90
    # distance of the three of the four points from the center
    r = int(resolution.x / 2)
    # angle from degrees to radians
    theta = azimuth_from_east * pi / 180
    # horizon width from degrees to radians
    width = settings.width_horizon_area_degrees * pi / 180
    # four points at vertices of polygon
    p1 = [int(int(resolution.x / 2)), int(int(resolution.y / 2))]
    p2 = [int(int(resolution.x / 2)) + r * cos(theta - width), int(int(resolution.y / 2)) + r * sin(theta - width)]
    p3 = [int(int(resolution.x / 2)) + r * cos(theta), int(int(resolution.y / 2)) + r * sin(theta)]
    p4 = [int(int(resolution.x / 2)) + r * cos(theta + width), int(int(resolution.y / 2)) + r * sin(theta + width)]
    horizon_area = np.array([p1, p2, p3, p4], dtype=int)
    # draw the polygon
    cv2.fillConvexPoly(regions, horizon_area, color=settings.cyan)
    cv2.fillConvexPoly(labels, horizon_area, color=2)
    cv2.fillConvexPoly(outlines, horizon_area, color=settings.black)
    cv2.polylines(outlines, [horizon_area], True, settings.cyan, settings.outline_thickness)

    return regions, labels, outlines, theta


def inner_circle(regions, labels, outlines):
    """Draw the inner circle of the segmented image

    The radius is smaller than the radius used in :meth:`createregions.large_circle`

    Args:
        regions (int): RGB representation of the segmented image
        labels (int): Scalar (1,2,3,4) representation of the segmented image
        outlines (int): RGB array of the segment outlines

    Returns:
        tuple: regions, labels, outlines
    """
    cv2.circle(regions, (int(int(resolution.x / 2)), int(int(resolution.y / 2))), settings.radius_inner_circle, settings.green, -1)
    cv2.circle(labels, (int(int(resolution.x / 2)), int(int(resolution.y / 2))), settings.radius_inner_circle, 3, -1)
    cv2.circle(outlines, (int(int(resolution.x / 2)), int(int(resolution.y / 2))), settings.radius_inner_circle, (0, 0, 0), -1)
    cv2.circle(outlines, (int(int(resolution.x / 2)), int(int(resolution.y / 2))), settings.radius_inner_circle, settings.green,
               settings.outline_thickness)

    return regions, labels, outlines


def sun_circle(altitude, regions, labels, outlines, theta):
    """Draw the sun cirlce segment

    The position of the sun in the image plane is calculated using an approximation of the mirror. The function that is
    used to estimate the mirror geometry is :math:`y = -0.23x+1.25`.

    The radial distance from the center of the image to the center of the sun can subsequently be calculated using
    the quadratic equation (abc formula).

    Using the description of a circle (:meth:`createmask.calculate_band_position`), the solar position is calculated.

    Args:
        altitude (float): altitude of the sun, taken from the properties file
        regions (int): RGB representation of the segmented image
        labels (int): Scalar (1,2,3,4) representation of the segmented image
        outlines (int): RGB array of the segment outlines
        theta (float): azimuth measured from the East

    Returns:
        tuple: regions, labels, outlines
    """
    # altitude from degrees to radians
    altitude_radians = altitude * pi / 180
    a = -0.23
    b = -tan(altitude_radians)
    c = 1.25
    d = b ** 2 - 4 * a * c
    r = settings.radius_mirror * (-b - sqrt(d)) / (2 * a) / 2
    # x and y position of the sun
    x_sun = int(int(resolution.x / 2) + r * cos(theta))
    y_sun = int(int(resolution.y / 2) + r * sin(theta))
    # draw the circle
    cv2.circle(regions, (x_sun, y_sun), settings.radius_sun_circle, settings.yellow, -1)
    cv2.circle(labels, (x_sun, y_sun), settings.radius_sun_circle, 4, -1)
    cv2.circle(outlines, (x_sun, y_sun), settings.radius_sun_circle, (0, 0, 0), -1)
    cv2.circle(outlines, (x_sun, y_sun), settings.radius_sun_circle, settings.yellow, settings.outline_thickness)

    return regions, labels, outlines


def create_stencil(stencil, stencil_labels):
    """Create the stencil which is used to mask the outside of the large circle

    Args:
        stencil (int): empty stencil array in RGB format
        stencil_labels (int): empty stencil array in scalar format

    Returns:
        tuple: stencil in both RGB and scalar format
    """
    cv2.circle(stencil, (int(int(resolution.x / 2)), int(int(resolution.y / 2))), settings.radius_circle, settings.white, -1)
    cv2.circle(stencil_labels, (int(int(resolution.x / 2)), int(int(resolution.y / 2))), settings.radius_circle, 1, -1)

    return stencil, stencil_labels


def outer_circle(regions, labels, outlines, stencil, stencil_labels):
    """Mask the outside of the large circle

    Args:
        regions (int): RGB representation of the segmented image
        labels (int): Scalar (1,2,3,4) representation of the segmented image
        outlines (int): RGB array of the segment outlines
        stencil (int): stencil array in RGB format
        stencil_labels (int): stencil array in scalar format

    Returns:
        tuple: regions, labels, outlines, stencil (RGB), stencil (scalar)
    """
    regions = cv2.bitwise_and(regions, stencil)
    labels = cv2.bitwise_and(labels, labels, mask=stencil_labels)
    outlines = cv2.bitwise_and(outlines, stencil)

    return regions, labels, outlines


def overlay_outlines_on_image(img, outlines, stencil):
    """Overlay outlines on image by converting to BW and performing several other operations

    Args:
        img (int): image in NumPy format
        outlines (int): RGB array of the segment outlines
        stencil (int): stencil array in RGB format

    Returns:
        int: image with outlines as overlay
    """
    # create mask of outlines and create inverse mask
    img2gray = cv2.cvtColor(outlines, cv2.COLOR_BGR2GRAY)
    ret, mask = cv2.threshold(img2gray, 10, settings.max_color_value-1, cv2.THRESH_BINARY)
    mask_inv = cv2.bitwise_not(mask)

    # black out area of outlines
    img_bg = cv2.bitwise_and(img[0:resolution.y, 0:resolution.x], img[0:resolution.y, 0:resolution.x], mask=mask_inv)

    # take only region of outlines from outlines image
    outlines_fg = cv2.bitwise_and(outlines, outlines, mask=mask)

    dst = cv2.add(img_bg, outlines_fg)

    image_with_outlines = cv2.bitwise_and(dst, stencil)

    return image_with_outlines



def draw_arm(regions, labels, image_with_outlines):
    """Draw the camera arm mask

    Args:
        regions (int): RGB representation of the segmented image
        labels (int): Scalar (1,2,3,4) representation of the segmented image
        image_with_outlines (int): image with outlines as overlay

    Returns:
        tuple: regions, labels, image_with_outlines
    """
    cv2.rectangle(regions, (141, 190), (154, 153), settings.black, -1)
    cv2.rectangle(regions, (145, 154), (152, 91), settings.black, -1)
    cv2.rectangle(regions, (int(resolution.x / 2), 91), (152, 26), settings.black, -1)
    cv2.rectangle(labels, (141, 190), (154, 153), 0, -1)
    cv2.rectangle(labels, (145, 154), (152, 91), 0, -1)
    cv2.rectangle(labels, (int(resolution.x / 2), 91), (152, 26), 0, -1)
    cv2.rectangle(image_with_outlines, (141, 190), (154, 153), settings.black, -1)
    cv2.rectangle(image_with_outlines, (145, 154), (152, 91), settings.black, -1)
    cv2.rectangle(image_with_outlines, (int(resolution.x / 2), 91), (152, 26), settings.black, -1)

    return regions, labels, image_with_outlines


def draw_band(regions, labels, image_with_outlines, theta):
    """Draw the shadow band mask

    Args:
        regions (int): RGB representation of the segmented image
        labels (int): Scalar (1,2,3,4) representation of the segmented image
        image_with_outlines (int): image with outlines as overlay
        theta (float): azimuth measured from the East

    Returns:
        regions, labels, image_with_outlines
    """
    x_inner = int(resolution.x / 2 + settings.r_inner * cos(theta))
    y_inner = int(resolution.y / 2 + settings.r_inner * sin(theta))
    x_outer = int(resolution.x / 2 + settings.r_outer * cos(theta))
    y_outer = int(resolution.y / 2 + settings.r_outer * sin(theta))
    cv2.line(regions, (x_inner, y_inner), (x_outer, y_outer), settings.black, settings.band_thickness)
    cv2.line(labels, (x_inner, y_inner), (x_outer, y_outer), 0, settings.band_thickness)
    cv2.line(image_with_outlines, (x_inner, y_inner), (x_outer, y_outer), 0, settings.band_thickness)

    return regions, labels, image_with_outlines


def create(img, azimuth, altitude):
    """Create the empty arrays and call drawing and masking functions

    Args:
        img (int): image in NumPy format
        azimuth (float): azimuth of the sun, taken from the properties file
        altitude (float): altitude of the sun, taken from the properties file

    Returns:
        tuple: regions, outlines, labels, stencil, image_with_outlines
    """
    # variable assignment
    labels = np.zeros((resolution.y, resolution.x))
    regions = np.zeros((resolution.y, resolution.x, resolution.nColors), dtype="uint8")
    outlines = np.zeros((resolution.y, resolution.x, resolution.nColors), dtype="uint8")
    stencil = np.zeros(regions.shape, dtype="uint8")
    stencil_labels = np.zeros(labels.shape, dtype="uint8")
    # convert from BGR -> RGB
    # conversion needs to be centralized in one place.
    img = img[..., ::-1]

    # drawing the shapes on arrays
    regions, labels, outlines = large_circle(regions, labels, outlines)
    regions, labels, outlines, theta = draw_horizon_area(azimuth, regions, labels, outlines)
    regions, labels, outlines = inner_circle(regions, labels, outlines)
    regions, labels, outlines = sun_circle(altitude, regions, labels, outlines, theta)
    stencil, stencil_labels = create_stencil(stencil, stencil_labels)
    regions, labels, outlines = outer_circle(regions, labels, outlines, stencil, stencil_labels)
    image_with_outlines = overlay_outlines_on_image(img, outlines, stencil)
    regions, labels, image_with_outlines = draw_arm(regions, labels, image_with_outlines)
    regions, labels, image_with_outlines = draw_band(regions, labels, image_with_outlines, theta)

    return regions, outlines, labels, stencil, image_with_outlines
