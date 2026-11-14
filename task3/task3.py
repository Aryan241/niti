'''
*****************************************************************************************
*
*  ===============================================
*     Niti Vahan (NV) Theme of eYRC 2026-27
*  ===============================================
*
*  This script is intended for implementation of Task 3A of Niti Vahan (NV) Theme.
*
*  Filename:         task3.py
*  Created:          2026
*  Author:           Team NV
*
*  Mini theme run: follow the lane, halt at the Hospital pickup point, keep to
*  the Speed 40 zone limit, change lane round obstacles and park at the ArUco
*  bay. Everything the vehicle acts on comes from its camera image.
*
*****************************************************************************************
'''

# Team ID:          < Team-ID >
# Author List:      < Names of the team members who worked on this file, comma separated >
# Filename:         task3.py
# Functions:        detect_lane, detect_signs, detect_obstacles, estimate_sign_range,
#                   lane_control, parking_manoeuvre, Mission.step, main
# Global variables: None (all run state lives in the Mission and PoseEstimator objects)


####################### IMPORT MODULES #######################
import os
import sys
import time

import cv2
import numpy as np

from coppeliasim_zmqremoteapi_client import RemoteAPIClient
##############################################################


##################### SCENE CONSTANTS ########################
VISION_SENSOR = '/Niti_Vahan/Camera_joint/Cuboid/visionSensor'
STEER_LEFT    = '/steeringLeft'
STEER_RIGHT   = '/steeringRight'
MOTOR_LEFT    = '/motorLeft'
MOTOR_RIGHT   = '/motorRight'

# Vehicle geometry (Task 1A / 2C)
WHEELBASE     = 0.120
TRACK_WIDTH   = 0.110
WHEEL_OFFSET  = 0.0275
WHEEL_RADIUS  = 0.0213               # m, measured: 3.0 rad/s drives 6.4 cm/s

# Camera (same sensor as 2A/2C): 640 x 480, 95 deg horizontal FOV, 30 deg down
IMG_W, IMG_H  = 640, 480
CAMERA_FOV_X  = np.deg2rad(95.0)
FOCAL_PX      = (IMG_W / 2) / np.tan(CAMERA_FOV_X / 2)
CAMERA_MATRIX = np.array([[FOCAL_PX, 0, IMG_W / 2],
                          [0, FOCAL_PX, IMG_H / 2],
                          [0, 0, 1]])
CAM_PITCH     = np.deg2rad(30.0)
CAM_AHEAD     = 0.047                # camera ahead of the vehicle centre, m

# ArUco bay (2C geometry)
ARUCO_DICT         = cv2.aruco.DICT_4X4_50
PARK_MARKER_ID     = 1
BAY_MIDDLE_FORWARD = 0.20            # m from the marker line to the parking spot centre
BAY_WIDTH          = 0.22
CAM_ABOVE_MK       = 0.176 - 0.085   # camera height minus marker-centre height, m
MARKER_SIDE        = 0.0556          # black pattern of the 0.08 m board (calibrated)
_HM = MARKER_SIDE / 2
MARKER_CORNERS_3D = np.array([[-_HM, _HM, 0], [_HM, _HM, 0],
                              [_HM, -_HM, 0], [-_HM, -_HM, 0]], np.float32)
##############################################################


######################## RUN SETTINGS ########################
SPEED_LIMIT   = 3.0                  # rad/s everywhere
ZONE_LIMIT    = 1.2                  # rad/s between the two Speed 40 signs
CRUISE        = SPEED_LIMIT          # use the permitted global cap outside the zone
ZONE_CRUISE   = 1.20                 # exact task cap while the Speed 40 zone is active
ZONE_NEAR_RANGE  = 0.65           # m, evidence that the current sign was approached

HALT_SECONDS      = 5.0              # required stationary time (simulation time)
HALT_MARGIN       = 0.25             # verified stationary interval supports 5.25 s total
HOSPITAL_STOP_RANGE = 0.565          # m, sign ahead of the vehicle centre at the pickup point
HALT_COAST          = 0.013          # m rolled after the stop command takes effect
HALT_LAG_FRAMES     = 1.5            # frames of travel between capture and the stop command
HALT_APPROACH_SPEED = 1.5            # rad/s for the last ~12 cm before the pickup point
HOSPITAL_ARM_RANGE  = 0.75           # sign must first be seen further away than this

OBSTACLE_TRIGGER_ROW = 0.40          # obstacle base this far down the image -> change lane
OBSTACLE_LATEST_ROW  = 0.72          # lower than this it is beside us, not ahead
LANE_CHANGE_COOLDOWN = 10.0          # s of sim time before another lane change is allowed

PARK_START_FORWARD = 0.95            # m, hand over to parking once the marker is this close
LANE_CHANGE_SPEED  = 2.9             # speed cap while changing lane
PARK_INNER_LATERAL = 0.32            # m, hand-over gate from the inner lane (on the straight ~0.21)
PARK_MAX_LATERAL   = 0.48            # m, ...and from the outer lane (~0.41)

MAX_TRAVEL_PER_FRAME = 0.025        # m driven between processed frames, at most

VERBOSE = bool(os.environ.get('NV_VERBOSE'))
##############################################################


# ============================================================
#                       LANE PERCEPTION
# ============================================================
# Lane side naming (as in 2A): "right" = the solid yellow edge is to the RIGHT
# of the dashed divider, "left" = it is to the LEFT. Driving clockwise, the
# inner lane is "right" and the outer lane is "left".

# Lane width in pixels grows linearly with image row on a flat road:
# width(row) = LANE_W_SLOPE * (row - LANE_W_HORIZON)
LANE_W_SLOPE   = 1.39
LANE_W_HORIZON = 70.0


def _lane_half_width(row):
    return 0.5 * LANE_W_SLOPE * max(float(row) - LANE_W_HORIZON, 1.0)


def _lane_masks(hsv):
    yellow = cv2.inRange(hsv, (18, 105, 105), (43, 255, 255))
    white = cv2.inRange(hsv, (0, 0, 165), (179, 105, 255))
    kernel = np.ones((3, 3), np.uint8)
    yellow = cv2.morphologyEx(yellow, cv2.MORPH_CLOSE, kernel)
    white = cv2.morphologyEx(white, cv2.MORPH_OPEN, kernel)
    return yellow, white


def _fit_point_model(points, height):
    points = np.asarray(points, dtype=np.float32)
    degree = min(2, len(points) - 1)
    yn = (points[:, 0] - height * 0.70) / max(height * 0.25, 1.0)
    coefficients = np.polyfit(yn, points[:, 1], degree)
    return {"coefficients": coefficients,
            "rows": (float(points[:, 0].min()), float(points[:, 0].max()))}


def _model_x(model, row, height):
    yn = (float(row) - height * 0.70) / max(height * 0.25, 1.0)
    return float(np.polyval(model["coefficients"], yn))


