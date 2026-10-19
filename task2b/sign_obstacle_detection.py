'''
*****************************************************************************************
*
*  ===============================================
*     Niti Vahan (NV) Theme of eYRC 2026-27
*  ===============================================
*
*  This script is intended for implementation of Task 2B of Niti Vahan (NV) Theme.
*
*  Filename:         sign_obstacle_detection.py
*  Created:          2026
*  Last Modified:
*  Author:           e-Yantra Team
*
*  You are ONLY allowed to write your code inside the block marked
*  "ADD YOUR IMPLEMENTATION HERE". Do not change anything outside it - the
*  evaluation script relies on the rest of this file staying as it is.
*
*****************************************************************************************
'''

# Team ID:          < Team-ID >
# Author List:      < Names of the team members who worked on this file, comma separated >
# Filename:         sign_obstacle_detection.py
# Functions:        detect_signs, detect_obstacle
# Global variables: < List any global variables you add, "None" if you add none >


####################### IMPORT MODULES #######################
import cv2
import numpy as np
##############################################################

# The only sign labels detect_signs() is allowed to return.
SIGN_LABELS = ("School", "Speed40", "Parking", "Hospital")


##############################################################
############### ADD YOUR IMPLEMENTATION HERE #################
##############################################################

def detect_signs(image):
    '''
    Purpose:
    ---
    Detect every road sign visible in a single image, and report what each
    one is and how large it appears. An image can hold zero, one, or more
    than one sign at once.

    Input Arguments:
    ---
    `image` :   [ numpy.ndarray ]
        A single BGR image, of shape (height, width, 3).

    Returns:
    ---
    `detections` :  [ list of dict ]
        Zero, one, or many entries - one per sign found in the image:
        [
            {
                "label" : str,   one of SIGN_LABELS
                "area"  : int,   that sign's area in pixels
            },
            ...
        ]

    Example call:
    ---
    detections = detect_signs(image)

    NOTE:
    ---
    This function must ONLY compute and return the result. Do not call
    cv2.imshow(), cv2.waitKey(), cv2.imwrite() or print() from inside it -
    reading images and reporting results is the evaluator's job, not this
    function's.
    '''

    detections = []

    for component in _colour_components(image, "red"):
        contour = component["contour"]
        area = component["area"]
        if area < 650:
            continue

        solidity = component["solidity"]
        white_ratio = _white_ratio_inside(image, contour)
        if solidity < 0.88 or white_ratio < 0.10:
            continue

        perimeter = cv2.arcLength(contour, True)
        polygon = cv2.approxPolyDP(contour, 0.04 * perimeter, True)
        label = "School" if len(polygon) == 3 else "Speed40"
        detections.append({"label": label, "area": int(round(area))})

    for component in _colour_components(image, "blue"):
        x, y, width, height = component["bbox"]
        if component["pixel_area"] < 500:
            continue
        if y < 5 or y >= image.shape[0] * 0.75:
            continue
        ratio = width / float(height or 1)
        if ratio < 0.80 or ratio > 1.35:
            continue

        symbol = _rectified_white_mask(image, component["mask"])
        parking_score = _template_score(symbol, _PARKING_TEMPLATE)
        hospital_score = _template_score(symbol, _HOSPITAL_TEMPLATE)
        if parking_score < 0.045 and hospital_score < 0.075:
            continue

        label = "Parking" if parking_score >= hospital_score else "Hospital"
        detections.append({"label": label, "area": int(round(component["area"]))})

    detections.sort(key=lambda item: (item["label"], item["area"]))
    return detections


def detect_obstacle(image):
    '''
    Purpose:
    ---
    Detect whether the obstacle is visible in a single image, and how large
    it appears.

    Input Arguments:
    ---
    `image` :   [ numpy.ndarray ]
        A single BGR image, of shape (height, width, 3).

    Returns:
    ---
    `result` :  [ dict ]
        {
            "present" : bool,   True if the obstacle is visible
            "area"    : int,    its area in pixels, 0 if not present
        }

    Example call:
    ---
    result = detect_obstacle(image)

    NOTE:
    ---
    This function must ONLY compute and return the result. Do not call
    cv2.imshow(), cv2.waitKey(), cv2.imwrite() or print() from inside it -
    reading images and reporting results is the evaluator's job, not this
    function's.
    '''

    candidates = []
    for component in _colour_components(image, "red"):
        if component["area"] < 700:
            continue
        if component["solidity"] < 0.85:
            continue
        if _white_ratio_inside(image, component["contour"]) >= 0.10:
            continue
        candidates.append(component)

    if not candidates:
        return {"present": False, "area": 0}

    obstacle = max(candidates, key=lambda component: component["area"])
    return {"present": True, "area": int(round(obstacle["area"]))}