def _solid_line_models(mask, y_min, y_max, min_area, min_height):
    work = mask.copy()
    work[:y_min] = 0
    work[y_max:] = 0
    count, labels, stats, _ = cv2.connectedComponentsWithStats(work, 8)
    models = []
    for index in range(1, count):
        x, y, width, height, area = stats[index]
        if area < min_area or height < min_height:
            continue
        ys, xs = np.where(labels[y:y + height, x:x + width] == index)
        if len(xs) < 20:
            continue
        points = np.column_stack((ys + y, xs + x)).astype(np.float32)
        if len(points) > 600:
            points = points[::len(points) // 600 + 1]
        models.append(_fit_point_model(points, mask.shape[0]))
    return models


def _dashed_line_points(mask, height, width, top=0.50, bottom=0.87):
    work = mask.copy()
    work[:int(height * top)] = 0
    work[int(height * bottom):] = 0
    count, _, stats, centroids = cv2.connectedComponentsWithStats(work, 8)
    points = []
    for index in range(1, count):
        x, y, component_width, component_height, area = stats[index]
        if area < 12 or component_height < 3 or component_width < 2:
            continue
        if component_width > width * 0.35 or area > 6000:
            continue
        if y + component_height < height * 0.62 and area < 12:
            continue
        cx, cy = centroids[index]
        points.append((float(cy), float(cx), float(area)))
    return points


def _dashed_line_models(points, height, width):
    if len(points) < 2:
        return []
    all_points = np.asarray(points, dtype=np.float32)[:, :2]
    models = [_fit_point_model(all_points, height)]
    left = all_points[all_points[:, 1] < width * 0.54]
    right = all_points[all_points[:, 1] > width * 0.46]
    if len(left) >= 2:
        models.append(_fit_point_model(left, height))
    if len(right) >= 2:
        models.append(_fit_point_model(right, height))
    return models


def detect_lane(yellow, white, want_side=None, previous_centre=None):
    '''
    Purpose:
    ---
    Find the lane to follow in one frame. This is the Task 2A detector with a
    lane preference added: `want_side` picks the lane (yellow edge "left" or
    "right" of the dashed divider) so a lane change is just a change of the
    preferred side.

    Returns:
    ---
    dict with "valid", "side", "center_near", "center_far" (pixels) and the
    divider/edge models used, so obstacles can be placed in a lane.
    '''
    height, width = yellow.shape[:2]
    reference = height * 0.78
    yellow_models = _solid_line_models(yellow, int(height * 0.42), int(height * 0.90), 120, 24)
    white_points = _dashed_line_points(white, height, width)
    white_models = _dashed_line_models(white_points, height, width)
    result = {"valid": False, "side": want_side, "center_near": width * 0.5,
              "center_far": width * 0.5, "divider": None, "edge": None,
              "yellow_models": yellow_models}

    candidates = []
    for yellow_model in yellow_models:
        for white_model in white_models:
            outer = _model_x(yellow_model, reference, height)
            divider = _model_x(white_model, reference, height)
            if not (np.isfinite(outer) and np.isfinite(divider)):
                continue
            width_px = abs(divider - outer)
            expected = 2.0 * _lane_half_width(reference)
            if not (0.55 * expected <= width_px <= 1.6 * expected):
                continue
            side = "left" if outer < divider else "right"
            centre = 0.5 * (divider + outer)
            if previous_centre is not None:
                continuity = abs(centre - previous_centre) / width
            else:
                continuity = abs(centre - width * 0.5) / width
            score = continuity + 0.5 * abs(width_px - expected) / width
            if want_side is not None and side != want_side:
                score += 10.0
            candidates.append((score, yellow_model, white_model, side))

    rows = (height * 0.62, height * 0.74, height * 0.84)
    centres = None
    if candidates:
        candidates.sort(key=lambda item: item[0])
        score, edge_model, divider_model, side = candidates[0]
        if want_side is None or side == want_side:
            centres = [(row, 0.5 * (_model_x(edge_model, row, height) +
                                    _model_x(divider_model, row, height)))
                       for row in rows]
            result.update(side=side, divider=divider_model, edge=edge_model)

    if centres is None and white_models and want_side is not None:
        # Edge line not in view (mid lane change, or a bend): offset from the divider.
        divider_model = white_models[0]
        sign = 1.0 if want_side == "right" else -1.0
        centres = [(row, _model_x(divider_model, row, height) + sign * _lane_half_width(row))
                   for row in rows]
        result.update(divider=divider_model, synthetic=True)

    if centres is None and yellow_models and want_side is not None:
        # Divider not in view: offset from the yellow edge on the expected side.
        sign = -1.0 if want_side == "right" else 1.0
        expected_x = (previous_centre if previous_centre is not None else width * 0.5) \
            - sign * _lane_half_width(reference)
        edge_model = min(yellow_models,
                         key=lambda m: abs(_model_x(m, reference, height) - expected_x))
        centres = [(row, _model_x(edge_model, row, height) + sign * _lane_half_width(row))
                   for row in rows]
        result.update(edge=edge_model, synthetic=True)

    if centres is None:
        return result
    if not all(np.isfinite(value) for _, value in centres):
        return result

    centre_model = _fit_point_model(np.asarray(centres, dtype=np.float32), height)
    near = _model_x(centre_model, height * 0.84, height)
    far = _model_x(centre_model, height * 0.60, height)
    if not (np.isfinite(near) and np.isfinite(far)):
        return result
    result.update(valid=True, center_near=float(near), center_far=float(far))
    if result["side"] is None:
        result["side"] = candidates[0][3] if candidates else None
    return result


# ============================================================
#                 SIGN AND OBSTACLE PERCEPTION (2B)
# ============================================================

# Sign faces are close to pure white; the obstacle's light-pink panels are not.
SIGN_WHITE_LOW = (0, 0, 180)
SIGN_WHITE_HIGH = (179, 50, 255)


def _colour_mask(hsv, colour):
    if colour == "red":
        mask = cv2.inRange(hsv, (0, 80, 50), (14, 255, 255))
        mask |= cv2.inRange(hsv, (166, 80, 50), (179, 255, 255))
        return mask
    return cv2.inRange(hsv, (85, 60, 30), (145, 255, 255))


def _components(mask, min_pixels):
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    components = []
    for label in range(1, count):
        x, y, width, height, pixel_area = [int(value) for value in stats[label]]
        if pixel_area < min_pixels:
            continue
        local = np.where(labels[y:y + height, x:x + width] == label, 255, 0).astype(np.uint8)
        contours, _ = cv2.findContours(local, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            continue
        contour = max(contours, key=cv2.contourArea) + np.array([x, y], dtype=np.int32)
        area = float(cv2.contourArea(contour))
        hull_area = float(cv2.contourArea(cv2.convexHull(contour)))
        components.append({
            "bbox": (x, y, width, height),
            "pixel_area": pixel_area,
            "contour": contour,
            "area": area,
            "solidity": area / hull_area if hull_area else 0.0,
        })
    return components


def _inside_ratio(hsv, contour, bbox, low, high):
    x, y, width, height = bbox
    inside = np.zeros((height, width), dtype=np.uint8)
    cv2.drawContours(inside, [contour - np.array([x, y], dtype=np.int32)], -1, 255, -1)
    selected = cv2.inRange(hsv[y:y + height, x:x + width], low, high)
    area = cv2.countNonZero(inside)
    if area <= 0:
        return 0.0
    return cv2.countNonZero(cv2.bitwise_and(selected, inside)) / float(area)


def _ordered_box(points):
    points = np.asarray(points, dtype=np.float32)
    sums = points.sum(axis=1)
    differences = np.diff(points, axis=1).ravel()
    return np.array([points[np.argmin(sums)], points[np.argmin(differences)],
                     points[np.argmax(sums)], points[np.argmax(differences)]],
                    dtype=np.float32)


def _rectified_white_mask(image, contour):
    hull = cv2.convexHull(contour)
    quad = cv2.approxPolyDP(hull, 0.025 * cv2.arcLength(hull, True), True)
    rectangle = _ordered_box(quad.reshape(4, 2) if len(quad) == 4 else
                             cv2.boxPoints(cv2.minAreaRect(contour)))
    destination = np.array([[0, 0], [63, 0], [63, 63], [0, 63]], dtype=np.float32)
    transform = cv2.getPerspectiveTransform(rectangle, destination)
    warped = cv2.warpPerspective(image, transform, (64, 64))
    hsv = cv2.cvtColor(warped, cv2.COLOR_BGR2HSV)
    return cv2.inRange(hsv, (0, 0, 130), (179, 105, 255))


def _template_score(symbol, template):
    symbol = symbol.astype(np.float32) / 255.0
    template = template.astype(np.float32) / 255.0
    if float(symbol.std()) < 1e-6:
        return 0.0
    return float(cv2.matchTemplate(symbol, template, cv2.TM_CCOEFF_NORMED)[0, 0])


def _symbol_glyph(mask):
    '''Ignore the white sign border; require a substantial interior letter.'''
    interior = mask[8:56, 8:56]
    count, labels, stats, _ = cv2.connectedComponentsWithStats(interior, 8)
    if count < 2:
        return None
    index = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    x, y, width, height, area = stats[index]
    if area < 0.06 * interior.size or width < 0.28 * interior.shape[1] or height < 0.55 * interior.shape[0]:
        return None
    glyph = np.where(labels[y:y + height, x:x + width] == index, 255, 0).astype(np.uint8)
    return cv2.resize(glyph, (32, 40), interpolation=cv2.INTER_AREA)


def _load_symbol_template(filename, fallback):
    try:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "reference_images", filename)
        reference = cv2.imread(path)
        if reference is not None:
            hsv = cv2.cvtColor(reference, cv2.COLOR_BGR2HSV)
            blue = _colour_mask(hsv, "blue")
            parts = _components(blue, 50)
            if parts:
                part = max(parts, key=lambda item: item["area"])
                return _rectified_white_mask(reference, part["contour"])
    except Exception:
        pass
    return cv2.resize(np.asarray(fallback, dtype=np.uint8) * 255, (64, 64),
                      interpolation=cv2.INTER_NEAREST)


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
_PARKING_GLYPH = _symbol_glyph(_PARKING_TEMPLATE)
_HOSPITAL_GLYPH = _symbol_glyph(_HOSPITAL_TEMPLATE)


def detect_signs(image, hsv, red_parts, blue_parts):
    '''
    The 2B sign detector, returning where each sign is in the image as well:
    [{"label", "area", "bbox": (x, y, w, h)}, ...]
    '''
    detections = []
    for component in red_parts:
        area = component["area"]
        if area < 150 or component["solidity"] < 0.88:
            continue
        white_ratio = _inside_ratio(hsv, component["contour"], component["bbox"],
                                    SIGN_WHITE_LOW, SIGN_WHITE_HIGH)
        if white_ratio < 0.10:
            continue
        x, y, width, height = component["bbox"]
        ratio = width / float(height or 1)
        if ratio < 0.45 or ratio > 1.8:
            continue
        perimeter = cv2.arcLength(component["contour"], True)
        polygon = cv2.approxPolyDP(component["contour"], 0.04 * perimeter, True)
        if len(polygon) == 3:
            label = "School"
        else:
            (_, _), radius = cv2.minEnclosingCircle(component["contour"])
            circularity = area / (np.pi * radius * radius + 1e-6)
            dark = _inside_ratio(hsv, component["contour"], component["bbox"],
                                 (0, 0, 0), (179, 255, 90))
            if circularity < 0.55 or dark < 0.01:
                continue
            label = "Speed40"
        detections.append({"label": label, "area": int(round(area)),
                           "bbox": component["bbox"]})

    for component in blue_parts:
        x, y, width, height = component["bbox"]
        if component["pixel_area"] < 120 or component["solidity"] < 0.80:
            continue
        if x <= 0 or x + width >= image.shape[1] or y < 1 or y >= image.shape[0] * 0.75:
            continue
        ratio = width / float(height or 1)
        if ratio < 0.55 or ratio > 1.45:
            continue
        symbol = _rectified_white_mask(image, component["contour"])
        glyph = _symbol_glyph(symbol)
        if glyph is None:
            continue
        # Raw masks preserve small/oblique letters; normalized glyphs also work
        # with the built-in no-reference templates, whose border/font differs.
        parking_score = max(_template_score(symbol, _PARKING_TEMPLATE),
                            _template_score(glyph, _PARKING_GLYPH))
        hospital_score = max(_template_score(symbol, _HOSPITAL_TEMPLATE),
                             _template_score(glyph, _HOSPITAL_GLYPH))
        if max(parking_score, hospital_score) < 0.35 or abs(parking_score - hospital_score) < 0.03:
            continue
        label = "Parking" if parking_score >= hospital_score else "Hospital"
        detections.append({"label": label, "area": int(round(component["area"])),
                           "bbox": component["bbox"]})
    return detections


def _oblique_speed40_candidates(frame):
    """Image-only fragmented-rim recognizer for the small oblique Speed40 face."""
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    red = _colour_mask(hsv, "red")
    blue = _colour_mask(hsv, "blue") > 0
    white = cv2.inRange(hsv, (0, 0, 130), (179, 105, 255)) > 0
    dark = cv2.inRange(hsv, (0, 0, 0), (179, 255, 90)) > 0
    labels = cv2.dilate(red, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (17, 17)))
    count, ids, stats, _ = cv2.connectedComponentsWithStats(labels, 8)
    found = []
    for i in range(1, count):
        x, y, w, h, _ = map(int, stats[i])
        if w < 3 or h < 3 or w > 140 or h > 140:
            continue
        # The component bounds already include the rim's 8-pixel dilation.
        # Keep fragment morphology local; all supported pixels remain inside
        # these bounds, including components clipped by the image border.
        roi = np.s_[y:y+h, x:x+w]
        rim = (ids[roi] == i) & (red[roi] > 0)
        near = cv2.dilate(rim.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (17, 17))) > 0
        local_support = (rim | (near & white[roi]) | (near & dark[roi])) & ~blue[roi]
        yy, xx = np.where(local_support)
        if len(xx) < 12 or int(rim.sum()) < 3:
            continue
        points = np.column_stack((xx+x, yy+y)).astype(np.float32)
        support = np.zeros(red.shape, np.uint8)
        support[roi] = local_support
        rect = cv2.minAreaRect(points)
        box = cv2.boxPoints(rect)
        center = box.mean(axis=0)
        box = box[np.argsort(np.arctan2(box[:, 1]-center[1], box[:, 0]-center[0]))].astype(np.float32)
        dst = np.array([[0, 0], [63, 0], [63, 63], [0, 63]], np.float32)
        patch = cv2.warpPerspective(frame, cv2.getPerspectiveTransform(box, dst), (64, 64), flags=cv2.INTER_NEAREST)
        sm = cv2.warpPerspective(support.astype(np.uint8), cv2.getPerspectiveTransform(box, dst), (64, 64), flags=cv2.INTER_NEAREST) > 0
        ph = cv2.cvtColor(patch, cv2.COLOR_BGR2HSV)
        pb = ((ph[:, :, 0] >= 85) & (ph[:, :, 0] <= 145) & (ph[:, :, 1] >= 60) & (ph[:, :, 2] >= 30))
        pr = (((ph[:, :, 0] <= 14) | (ph[:, :, 0] >= 166)) & (ph[:, :, 1] >= 80) & (ph[:, :, 2] >= 50) & sm & ~pb)
        pw = (ph[:, :, 1] <= 105) & (ph[:, :, 2] >= 130) & sm & ~pb
        pd = (ph[:, :, 2] <= 90) & sm & ~pb & ~pr
        ry, rx = np.where(pr)
        if len(rx) < 5:
            continue
        (cx, cy), (d1, d2), angle = cv2.fitEllipse(np.column_stack((rx, ry)).astype(np.float32).reshape(-1, 1, 2))
        # Keep each fitted radius paired with OpenCV's returned angle basis.
        # Sorting the radii without rotating the basis corrupts ellipse tests.
        a, b = d1/2.0, d2/2.0
        theta = np.deg2rad(angle); dx=rx-cx; dy=ry-cy
        u=dx*np.cos(theta)+dy*np.sin(theta); v=-dx*np.sin(theta)+dy*np.cos(theta)
        radial=np.sqrt((u/max(a, 1e-3))**2+(v/max(b, 1e-3))**2)
        ang=np.sort(np.mod(np.arctan2(v/max(b, 1e-3), u/max(a, 1e-3)), 2*np.pi))
        coverage=1.0-float(np.diff(np.r_[ang, ang[0]+2*np.pi]).max()/(2*np.pi))
        yy0, xx0 = np.indices(pd.shape); du=xx0-cx; dv=yy0-cy
        iu=du*np.cos(theta)+dv*np.sin(theta); iv=-du*np.sin(theta)+dv*np.cos(theta)
        interior=(np.sqrt((iu/max(a, 1e-3))**2+(iv/max(b, 1e-3))**2)<.9)
        white_inside=float(np.mean(interior[pw])) if np.any(pw) else 0.0
        n, _, st, _ = cv2.connectedComponentsWithStats((interior & pd).astype(np.uint8), 8)
        glyph_parts=sum(int(st[j, cv2.CC_STAT_AREA]) >= 3 for j in range(1, n))
        ratio=min(a, b)/max(max(a, b), 1e-3); mad=float(np.median(np.abs(radial-1)))
        interior_white = int(np.count_nonzero(interior & pw))
        interior_dark = int(np.count_nonzero(interior & pd))
        white_fill = interior_white / max(1, interior_white + interior_dark)
        white_support = float(np.count_nonzero(pw)) / max(1, np.count_nonzero(sm))
        if (.28 <= ratio <= .55 and mad <= .10 and white_support >= .25 and
                .70 <= white_fill <= .92 and glyph_parts >= 4 and coverage >= .60):
            bx, by, bw, bh = cv2.boundingRect(points.astype(np.int32))
            found.append({"label": "Speed40", "area": int(len(rx)), "bbox": (bx, by, bw, bh),
                          # Partial rim views support a track, but cannot release
                          # the cap without a stronger current face observation.
                          "strong": white_inside >= .25 and coverage >= .80})
    return found


def _whiteboard_speed_candidates(hsv):
    # Kept as a conservative compatibility shim; callers must provide the image.
    return []


class WeakBoardTracker:
    '''Require two spatially consistent weak board observations in a row.'''

    def __init__(self):
        self.bbox = None
        self.streak = 0

    def reset(self):
        self.bbox = None
        self.streak = 0

    def update(self, candidates):
        if len(candidates) != 1:
            self.reset()
            return []
        candidate = candidates[0]
        x, y, width, height = candidate['bbox']
        if self.bbox is not None:
            px, py, pwidth, pheight = self.bbox
            cx, cy = x + width / 2.0, y + height / 2.0
            pcx, pcy = px + pwidth / 2.0, py + pheight / 2.0
            displacement = np.hypot(cx - pcx, cy - pcy)
            size_ratio = height / float(pheight or 1)
            consistent = (displacement <= max(18.0, 1.5 * max(height, pheight)) and
                          0.5 <= size_ratio <= 2.0)
            if not consistent:
                self.streak = 0
        self.streak += 1
        self.bbox = candidate['bbox']
        return [candidate] if self.streak >= 2 and candidate.get('strong', True) else []


def detect_obstacles(hsv, red_mask):
    '''
    The 2B obstacle detector, returning every candidate with its image box:
    [{"area", "bbox", "base": (x, y)}, ...] - base is the bottom centre.
    '''
    merged = cv2.morphologyEx(red_mask, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    found = []
    for component in _components(merged, 400):
        if component["area"] < 500 or component["solidity"] < 0.80:
            continue
        if _inside_ratio(hsv, component["contour"], component["bbox"],
                         SIGN_WHITE_LOW, SIGN_WHITE_HIGH) >= 0.10:
            continue
        x, y, width, height = component["bbox"]
        if width < 1.2 * height * 0.5:
            continue
        found.append({"area": int(round(component["area"])), "bbox": component["bbox"],
                      "base": (x + 0.5 * width, float(y + height))})
    return found


def estimate_sign_range(bbox):
    '''
    Forward distance (m, from the vehicle centre) and lateral offset (m,
    + = right) of a sign plate, from its box in the image. The plate is a
    small square standing upright; its pixel size gives the range. The two
    constants were fitted against renders at known distances.
    '''
    x, y, width, height = bbox
    size = max(float(width), float(height), 1.0)
    depth = SIGN_PLATE * FOCAL_PX / size
    cx = x + 0.5 * width
    lateral = (cx - IMG_W / 2) / FOCAL_PX * depth
    return depth + SIGN_RANGE_OFFSET, lateral


SIGN_PLATE = 0.0802
SIGN_RANGE_OFFSET = 0.096


def obstacle_in_lane(obstacle, lane, height=IMG_H):
    '''
    True if an obstacle still ahead sits in the lane `lane` is following.
    An obstacle in the next lane is a tall box, so close up its image leans
    over the divider: its centre has to be clearly on our side of the
    divider, not just near it.
    '''
    bx, by = obstacle["base"]
    x, _, width, _ = obstacle["bbox"]
    if (x <= 0 or x + width >= IMG_W) and by > height * OBSTACLE_LATEST_ROW * 0.85:
        return False                       # low and cut off by the frame: alongside us
    side = lane.get("side")
    divider = lane.get("divider")
    row = max(by, height * 0.30)
    half = _lane_half_width(row)
    divider_x = _model_x(divider, row, height) if divider is not None else None
    if divider_x is None or side is None or not (-0.2 * IMG_W < divider_x < 1.2 * IMG_W):
        return abs(bx - IMG_W * 0.5) < IMG_W * 0.18
    if side == "right":
        return divider_x + 0.3 * half < bx < divider_x + 2.2 * half
    return divider_x - 2.2 * half < bx < divider_x - 0.3 * half


# ============================================================
#                       LANE CONTROL (2A)
# ============================================================

def _virtual_steering_limit():
    return float(np.arctan(WHEELBASE / (WHEELBASE + (TRACK_WIDTH - 2 * WHEEL_OFFSET) / 2.0)) - 1e-3)


def ackermann_wheel_angles(delta):
    if abs(delta) < 1e-9:
        return 0.0, 0.0
    l = WHEELBASE
    w = TRACK_WIDTH - 2 * WHEEL_OFFSET
    s, c = np.sin(delta), np.cos(delta)
    left = np.arctan2(2 * l * s, 2 * l * c - w * s)
    right = np.arctan2(2 * l * s, 2 * l * c + w * s)
    return float(left), float(right)


def lane_control(lane, speed_cap, steer_cap=None):
    '''Virtual steering angle (rad, + left) and speed from a lane detection.'''
    limit = _virtual_steering_limit() if steer_cap is None else steer_cap
    scale = float(IMG_W)
    near_error = (lane["center_near"] - IMG_W * 0.5) / scale
    far_error = (lane["center_far"] - IMG_W * 0.5) / scale
    virtual = -2.05 * near_error - 1.35 * (far_error - near_error)
    virtual = float(np.clip(virtual, -limit, limit))
    turn = min(abs(virtual) / _virtual_steering_limit(), 1.0)
    speed = speed_cap * (1.0 - 0.05 * turn) if speed_cap > ZONE_LIMIT else speed_cap
    return virtual, float(min(speed, speed_cap))


# ============================================================
#                       PARKING (2C)
# ============================================================

class PoseEstimator:
    '''Vehicle pose relative to the bay from the ArUco marker (2C).'''

    YAW_NORMAL_TAU = 0.20             # seconds; normal clear-yaw correction time constant
    YAW_GATE = np.deg2rad(15.0)
    AMBIGUITY_RATIO = 1.5
    YAW_RECOVERY_FRAMES = 3
    # Bound frame-to-frame yaw changes by the greatest steering yaw rate the
    # vehicle can command, with a small image/PnP noise allowance.
    YAW_RECOVERY_RATE = ((SPEED_LIMIT - 0.05) * WHEEL_RADIUS *
                         np.tan(_virtual_steering_limit()) / WHEELBASE)
    YAW_RECOVERY_FLOOR = np.deg2rad(2.0)
    YAW_RECOVERY_MAX_GAP = 0.75
    YAW_RECOVERY_BLEND = 0.60

    def __init__(self):
        self.heading = 0.0
        self.rho = None
        self._recovery_yaw = None
        self._recovery_count = 0
        self._last_observation_time = None

    def _reset_yaw_recovery(self):
        self._recovery_yaw = None
        self._recovery_count = 0

    @staticmethod
    def _bearing(corners):
        cx, cy = corners[:, 0].mean(), corners[:, 1].mean()
        xc = (cx - IMG_W / 2) / FOCAL_PX
        yc = (IMG_H / 2 - cy) / FOCAL_PX
        return float(np.arctan2(xc, np.cos(CAM_PITCH) + yc * np.sin(CAM_PITCH)))

    def _pnp(self, corners):
        count, rvecs, tvecs, errs = cv2.solvePnPGeneric(
            MARKER_CORNERS_3D, corners.astype(np.float32), CAMERA_MATRIX,
            np.zeros(5), flags=cv2.SOLVEPNP_IPPE_SQUARE)
        if not count or errs is None:
            return None
        sols = []
        for rv, tv, e in zip(rvecs, tvecs, np.array(errs).flatten()):
            rv, tv = np.asarray(rv), np.asarray(tv).reshape(-1)
            if (rv.size != 3 or tv.size != 3 or not np.isfinite(rv).all() or
                    not np.isfinite(tv).all() or not np.isfinite(e) or e < 0 or
                    tv[2] <= 0 or tv @ tv <= CAM_ABOVE_MK ** 2):
                continue
            R, _ = cv2.Rodrigues(rv)
            fwd = R.T @ np.array([0.0, 0.0, 1.0])
            sols.append((float(e), float(np.arctan2(fwd[0], -fwd[2])), tv))
        if not sols:
            return None
        sols.sort(key=lambda s: s[0])
        t = sols[0][2]
        rho = float(np.sqrt(max(t @ t - CAM_ABOVE_MK ** 2, 1e-6)))
        clear = len(sols) < 2 or sols[1][0] > self.AMBIGUITY_RATIO * max(sols[0][0], 1e-6)
        return (sols[0][1] if clear else None), rho

    def update(self, corners, last_steering, now=None, last_speed=0.0):
        # Keep image-fusion timing separate from motion-prediction timing. The
        # fallback interval preserves the existing blend behavior, but cannot
        # invent travel when this observation has no valid elapsed time.
        blend_dt = 0.15
        prediction_dt = 0.0
        try:
            observation_time = None if now is None else float(now)
        except (TypeError, ValueError, OverflowError):
            observation_time = None
        if now is None:
            self._reset_yaw_recovery()
            self._last_observation_time = None
        elif observation_time is None or not np.isfinite(observation_time):
            self._reset_yaw_recovery()
            self._last_observation_time = None
        elif self._last_observation_time is None:
            self._last_observation_time = observation_time
        else:
            elapsed = observation_time - float(self._last_observation_time)
            self._last_observation_time = observation_time
            if 0.0 < elapsed <= self.YAW_RECOVERY_MAX_GAP:
                blend_dt = elapsed
                prediction_dt = elapsed
            else:
                self._reset_yaw_recovery()

        try:
            bounded_speed = float(last_speed)
        except (TypeError, ValueError, OverflowError):
            bounded_speed = 0.0
        if not np.isfinite(bounded_speed):
            bounded_speed = 0.0
        bounded_speed = float(np.clip(bounded_speed, 0.0, SPEED_LIMIT))
        try:
            bounded_steering = float(last_steering)
        except (TypeError, ValueError, OverflowError):
            bounded_steering = 0.0
        if not np.isfinite(bounded_steering):
            bounded_steering = 0.0
        bounded_steering = float(np.clip(bounded_steering, -_virtual_steering_limit(),
                                         _virtual_steering_limit()))
        if prediction_dt > 0.0:
            distance = bounded_speed * WHEEL_RADIUS * prediction_dt
            self.heading -= (np.tan(bounded_steering) * distance / WHEELBASE)

        if corners is None:
            self._reset_yaw_recovery()
            return None
        try:
            corners = np.asarray(corners, dtype=np.float32)
            if (corners.shape != (4, 2) or not np.isfinite(corners).all() or
                    not np.isfinite(last_steering) or
                    not cv2.isContourConvex(corners) or abs(cv2.contourArea(corners)) < 1.0):
                self._reset_yaw_recovery()
                return None
            solution = self._pnp(corners)
        except (cv2.error, ValueError, TypeError, OverflowError):
            self._reset_yaw_recovery()
            return None
        if solution is None:
            self._reset_yaw_recovery()
            return None
        bearing = self._bearing(corners)
        yaw_seen, rho_now = solution
        if self.rho is None:
            self.rho = rho_now
        self.rho = 0.6 * self.rho + 0.4 * rho_now
        range_filter_lag = max(self.rho - rho_now, 0.0)
        # Filtered range is diagnostic only; yaw prediction integrates the
        # preceding bounded motor/steering command over valid simulation time.
        heading_observed = False
        if yaw_seen is None:
            # IPPE ambiguity is not evidence for either alignment or recovery.
            self._reset_yaw_recovery()
        else:
            yaw_residual = float(np.arctan2(np.sin(yaw_seen - self.heading),
                                            np.cos(yaw_seen - self.heading)))
            if abs(yaw_residual) < self.YAW_GATE:
                self._reset_yaw_recovery()
                normal_blend = 1.0 - np.exp(-blend_dt / self.YAW_NORMAL_TAU)
                self.heading += normal_blend * yaw_residual
                heading_observed = True
            else:
                if self._recovery_yaw is None:
                    self._recovery_yaw, self._recovery_count = yaw_seen, 1
                else:
                    yaw_step = abs(float(np.arctan2(
                        np.sin(yaw_seen - self._recovery_yaw),
                        np.cos(yaw_seen - self._recovery_yaw))))
                    plausible_step = (self.YAW_RECOVERY_FLOOR +
                                      self.YAW_RECOVERY_RATE * blend_dt)
                    if yaw_step <= plausible_step:
                        self._recovery_count += 1
                        self._recovery_yaw = yaw_seen
                    else:
                        self._recovery_yaw, self._recovery_count = yaw_seen, 1
                if self._recovery_count >= self.YAW_RECOVERY_FRAMES:
                    self.heading += self.YAW_RECOVERY_BLEND * yaw_residual
                    heading_observed = abs(float(np.arctan2(
                        np.sin(yaw_seen - self.heading),
                        np.cos(yaw_seen - self.heading)))) < self.YAW_GATE
        los = bearing + self.heading
        # Current-frame raw range pairs with current-frame bearing. Keep the
        # filtered range only for odometry; do not let its lag certify parking.
        lateral_cam = -rho_now * np.sin(los)
        forward_cam = rho_now * np.cos(los)
        lateral_front = lateral_cam + (WHEELBASE / 2 - CAM_AHEAD) * np.sin(self.heading)
        forward = forward_cam + CAM_AHEAD * np.cos(self.heading)
        return {'lateral': float(-lateral_front), 'heading': float(-self.heading),
                'forward': float(forward), 'bearing': float(-bearing),
                'range_filter_lag': float(range_filter_lag),
                # A zero-initialized/propagated yaw is not proof of alignment.
                'heading_observed': bool(heading_observed)}


def valid_pose(pose):
    '''Validate the required scalar pose fields before any motion or success.'''
    if not isinstance(pose, dict):
        return False
    try:
        values = [pose[k] for k in ('lateral', 'heading', 'forward', 'bearing')]
        return (all(np.isscalar(v) and np.isfinite(v) for v in values) and
                pose['forward'] > 0 and abs(pose['heading']) <= np.pi and
                abs(pose['bearing']) <= np.pi / 2)
    except (KeyError, TypeError, ValueError):
        return False


class Parker:
    '''
    The 2C parking manoeuvre, adapted to a bay that opens off the side of the
    road. A smootherstep path begins at the measured hand-over pose and brings
    the vehicle onto the bay centre line by MERGE_END.
    Then straight on to the spot and stop.
    Marker loss commands an immediate stop; command integration is diagnostic
    only and never establishes parking success. Returns (steering, speed, parked).
    '''

    MERGE_END = 0.26
    # MERGE_END is defined in the existing center-forward frame. The aligned
    # rear axle reaches that plane when the vehicle center is L/2 behind it.
    MERGE_END_REAR = MERGE_END + WHEELBASE / 2.0
    FORWARD_TOLERANCE = 0.015
    LATERAL_TOLERANCE = 0.025
    HEADING_TOLERANCE = np.deg2rad(5.0)
    # Offline marker-frame comparisons from three Hard parks show image
    # centre-forward under-reporting of 7.74–8.48 mm. Use the conservative
    # observed edge only in terminal camera-pose checks. Lateral and heading
    # residual signs changed across runs, so those checks use symmetric
    # completion margins instead of a signed correction. These are generic
    # camera-pose calibration values, never simulator/world coordinates.
    IMAGE_FORWARD_BIAS = 0.0083
    # Keep completion comfortably inside the unchanged physical tolerances.
    COMPLETION_FORWARD_TOLERANCE = 0.010
    COMPLETION_LATERAL_TOLERANCE = 0.015
    COMPLETION_HEADING_TOLERANCE = np.deg2rad(3.5)
    SETTLE_SECONDS = 0.5
    MAX_SPEED = SPEED_LIMIT - 0.05
    MAX_FRAME_TRAVEL = 0.016          # m; bound motion between camera observations
    MAX_YAW_RATE = 0.30               # rad/s; conservative cap retained after the 0.38 trial
    BRAKING_DECEL = 0.020              # m/s^2; conservative approach model
    BRAKING_MARGIN = 0.005             # m before the desired 0.20 m stopping point
    EDGE_BEARING_MARGIN = np.deg2rad(8.0)
    UNCERTAIN_EDGE_STOP_MARGIN = np.deg2rad(15.0)
    TRACK_LATERAL_SCALE = 0.060        # m; scale from live safe-run error distribution
    TRACK_HEADING_SCALE = 0.20         # rad
    CUBIC_BEARING_RESERVE = np.deg2rad(5.0)
    CUBIC_CURVATURE_RESERVE = 0.90

    def __init__(self):
        self.last_pose = None
        self.last_steering = 0.0
        self.last_speed = 0.0
        self.last_time = None
        self.est_forward = None
        self.misses = 0
        self.good_frames = 0
        self.start_rear_lateral = None
        self.start_rear_forward = None
        self.path_profile = None
        self.merge_end_rear = self.MERGE_END_REAR
        self.rest_time = None
        self.failed = False

    @classmethod
    def _completion_pose(cls, pose):
        """Convert image pose to calibrated bay-center/front-axle coordinates."""
        heading = float(np.arctan2(np.sin(pose['heading']), np.cos(pose['heading'])))
        return dict(forward=float(pose['forward'] + cls.IMAGE_FORWARD_BIAS),
                    lateral=float(pose['lateral']),
                    heading=heading)

    @staticmethod
    def _rear_coordinates(pose):
        """Convert bay-relative front/center pose to rear-axle coordinates."""
        lateral = float(pose['lateral']) - WHEELBASE * np.sin(pose['heading'])
        forward = float(pose['forward']) + (WHEELBASE / 2.0) * np.cos(pose['heading'])
        return lateral, forward

    def invalidate(self):
        self.good_frames = 0
        self.rest_time = None
        self.last_pose = None
        self.last_steering = self.last_speed = 0.0

    def _path_reference(self, rear_forward):
        # The quintic's hand-off, progress and cross-track error all use the
        # rear axle. Translate the aligned endpoint from the established
        # center-forward MERGE_END convention exactly once.
        span = max(self.start_rear_forward - self.merge_end_rear, 0.30)
        raw = (rear_forward - self.merge_end_rear) / span
        r = float(np.clip(raw, 0.0, 1.0))
        if self.path_profile is None:
            samples = np.linspace(0.0, 1.0, 201)
            y0 = float(self.start_rear_lateral)
            cubic_slope = y0 * (6 * samples - 6 * samples ** 2) / span
            cubic_second = y0 * (6 - 12 * samples) / span ** 2
            cubic_curvature = cubic_second / (1.0 + cubic_slope ** 2) ** 1.5
            cubic_theta = -np.arctan(cubic_slope)
            x = self.MERGE_END_REAR + span * samples
            camera_x = x - (WHEELBASE / 2.0 + CAM_AHEAD) * np.cos(cubic_theta)
            camera_y = y0 * (3 * samples ** 2 - 2 * samples ** 3) + (
                WHEELBASE / 2.0 + CAM_AHEAD) * np.sin(cubic_theta)
            cubic_bearing = np.arctan2(-camera_y, camera_x) - cubic_theta
            quintic_slope = y0 * (30 * samples ** 4 - 60 * samples ** 3 +
                                   30 * samples ** 2) / span
            quintic_theta = -np.arctan(quintic_slope)
            quintic_y = y0 * (6 * samples ** 5 - 15 * samples ** 4 + 10 * samples ** 3)
            quintic_bearing = np.arctan2(
                -(quintic_y + (WHEELBASE / 2.0 + CAM_AHEAD) * np.sin(quintic_theta)),
                x - (WHEELBASE / 2.0 + CAM_AHEAD) * np.cos(quintic_theta)) - quintic_theta
            bearing_limit = (CAMERA_FOV_X / 2.0 - self.UNCERTAIN_EDGE_STOP_MARGIN -
                             self.CUBIC_BEARING_RESERVE)
            curvature_limit = (np.tan(_virtual_steering_limit()) / WHEELBASE *
                               self.CUBIC_CURVATURE_RESERVE)
            peak_bearing = float(np.max(np.abs(cubic_bearing)))
            peak_quintic_bearing = float(np.max(np.abs(quintic_bearing)))
            useful_bearing_reduction = peak_quintic_bearing - peak_bearing >= np.deg2rad(3.0)
            feasible = (np.max(np.abs(cubic_curvature)) <= curvature_limit and
                        peak_bearing <= bearing_limit and useful_bearing_reduction)
            # A shorter remaining merge can make the cubic just miss its
            # visibility reserve while the quintic is substantially worse.
            # Extend only the planned merge, leaving 2 cm of aligned travel
            # before the bay center. Keep the same curvature/bearing reserves.
            if not feasible and useful_bearing_reduction:
                endpoint = BAY_MIDDLE_FORWARD + WHEELBASE / 2.0 + 0.02
                extended_span = self.start_rear_forward - endpoint
                if extended_span > span:
                    es = y0 * (6*samples - 6*samples**2) / extended_span
                    ec = y0 * (6 - 12*samples) / extended_span**2 / (1+es**2)**1.5
                    et = -np.arctan(es)
                    ex = endpoint + extended_span*samples
                    ey = y0 * (3*samples**2 - 2*samples**3)
                    offset = WHEELBASE / 2.0 + CAM_AHEAD
                    eb = np.arctan2(-(ey + offset*np.sin(et)),
                                    ex - offset*np.cos(et)) - et
                    if (np.max(np.abs(ec)) <= curvature_limit and
                            np.max(np.abs(eb)) <= bearing_limit):
                        self.merge_end_rear = endpoint
                        span = extended_span
                        raw = (rear_forward - endpoint) / span
                        r = float(np.clip(raw, 0.0, 1.0))
                        feasible = True
            self.path_profile = 'cubic' if feasible else 'quintic'
        if self.path_profile == 'cubic':
            lateral = self.start_rear_lateral * (3 * r ** 2 - 2 * r ** 3)
            if not 0.0 < raw < 1.0:
                return lateral, 0.0, 0.0
            slope = self.start_rear_lateral * (6 * r - 6 * r ** 2) / span
            second = self.start_rear_lateral * (6 - 12 * r) / (span * span)
            return lateral, slope, second / (1.0 + slope * slope) ** 1.5
        lateral = self.start_rear_lateral * (6 * r ** 5 - 15 * r ** 4 + 10 * r ** 3)
        if not 0.0 < raw < 1.0:
            return lateral, 0.0, 0.0
        slope = self.start_rear_lateral * (30 * r ** 4 - 60 * r ** 3 + 30 * r ** 2) / span
        second = self.start_rear_lateral * (120 * r ** 3 - 180 * r ** 2 + 60 * r) / (span * span)
        return lateral, slope, second / (1.0 + slope * slope) ** 1.5

    def _adaptive_speed(self, pose, steering, dt, lateral_error, heading_error,
                        lateral_ref, heading_ref):
        """Bound parking speed using observed tracking, timing and stopping room."""
        speed = self.MAX_SPEED
        if dt > 0.0:
            speed = min(speed, self.MAX_FRAME_TRAVEL / (WHEEL_RADIUS * dt))
        remaining = max(pose['forward'] - BAY_MIDDLE_FORWARD - self.BRAKING_MARGIN, 0.0)
        # forward is reconstructed from this frame's raw marker range, so the
        # filtered odometry range lag must not be counted as extra stopping delay.
        response_lag = max(float(dt), 0.0)
        limited_linear_speed = self.BRAKING_DECEL * (
            np.sqrt(response_lag ** 2 + 2.0 * remaining / self.BRAKING_DECEL) -
            response_lag)
        speed = min(speed, limited_linear_speed / WHEEL_RADIUS)
        turn = abs(np.tan(steering)) / WHEELBASE
        if turn > 1e-9:
            speed = min(speed, self.MAX_YAW_RATE / (WHEEL_RADIUS * turn))
        bearing_margin = CAMERA_FOV_X / 2.0 - abs(float(pose['bearing']))
        if (not pose.get('heading_observed', False) and
                bearing_margin < self.UNCERTAIN_EDGE_STOP_MARGIN):
            return 0.0
        if (not pose.get('heading_observed', False) or
                bearing_margin < max(self.EDGE_BEARING_MARGIN,
                                     self.UNCERTAIN_EDGE_STOP_MARGIN)):
            speed = min(speed, ZONE_CRUISE)
        lat_error = abs(lateral_error - lateral_ref)
        yaw_error = abs(heading_error - heading_ref)
        normalized_error = max(lat_error / self.TRACK_LATERAL_SCALE,
                               yaw_error / self.TRACK_HEADING_SCALE)
        tracking_factor = float(np.clip(1.0 - 0.55 * max(normalized_error - 0.5, 0.0),
                                        0.40, 1.0))
        return float(max(0.0, speed * tracking_factor))

    def step(self, pose, now):
        limit = _virtual_steering_limit()
        dt = 0.0 if self.last_time is None else max(now - self.last_time, 0.0)
        self.last_time = now
        if self.est_forward is not None:
            self.est_forward -= self.last_speed * WHEEL_RADIUS * dt

        if self.failed or not valid_pose(pose):
            self.misses += 1
            self.invalidate()
            return 0.0, 0.0, False

        lateral, heading = pose["lateral"], pose["heading"]
        forward, bearing = pose["forward"], pose["bearing"]
        rear_lateral, rear_forward = self._rear_coordinates(pose)
        self.misses = 0
        previous_pose = self.last_pose
        self.last_pose = pose.copy()
        self.est_forward = forward
        if self.start_rear_lateral is None:
            self.start_rear_lateral = rear_lateral
            self.start_rear_forward = rear_forward

        lateral_ref, slope, curvature = self._path_reference(rear_forward)
        heading_ref = -float(np.arctan(slope))

        lateral_error = rear_lateral
        heading_error = float(np.clip(heading, -np.pi / 2.0, np.pi / 2.0))
        lateral_gain = 30.0 if rear_forward < self.merge_end_rear else 7.0
        heading_gain = 8.0 if rear_forward < self.merge_end_rear else 2.8
        steering = (float(np.arctan(WHEELBASE * curvature)) +
                    heading_gain * (heading_ref - heading_error) -
                    lateral_gain * (lateral_error - lateral_ref))
        # Permit the path's planned heading on either merge. Keep the separate
        # marker-bearing guard below to limit turns that move the target out of view.
        heading_limit = max(0.65, abs(heading_ref))
        if heading_error < -heading_limit:
            steering = max(steering, 3.0 * (-heading_limit - heading_error))
        elif heading_error > heading_limit:
            steering = min(steering, 3.0 * (heading_limit - heading_error))
        if bearing > 0.65:
            steering = max(steering, 3.0 * (bearing - 0.65))
        elif bearing < -0.65:
            steering = min(steering, 3.0 * (bearing + 0.65))
        steering = float(np.clip(steering, -limit, limit))

        completion = self._completion_pose(pose)
        check_forward = completion['forward']
        check_lateral = completion['lateral']
        check_heading = completion['heading']
        at_target = check_forward <= BAY_MIDDLE_FORWARD + self.FORWARD_TOLERANCE
        if at_target:
            aligned = (abs(check_forward - BAY_MIDDLE_FORWARD) <=
                       self.COMPLETION_FORWARD_TOLERANCE and
                       abs(check_lateral) <= self.COMPLETION_LATERAL_TOLERANCE and
                       abs(check_heading) <= self.COMPLETION_HEADING_TOLERANCE)
            if not aligned:
                # The front edge of the acceptance window is not an overshoot.
                # Use remaining physical-window distance for a slow correction
                # only when steering authority and lateral clearance support it.
                remaining = check_forward - (BAY_MIDDLE_FORWARD - self.FORWARD_TOLERANCE)
                max_curvature = np.tan(limit) / WHEELBASE
                needed = max(abs(check_heading) - self.COMPLETION_HEADING_TOLERANCE,
                             0.0) / max_curvature
                safe = (remaining > 0 and needed < remaining and
                        abs(check_lateral) + needed * abs(np.sin(check_heading)) <=
                        self.LATERAL_TOLERANCE)
                self.good_frames = 0
                self.rest_time = None
                if safe:
                    steering = float(np.clip(-4.0 * check_heading - 7.0 * check_lateral,
                                             -limit, limit))
                    speed = min(0.25, 14.0 * remaining)
                    self.last_steering, self.last_speed = steering, speed
                    return steering, speed, False
                # No reverse recovery is implemented. Never label an overshoot as parked.
                self.failed = True
            still = (aligned and pose.get('heading_observed', True) and
                     self.last_speed == 0.0 and previous_pose is not None and
                     abs(forward - previous_pose['forward']) <= 0.003 and
                     abs(lateral - previous_pose['lateral']) <= 0.003 and
                     abs(heading - previous_pose['heading']) <= np.deg2rad(2.0))
            self.good_frames = self.good_frames + 1 if still else 0
            if not still:
                self.rest_time = None
            elif self.rest_time is None:
                self.rest_time = now
            self.last_steering, self.last_speed = 0.0, 0.0
            parked = (self.good_frames >= 3 and self.rest_time is not None and
                      now - self.rest_time >= self.SETTLE_SECONDS)
            return 0.0, 0.0, parked

        self.good_frames = 0
        self.rest_time = None

        speed = self._adaptive_speed(pose, steering, dt, lateral_error,
                                     heading_error, lateral_ref, heading_ref)
        self.last_steering, self.last_speed = steering, float(speed)
        return steering, float(speed), False


# ============================================================
#                       MISSION LOGIC
# ============================================================

class SignTracker:
    '''Enter on first sight; release only after a distinct subsequent encounter.

    Require a near approach, sustained absence with commanded travel, and a
    new farther-away sign confirmed in consecutive frames. Absence alone, or
    reacquiring the same near sign, never releases the conservative zone cap.
    Commanded travel is supporting evidence, not measured vehicle motion.
    '''

    def __init__(self, near_range, frames_needed=2, gap_seconds=4.0):
        self.near_range = near_range
        self.frames_needed = frames_needed
        self.gap_seconds = gap_seconds
        self.streak = 0
        self.last_seen = -1e9
        self.nearest = float('inf')
        self.unseen_travel = 0.0
        self.rearmed = False
        self.count = 0

    def update(self, detections, now, frame_dt=0.0, travel=0.0, confirmed=True):
        ranges = [estimate_sign_range(d["bbox"])[0] for d in detections]
        ranges = [r for r in ranges if np.isfinite(r) and r > 0]
        nearest = min(ranges) if ranges else None
        if self.count >= 2:
            return False
        if nearest is None:
            self.streak = 0
            self.unseen_travel += max(travel, 0.0)
            if (self.count == 1 and self.nearest <= self.near_range and
                    now - self.last_seen >= max(self.gap_seconds, 2.5 * frame_dt) and
                    self.unseen_travel >= 0.08):
                self.rearmed = True
            return False
        self.last_seen = now
        self.unseen_travel = 0.0
        if self.count == 0:
            self.count = 1
            self.nearest = nearest
            return True
        distinct = self.rearmed and nearest >= self.nearest + 0.15
        self.streak = self.streak + 1 if distinct else 0
        if not distinct:
            self.rearmed = False
            self.nearest = min(self.nearest, nearest)
        if self.streak >= self.frames_needed and confirmed:
            self.count = 2
            return True
        return False


class Mission:
    '''Everything the vehicle has to remember over one lap.'''

    def __init__(self):
        self.side = None                 # lane being followed
        self.previous_centre = None
        self.zone = False                # inside the Speed 40 zone
        self.zone_done = False
        self.speed40 = SignTracker(ZONE_NEAR_RANGE)
        self.weak_exit = WeakBoardTracker()
        self.hospital_done = False
        self.hospital_armed = False      # a Hospital sign seen far away and approaching
        self.hospital_streak = 0
        self.halt_started = None         # sim time the stop was commanded
        self.rest_time = None            # sim time the vehicle came to rest
        self.previous_gray = None
        self.still_frames = 0
        self.last_change = -1e9
        self.obstacle_streak = 0
        self.changing_until = -1e9
        self.parker = None
        self.estimator = PoseEstimator()
        self.detector = cv2.aruco.ArucoDetector(
            cv2.aruco.getPredefinedDictionary(ARUCO_DICT), cv2.aruco.DetectorParameters())
        self.last_steering = 0.0
        self.finished = False
        self.lost_frames = 0
        self.park_streak = 0
        self.last_now = None
        self.frame_dt = 0.15             # sim seconds between processed frames (measured)
        self.last_speed = 0.0
        self.approach_cap = None
        self.travel = 0.0
        self.frame_travel = 0.0
        self.obstacle_pending = False
        self.obstacle_last_seen = None
        self.obstacle_near_seen = False
        self.obstacle_last_travel = 0.0
        self.obstacles_passed = 0
        self.failed = False
        self.school_near_frames = 0
        self.school_last_seen = None
        self.school_last_travel = 0.0
        self.school_passed = False

    def note(self, now, text):
        print('[%7.2f] %s' % (now, text), flush=True)

    # ---------------- per frame ----------------
    def step(self, frame, now):
        if not np.isfinite(now) or (self.last_now is not None and now < self.last_now):
            raise ValueError('Invalid or decreasing simulation time')
        dt = 0.0 if self.last_now is None else now - self.last_now
        self.frame_travel = self.last_speed * WHEEL_RADIUS * dt
        self.travel += self.frame_travel
        if self.last_now is not None and now > self.last_now:
            self.frame_dt = 0.7 * self.frame_dt + 0.3 * (now - self.last_now)
        self.last_now = now
        self.approach_cap = None
        if (not isinstance(frame, np.ndarray) or frame.shape != (IMG_H, IMG_W, 3) or
                frame.dtype != np.uint8):
            # Account for the preceding final bounded command up to this
            # timestamp before the invalid frame forces an immediate stop.
            self.estimator.update(None, self.last_steering, now,
                                  last_speed=self.last_speed)
            self.invalidate_observations()
            return 0.0, 0.0
        steering, speed = self._step(frame, now)
        if self.approach_cap is not None:
            speed = min(speed, self.approach_cap)
        # On a slow machine fewer frames are processed per simulated second; keep
        # the distance driven between two looks at the road bounded.
        speed = min(speed, MAX_TRAVEL_PER_FRAME / (WHEEL_RADIUS * max(self.frame_dt, 1e-3)))
        speed = min(speed, ZONE_CRUISE if self.zone else CRUISE)
        steering, speed = bounded_command(steering, speed)
        self.last_steering, self.last_speed = steering, speed
        if self.parker is not None:
            # Record the command after every cap, for the next interval's integration.
            self.parker.last_steering, self.parker.last_speed = steering, speed
        return steering, speed

    def invalidate_observations(self):
        self.rest_time = self.previous_gray = None
        self.still_frames = self.park_streak = self.obstacle_streak = 0
        self.hospital_streak = 0
        self.last_steering = self.last_speed = 0.0
        self.speed40.streak = 0
        self.speed40.rearmed = False
        self.speed40.unseen_travel = 0.0
        self.weak_exit.reset()
        self.school_near_frames = 0
        if self.parker is not None:
            self.parker.invalidate()

    def _step(self, frame, now):
        # Once the Speed 40 zone has ended, route perception is no longer used
        # during parking. Mission.step validates frames before reaching here;
        # while the zone is active this shortcut is disabled so its exit sign
        # remains detectable.
        if self.parker is not None and not self.zone:
            return self._park(frame, now)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        red = _colour_mask(hsv, "red")
        blue = _colour_mask(hsv, "blue")
        red_parts = _components(red, 120)
        blue_parts = _components(blue, 120)
        signs = detect_signs(frame, hsv, red_parts, blue_parts)

        # ---- Speed 40 zone ----
        speed40 = [s for s in signs if s["label"] == "Speed40"]
        normal_speed40 = bool(speed40)
        weak_speed40 = []
        if self.zone and self.speed40.rearmed:
            oblique = _oblique_speed40_candidates(frame)
            weak_speed40 = self.weak_exit.update(oblique)
            # Both trackers observe the same raw sequence. Spatial confirmation
            # gates release, while the distinct-encounter tracker still requires
            # two consecutive observations after near approach/travel/absence.
            if len(oblique) == 1:
                speed40.extend(oblique)
        else:
            self.weak_exit.reset()
        if VERBOSE and signs:
            self.note(now, 'signs ' + ', '.join('%s %d r=%.2f' % (s["label"], s["area"],
                      estimate_sign_range(s["bbox"])[0]) for s in signs))
        if self.speed40.update(speed40, now, self.frame_dt, self.frame_travel,
                               confirmed=normal_speed40 or bool(weak_speed40)):
            if not self.zone and not self.zone_done:
                self.zone = True
                self.note(now, 'Speed 40 sign: entering the zone (<= %.2f rad/s)' % ZONE_CRUISE)
            elif self.zone:
                self.zone = False
                self.zone_done = True
                self.note(now, 'second Speed 40 sign: zone ends')
        cap = ZONE_CRUISE if self.zone else CRUISE
        if self.parker is not None:
            return self._park(frame, now)
        self._observe_school(signs, now)

        # ---- Hospital halt ----
        if not self.hospital_done:
            halted = self._hospital(frame, signs, now)
            if halted is not None:
                return halted

        # ---- lane following and obstacles ----
        # Update obstacle evidence before considering a parking hand-over.
        yellow, white = _lane_masks(hsv)
        lane = detect_lane(yellow, white, self.side, self.previous_centre)
        obstacles = detect_obstacles(hsv, red)
        # Far red building trim is also detected by the existing 2B mask. Only
        # ground-level near encounters (the existing change-lane row) block parking.
        near_obstacles = [o for o in obstacles if o['base'][1] >= IMG_H * OBSTACLE_TRIGGER_ROW]
        self._observe_obstacles(near_obstacles, now)

        # ---- parking hand-over ----
        # The exit sign can face away. A visually passed School after Hospital
        # and zone entry provides independent route progress; keep the zone cap
        # in that case. The target marker must still satisfy the entry pose gate.
        route_progress = self.zone_done or (self.zone and self.school_passed)
        parking_ready = (self.hospital_done and route_progress and not self.obstacle_pending and
                         now >= self.changing_until and lane['valid'] and not near_obstacles)
        if parking_ready:
            corners = self._marker(frame)
            lined_up = False
            if corners is not None:
                # Fresh estimate each frame: on the straight the heading is ~0.
                pose = PoseEstimator().update(corners, 0.0, now, last_speed=0.0)
                # The estimate assumes we are parallel to the bay; coming out of the
                # bend it reads too far left, so the gate is tight for the inner lane.
                max_lateral = PARK_MAX_LATERAL if self.side == "left" else PARK_INNER_LATERAL
                lined_up = (valid_pose(pose) and pose["forward"] <= PARK_START_FORWARD and
                            0.10 < pose["lateral"] < max_lateral)
            self.park_streak = self.park_streak + 1 if lined_up else 0
            if self.park_streak >= 3:
                self.note(now, 'parking: marker at %.2f m, lateral %.2f m'
                          % (pose["forward"], pose["lateral"]))
                self.parker = Parker()
                self.estimator = PoseEstimator()
                self.estimator.update(corners, 0.0, now, last_speed=0.0)
                return self._drive_parking(pose, now)
        else:
            self.park_streak = 0

        if not lane["valid"]:
            self.lost_frames += 1
            speed = cap * 0.5 if self.lost_frames < 10 else 0.0
            return self.last_steering, speed
        self.lost_frames = 0
        if self.side is None:
            self.side = lane["side"]
            self.note(now, 'starting in the %s-edged lane' % self.side)

        if VERBOSE and obstacles:
            self.note(now, 'obstacles ' + ', '.join('box %s in-lane %s' % (o["bbox"], obstacle_in_lane(o, lane))
                                                    for o in obstacles) + ' side %s' % self.side)
        blocking = [o for o in obstacles
                    if IMG_H * OBSTACLE_TRIGGER_ROW <= o["base"][1] <= IMG_H * OBSTACLE_LATEST_ROW
                    and obstacle_in_lane(o, lane)]
        self.obstacle_streak = self.obstacle_streak + 1 if blocking else 0
        if self.obstacle_streak >= 2 and now - self.last_change > LANE_CHANGE_COOLDOWN:
            self.side = "left" if self.side == "right" else "right"
            self.last_change = now
            self.changing_until = now + 6.0
            self.previous_centre = None
            self.note(now, 'obstacle in lane at row %.0f: changing to the %s-edged lane'
                      % (blocking[0]["base"][1], self.side))
            lane = detect_lane(yellow, white, self.side, None)
            if not lane["valid"]:
                return self.last_steering, cap * 0.6

        self.previous_centre = lane["center_near"]
        if now < self.changing_until:
            cap = min(cap, LANE_CHANGE_SPEED)
        steering, speed = lane_control(lane, cap)
        self.last_steering = steering
        return steering, speed

    # ---------------- helpers ----------------
    def _observe_school(self, signs, now):
        if self.school_passed or not (self.hospital_done and (self.zone or self.zone_done)):
            return
        school = [s for s in signs if s['label'] == 'School']
        if school:
            near = min(estimate_sign_range(s['bbox'])[0] for s in school) <= ZONE_NEAR_RANGE
            self.school_near_frames = self.school_near_frames + 1 if near else 0
            self.school_last_seen = now
            self.school_last_travel = self.travel
        elif (self.school_near_frames >= 2 and self.school_last_seen is not None and
              now - self.school_last_seen >= max(0.4, 2.5 * self.frame_dt) and
              self.travel - self.school_last_travel >= 0.08):
            self.school_passed = True
            self.note(now, 'School sign passed after Hospital and Speed 40 entry; driving on')

    def _observe_obstacles(self, obstacles, now):
        if obstacles:
            self.obstacle_pending = True
            self.obstacle_last_seen = now
            self.obstacle_last_travel = self.travel
            self.obstacle_near_seen |= any(o['base'][1] >= IMG_H * OBSTACLE_TRIGGER_ROW
                                           for o in obstacles)
        elif (self.obstacle_pending and self.obstacle_near_seen and
              now - self.obstacle_last_seen >= max(0.4, 2.5 * self.frame_dt) and
              self.travel - self.obstacle_last_travel >= 0.12):
            # Camera disappearance after a near encounter plus forward command
            # history supports passing. It cannot prove unseen obstacles are absent.
            self.obstacle_pending = False
            self.obstacle_near_seen = False
            self.obstacles_passed += 1

    def _hospital(self, frame, signs, now):
        if self.halt_started is not None:
            gray = cv2.resize(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), (80, 60)).astype(np.float32)
            if self.previous_gray is not None:
                moving = float(np.mean(np.abs(gray - self.previous_gray))) > 0.6
                self.still_frames = 0 if moving else self.still_frames + 1
                if moving:
                    self.rest_time = None
            self.previous_gray = gray
            if self.rest_time is None and self.still_frames >= 2:
                self.rest_time = now
                self.note(now, 'at rest - holding %.1f s' % (HALT_SECONDS + HALT_MARGIN))
            if self.rest_time is not None and now - self.rest_time >= HALT_SECONDS + HALT_MARGIN:
                self.hospital_done = True
                self.note(now, 'halt complete, driving on')
                return None
            return self.last_steering, 0.0

        hospital = [s for s in signs if s["label"] == "Hospital"]
        if not hospital:
            self.hospital_streak = 0
            return None
        ranged = [estimate_sign_range(s["bbox"]) for s in hospital]
        ranged = [r for r in ranged if 0.05 <= r[1] <= 0.30]   # roadside, to the right
        if not ranged:
            self.hospital_streak = 0
            return None
        forward, lateral = min(ranged, key=lambda r: r[0])
        self.hospital_streak += 1
        if (forward > HOSPITAL_ARM_RANGE or
                (self.hospital_streak >= 2 and
                 forward > HOSPITAL_STOP_RANGE + HALT_COAST + 0.02)):
            if not self.hospital_armed:
                self.note(now, 'Hospital sign ahead at %.2f m' % forward)
            self.hospital_armed = True
        if not self.hospital_armed:
            return None
        # Where the vehicle would come to rest if told to stop now: it keeps
        # going for about one frame of latency, then coasts briefly. Stop on the
        # frame whose rest point is nearest the pickup point, whatever the frame rate.
        travel = self.last_speed * WHEEL_RADIUS * self.frame_dt
        rest_range = forward - HALT_COAST - HALT_LAG_FRAMES * travel
        if rest_range <= HOSPITAL_STOP_RANGE + 0.5 * travel:
            self.halt_started = now
            self.note(now, 'Hospital pickup point: stopping (sign at %.2f m, %.2f m right, '
                      'frame %.2f s)' % (forward, lateral, self.frame_dt))
            return self.last_steering, 0.0
        if rest_range <= HOSPITAL_STOP_RANGE + 0.12:
            self.approach_cap = HALT_APPROACH_SPEED
        return None

    def _marker(self, frame):
        corners, ids, _ = self.detector.detectMarkers(frame)
        if ids is None:
            return None
        for quad, marker_id in zip(corners, ids.flatten()):
            if int(marker_id) == PARK_MARKER_ID:
                return quad.reshape(4, 2)
        return None

    def _park(self, frame, now):
        corners = self._marker(frame)
        pose = self.estimator.update(corners, self.last_steering, now,
                                     last_speed=self.last_speed)
        return self._drive_parking(pose, now)

    def _drive_parking(self, pose, now=None):
        steering, speed, parked = self.parker.step(pose, now)
        self.failed = self.parker.failed
        if VERBOSE:
            self.note(now, 'park pose %s -> steer %.3f speed %.2f parked %s' % (
                None if pose is None else {k: round(v, 3) for k, v in pose.items()},
                steering, speed, parked))
        if parked:
            self.finished = True
            return 0.0, 0.0
        self.last_steering = steering
        return steering, speed