# ------------------------------------------------------------------
# Add any helper functions and global variables you need below this
# comment, and keep them ABOVE the "END OF YOUR IMPLEMENTATION" line.
# They must be called from detect_signs() or detect_obstacle() - the
# evaluation script only ever calls those two functions. List them in
# the file header too.
# ------------------------------------------------------------------


def _colour_components(image, colour):
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    if colour == "red":
        mask = cv2.inRange(hsv, (0, 80, 50), (14, 255, 255))
        mask |= cv2.inRange(hsv, (166, 80, 50), (179, 255, 255))
    else:
        mask = cv2.inRange(hsv, (85, 60, 30), (145, 255, 255))

    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    components = []
    for label in range(1, count):
        x, y, width, height, pixel_area = [int(value) for value in stats[label]]
        if pixel_area == 0:
            continue

        component_mask = np.where(labels == label, 255, 0).astype(np.uint8)
        contours, _ = cv2.findContours(
            component_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        if not contours:
            continue
        contour = max(contours, key=cv2.contourArea)
        area = float(cv2.contourArea(contour))
        hull_area = float(cv2.contourArea(cv2.convexHull(contour)))
        components.append({
            "bbox": (x, y, width, height),
            "mask": component_mask,
            "pixel_area": pixel_area,
            "contour": contour,
            "area": area,
            "solidity": area / hull_area if hull_area else 0.0,
        })
    return components


def _white_ratio_inside(image, contour):
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    inside = np.zeros(image.shape[:2], dtype=np.uint8)
    cv2.drawContours(inside, [contour], -1, 255, -1)
    white = cv2.inRange(hsv, (0, 0, 150), (179, 105, 255))
    area = cv2.contourArea(contour)
    if area <= 0:
        return 0.0
    return cv2.countNonZero(cv2.bitwise_and(white, inside)) / area


def _ordered_box(points):
    points = np.asarray(points, dtype=np.float32)
    sums = points.sum(axis=1)
    differences = np.diff(points, axis=1).ravel()
    return np.array([
        points[np.argmin(sums)],
        points[np.argmin(differences)],
        points[np.argmax(sums)],
        points[np.argmax(differences)],
    ], dtype=np.float32)


def _rectified_white_mask(image, component_mask):
    contours, _ = cv2.findContours(
        component_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    if not contours:
        return np.zeros((64, 64), dtype=np.uint8)

    contour = max(contours, key=cv2.contourArea)
    rectangle = _ordered_box(cv2.boxPoints(cv2.minAreaRect(contour)))
    destination = np.array(
        [[0, 0], [63, 0], [63, 63], [0, 63]], dtype=np.float32
    )
    transform = cv2.getPerspectiveTransform(rectangle, destination)
    warped = cv2.warpPerspective(image, transform, (64, 64))
    hsv = cv2.cvtColor(warped, cv2.COLOR_BGR2HSV)
    return cv2.inRange(hsv, (0, 0, 130), (179, 105, 255))


def _template_score(symbol, template):
    symbol = cv2.resize(symbol, (64, 64), interpolation=cv2.INTER_AREA)
    symbol = symbol.astype(np.float32) / 255.0
    template = template.astype(np.float32) / 255.0
    if float(symbol.std()) < 1e-6:
        return 0.0
    return float(cv2.matchTemplate(symbol, template, cv2.TM_CCOEFF_NORMED)[0, 0])


def _load_symbol_template(filename, fallback):
    try:
        import os
        path = os.path.join(os.path.dirname(__file__), "reference_images", filename)
        reference = cv2.imread(path)
        if reference is not None:
            hsv = cv2.cvtColor(reference, cv2.COLOR_BGR2HSV)
            blue = cv2.inRange(hsv, (85, 60, 30), (145, 255, 255))
            count, labels, stats, _ = cv2.connectedComponentsWithStats(blue, 8)
            if count > 1:
                label = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
                component = np.where(labels == label, 255, 0).astype(np.uint8)
                return _rectified_white_mask(reference, component)
    except Exception:
        pass
    return cv2.resize(np.asarray(fallback, dtype=np.uint8), (64, 64), interpolation=cv2.INTER_NEAREST)


_PARKING_TEMPLATE = _load_symbol_template("P.jpg", [
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 1, 1, 1, 1, 0, 0],
    [0, 0, 1, 0, 0, 1, 0, 0],
    [0, 0, 1, 0, 0, 1, 0, 0],
    [0, 0, 1, 1, 1, 0, 0, 0],
    [0, 0, 1, 0, 0, 0, 0, 0],
    [0, 0, 1, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
])

_HOSPITAL_TEMPLATE = _load_symbol_template("Hospital.png", [
    [0, 0, 1, 0, 0, 1, 0, 0],
    [0, 0, 1, 0, 0, 1, 0, 0],
    [0, 0, 1, 0, 0, 1, 0, 0],
    [0, 0, 1, 1, 1, 1, 0, 0],
    [0, 0, 1, 0, 0, 1, 0, 0],
    [0, 0, 1, 0, 0, 1, 0, 0],
    [0, 0, 1, 0, 0, 1, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
])


##############################################################
################ END OF YOUR IMPLEMENTATION ##################
##############################################################


#################### DO NOT EDIT BELOW THIS LINE ####################

def validate_signs(detections, image_name):
    '''
    Purpose:
    ---
    Check that detect_signs() returned the expected structure and normalise
    it, so a malformed return is reported here instead of silently scoring
    zero during evaluation.

    Input Arguments:
    ---
    `detections` :  [ object ]     whatever detect_signs() returned
    `image_name` :  [ str ]        name of the image, used in error messages

    Returns:
    ---
    `clean` :       [ list of dict ]   [{"label": str, "area": int}, ...]
    '''
    where = "detect_signs() on {}".format(image_name)

    if not isinstance(detections, list):
        raise TypeError("{} must return a list, got {}".format(where, type(detections).__name__))

    clean = []
    for index, entry in enumerate(detections):
        entry_where = "{}, entry {}".format(where, index)

        if not isinstance(entry, dict):
            raise TypeError("{} must be a dict, got {}".format(entry_where, type(entry).__name__))

        missing = {"label", "area"} - set(entry.keys())
        if missing:
            raise ValueError("{} is missing the key(s): {}".format(entry_where, ", ".join(sorted(missing))))

        label = entry["label"]
        if label not in SIGN_LABELS:
            raise ValueError("{} returned label = '{}', expected one of {}".format(
                entry_where, label, ", ".join(SIGN_LABELS)))

        area = _validate_area(entry["area"], entry_where)
        clean.append({"label": label, "area": area})

    return clean


def validate_obstacle(result, image_name):
    '''
    Purpose:
    ---
    Check that detect_obstacle() returned the expected structure and
    normalise it.

    Input Arguments:
    ---
    `result` :      [ object ]     whatever detect_obstacle() returned
    `image_name` :  [ str ]        name of the image, used in error messages

    Returns:
    ---
    `clean` :       [ dict ]       {"present": bool, "area": int}
    '''
    where = "detect_obstacle() on {}".format(image_name)

    if not isinstance(result, dict):
        raise TypeError("{} must return a dict, got {}".format(where, type(result).__name__))

    missing = {"present", "area"} - set(result.keys())
    if missing:
        raise ValueError("{} is missing the key(s): {}".format(where, ", ".join(sorted(missing))))

    present = result["present"]
    if not isinstance(present, (bool, np.bool_)):
        raise TypeError("{} returned present of type {}, expected a bool".format(
            where, type(present).__name__))
    present = bool(present)

    area = _validate_area(result["area"], where)
    if not present and area != 0:
        raise ValueError("{} returned present=False but area={}, expected 0".format(where, area))

    return {"present": present, "area": area}


def _validate_area(area, where):
    if isinstance(area, bool) or not isinstance(area, (int, float, np.integer, np.floating)):
        raise TypeError("{} returned area of type {}, expected a number".format(
            where, type(area).__name__))
    area = int(round(float(area)))
    if area < 0:
        raise ValueError("{} returned a negative area: {}".format(where, area))
    return area