# ============================================================
#                       SIMULATOR I/O
# ============================================================

def connect_and_locate():
    try:
        sim = RemoteAPIClient().getObject('sim')
        sim.getSimulationTime()
    except Exception as err:
        raise ConnectionError('Could not reach CoppeliaSim on the ZMQ Remote API port: %s' % err)
    handles = {}
    for name, path in (('vision_sensor', VISION_SENSOR), ('steer_left', STEER_LEFT),
                       ('steer_right', STEER_RIGHT), ('motor_left', MOTOR_LEFT),
                       ('motor_right', MOTOR_RIGHT)):
        handles[name] = sim.getObject(path)
    return sim, handles


def read_frame(sim, handles):
    sim.handleVisionSensor(handles['vision_sensor'])
    img, res = sim.getVisionSensorImg(handles['vision_sensor'], 0)
    if img is None or not res or len(res) != 2 or tuple(res) != (IMG_W, IMG_H):
        return None
    try:
        if len(img) != res[0] * res[1] * 3:
            return None
        frame = np.frombuffer(img, dtype=np.uint8).reshape((res[1], res[0], 3))
    except (TypeError, ValueError):
        return None
    frame = cv2.flip(frame, 0)
    return cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)


def bounded_command(steering, speed):
    if not np.isfinite([steering, speed]).all():
        return 0.0, 0.0
    speed = float(np.clip(speed, 0.0, SPEED_LIMIT))
    steering = float(np.clip(steering, -_virtual_steering_limit(), _virtual_steering_limit()))
    return steering, speed


def drive(sim, handles, steering, speed):
    steering, speed = bounded_command(steering, speed)
    left, right = ackermann_wheel_angles(steering)
    sim.setJointTargetPosition(handles['steer_left'], left)
    sim.setJointTargetPosition(handles['steer_right'], right)
    sim.setJointTargetVelocity(handles['motor_left'], speed)
    sim.setJointTargetVelocity(handles['motor_right'], speed)


def main():
    sim, handles = None, None
    frames = 0
    result = 0
    try:
        sim, handles = connect_and_locate()
        deadline = time.monotonic() + 120.0
        mission = Mission()
        started = False
        print('Waiting for the simulation to run - Task 3 lap.', flush=True)
        advancing = {sim.simulation_advancing_firstafterstop, sim.simulation_advancing_running,
                     sim.simulation_advancing_firstafterpause}
        stopping = {sim.simulation_advancing_abouttostop, sim.simulation_advancing_lastbeforestop}
        while True:
            state = sim.getSimulationState()
            if state in stopping or (started and state == sim.simulation_stopped):
                break
            if state not in advancing:
                drive(sim, handles, 0.0, 0.0)
                mission.invalidate_observations()
                if not started and time.monotonic() > deadline:
                    raise TimeoutError('The simulation never started.')
                time.sleep(0.05)
                continue
            started = True
            frame = read_frame(sim, handles)
            now = sim.getSimulationTime()
            steering, speed = mission.step(frame, now)
            drive(sim, handles, steering, speed)
            if frame is None:
                time.sleep(0.01)
                continue
            frames += 1
            if mission.failed:
                raise RuntimeError('Parking target reached without valid alignment; stopped.')
            if mission.finished:
                mission.note(now, 'parked')
                break
    except KeyboardInterrupt:
        print('\nInterrupted.')
        result = 130
    except Exception as err:
        print('Loop ended: %s: %s' % (type(err).__name__, err))
        result = 1
    finally:
        if sim is not None and handles is not None:
            for motor in ('motor_left', 'motor_right'):
                try:
                    sim.setJointTargetVelocity(handles[motor], 0.0)
                except Exception as err:
                    print('Could not stop %s: %s' % (motor, err))
                    result = 1
    print('%d frames processed.' % frames)
    return result


if __name__ == '__main__':
    sys.exit(main())
