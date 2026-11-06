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
FOCAL_PX      = (IMG_W / 2) / np.tan(np.deg2rad(95.0) / 2)
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
CRUISE        = 2.90                 # what we actually command (a margin below the limits)
ZONE_CRUISE   = 1.19
ZONE_ENTRY_RANGE = 0.32           # m, a Speed 40 sign this close counts as reached
ZONE_NEAR_RANGE  = 0.65           # m, ...or seen this close and then out of view

HALT_SECONDS      = 5.0              # required stationary time (simulation time)
HALT_MARGIN       = 0.8              # extra hold so the graded 5 s is never short
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
    rectangle = _ordered_box(cv2.boxPoints(cv2.minAreaRect(contour)))
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
        if y < 1 or y >= image.shape[0] * 0.75:
            continue
        ratio = width / float(height or 1)
        if ratio < 0.55 or ratio > 1.45:
            continue
        symbol = _rectified_white_mask(image, component["contour"])
        parking_score = _template_score(symbol, _PARKING_TEMPLATE)
        hospital_score = _template_score(symbol, _HOSPITAL_TEMPLATE)
        if parking_score < 0.045 and hospital_score < 0.075:
            continue
        label = "Parking" if parking_score >= hospital_score else "Hospital"
        detections.append({"label": label, "area": int(round(component["area"])),
                           "bbox": component["bbox"]})
    return detections


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
    speed = speed_cap * (1.0 - 0.15 * turn) if speed_cap > ZONE_LIMIT else speed_cap
    return virtual, float(min(speed, speed_cap))


# ============================================================
#                       PARKING (2C)
# ============================================================

class PoseEstimator:
    '''Vehicle pose relative to the bay from the ArUco marker (2C).'''

    YAW_BLEND = 0.12
    YAW_GATE = np.deg2rad(15.0)
    AMBIGUITY_RATIO = 1.5

    def __init__(self):
        self.heading = 0.0
        self.rho = None

    @staticmethod
    def _bearing(corners):
        cx, cy = corners[:, 0].mean(), corners[:, 1].mean()
        xc = (cx - IMG_W / 2) / FOCAL_PX
        yc = (IMG_H / 2 - cy) / FOCAL_PX
        return float(np.arctan2(xc, np.cos(CAM_PITCH) + yc * np.sin(CAM_PITCH)))

    def _pnp(self, corners):
        _, rvecs, tvecs, errs = cv2.solvePnPGeneric(
            MARKER_CORNERS_3D, corners.astype(np.float32), CAMERA_MATRIX,
            np.zeros(5), flags=cv2.SOLVEPNP_IPPE_SQUARE)
        sols = []
        for rv, tv, e in zip(rvecs, tvecs, np.array(errs).flatten()):
            R, _ = cv2.Rodrigues(rv)
            fwd = R.T @ np.array([0.0, 0.0, 1.0])
            sols.append((float(e), float(np.arctan2(fwd[0], -fwd[2])), tv.flatten()))
        sols.sort(key=lambda s: s[0])
        t = sols[0][2]
        rho = float(np.sqrt(max(t @ t - CAM_ABOVE_MK ** 2, 1e-6)))
        clear = len(sols) < 2 or sols[1][0] > self.AMBIGUITY_RATIO * max(sols[0][0], 1e-6)
        return (sols[0][1] if clear else None), rho

    def update(self, corners, last_steering):
        if corners is None:
            return None
        bearing = self._bearing(corners)
        yaw_seen, rho_now = self._pnp(corners)
        if self.rho is None:
            self.rho = rho_now
        rho_prev, self.rho = self.rho, 0.6 * self.rho + 0.4 * rho_now
        ds = min(max((rho_prev - self.rho) / max(np.cos(bearing), 0.3), 0.0), 0.01)
        self.heading -= np.tan(last_steering) / WHEELBASE * ds
        if yaw_seen is not None and abs(yaw_seen - self.heading) < self.YAW_GATE:
            self.heading += self.YAW_BLEND * (yaw_seen - self.heading)
        los = bearing + self.heading
        lateral_cam = -self.rho * np.sin(los)
        forward_cam = self.rho * np.cos(los)
        lateral_front = lateral_cam + (WHEELBASE / 2 - CAM_AHEAD) * np.sin(self.heading)
        forward = forward_cam + CAM_AHEAD * np.cos(self.heading)
        return {'lateral': float(-lateral_front), 'heading': float(-self.heading),
                'forward': float(forward), 'bearing': float(-bearing)}


class Parker:
    '''
    The 2C parking manoeuvre, adapted to a bay that opens off the side of the
    road. The lane position at hand-over is held until the bay is alongside
    (MERGE_START), then a smootherstep path brings the vehicle onto the bay's
    centre line by MERGE_END, so the wheels never cut the corner of the bay.
    Then straight on to the spot and stop.
    If the marker drops out of view near the end, the remaining distance is
    dead-reckoned from the commanded wheel speed. Returns (steering, speed, parked).
    '''

    MERGE_START = 0.78                   # hold the lane until the bay is alongside
    MERGE_END = 0.26

    def __init__(self):
        self.last_pose = None
        self.last_steering = 0.0
        self.last_speed = 0.6
        self.last_time = None
        self.est_forward = None
        self.misses = 0
        self.good_frames = 0
        self.start_lateral = None
        self.start_forward = None

    def step(self, pose, now):
        limit = _virtual_steering_limit()
        dt = 0.0 if self.last_time is None else max(now - self.last_time, 0.0)
        self.last_time = now
        if self.est_forward is not None:
            self.est_forward -= self.last_speed * WHEEL_RADIUS * dt

        if pose is None or not np.all(np.isfinite(list(pose.values()))):
            self.misses += 1
            if self.last_pose is None:
                return 0.0, 0.3, False
            if self.good_frames >= 3:
                return 0.0, 0.0, True
            if self.est_forward is not None and self.est_forward < self.MERGE_END + 0.12:
                # Close in and the marker is out of view: straight on, by odometry.
                if self.est_forward <= BAY_MIDDLE_FORWARD:
                    return 0.0, 0.0, True
                self.last_steering = 0.0
                self.last_speed = float(np.clip(14.0 * (self.est_forward - BAY_MIDDLE_FORWARD), 0.25, 0.6))
                return 0.0, self.last_speed, False
            steering = self.last_steering * (0.97 ** min(self.misses, 30))
            self.last_speed = 0.3 if self.misses < 60 else 0.0
            self.last_steering = steering
            return float(np.clip(steering, -limit, limit)), self.last_speed, False

        lateral, heading = pose["lateral"], pose["heading"]
        forward, bearing = pose["forward"], pose["bearing"]
        self.misses = 0
        self.last_pose = pose
        self.est_forward = forward
        if self.start_lateral is None:
            self.start_lateral, self.start_forward = lateral, forward

        # From the outer lane the shift is twice as long, so it uses the whole approach.
        merge_start = self.MERGE_START if self.start_lateral <= PARK_INNER_LATERAL else self.start_forward
        span = max(min(self.start_forward, merge_start) - self.MERGE_END, 0.30)
        r = float(np.clip((forward - self.MERGE_END) / span, 0.0, 1.0))
        lateral_ref = self.start_lateral * (6 * r ** 5 - 15 * r ** 4 + 10 * r ** 3)
        slope = self.start_lateral * (30 * r ** 4 - 60 * r ** 3 + 30 * r ** 2) / span
        heading_ref = -float(np.arctan(slope))
        second = self.start_lateral * (120 * r ** 3 - 180 * r ** 2 + 60 * r) / (span * span)
        curvature = second / (1.0 + slope * slope) ** 1.5

        lateral_error = float(lateral - WHEELBASE * np.sin(heading))
        heading_error = float(np.clip(heading, -np.pi / 2.0, np.pi / 2.0))
        lateral_gain = 30.0 if forward < self.MERGE_END else 7.0
        heading_gain = 4.0 if forward < self.MERGE_END else 2.8
        steering = (float(np.arctan(WHEELBASE * curvature)) +
                    heading_gain * (heading_ref - heading_error) -
                    lateral_gain * (lateral_error - lateral_ref))
        if heading_error < -0.65:
            steering = max(steering, 3.0 * (-0.65 - heading_error))
        elif heading_error > 0.65:
            steering = min(steering, 3.0 * (0.65 - heading_error))
        if bearing > 0.55:
            steering = max(steering, 3.0 * (bearing - 0.55))
        elif bearing < -0.55:
            steering = min(steering, 3.0 * (bearing + 0.55))
        steering = float(np.clip(steering, -limit, limit))

        # The vehicle cannot reverse, so reaching the spot's distance ends the manoeuvre.
        at_target = forward <= BAY_MIDDLE_FORWARD + 0.015
        self.good_frames = self.good_frames + 1 if at_target else 0
        if self.good_frames >= 2 or forward < BAY_MIDDLE_FORWARD - 0.02:
            self.last_speed = 0.0
            return 0.0, 0.0, True
        if at_target:
            self.last_steering, self.last_speed = 0.0, 0.0
            return 0.0, 0.0, False

        if forward > self.MERGE_START:
            speed = 2.2
        else:
            speed = float(np.clip(14.0 * (forward - BAY_MIDDLE_FORWARD), 0.25, 1.19))
        if abs(steering) > 0.80 * limit:
            speed = min(speed, 0.65)
        self.last_steering, self.last_speed = steering, float(speed)
        return steering, float(speed), False


# ============================================================
#                       MISSION LOGIC
# ============================================================

class SignTracker:
    '''Turns per-frame detections of one sign label into one event per sign.
    A sign counts as reached once it is seen within `max_range` for a few
    frames - or, when it sits far enough to the side that it leaves the
    camera's view first, once it has been seen within `near_range` and then
    drops out of sight. The next sign of the label counts only after this one
    has been out of sight for `gap_seconds`.'''

    def __init__(self, max_range, near_range, frames_needed=2, gap_seconds=3.0, lost_seconds=0.4):
        self.max_range = max_range
        self.near_range = near_range
        self.frames_needed = frames_needed
        self.gap_seconds = gap_seconds
        self.lost_seconds = lost_seconds
        self.streak = 0
        self.near_streak = 0
        self.last_seen = -1e9
        self.active = False              # current sign already counted
        self.closing = False             # current sign seen near, not yet counted
        self.count = 0

    def update(self, detections, now, frame_dt=0.0):
        '''Returns True on the frame a new sign is confirmed. A single missed
        detection is not "out of view": lost means unseen for a few frames.'''
        ranges = [estimate_sign_range(d["bbox"])[0] for d in detections]
        if ranges:
            self.last_seen = now
        nearest = min(ranges) if ranges else None
        self.streak = self.streak + 1 if nearest is not None and nearest <= self.max_range else 0
        self.near_streak = self.near_streak + 1 if nearest is not None and nearest <= self.near_range else 0
        if self.active:
            if now - self.last_seen > self.gap_seconds:
                self.active = False
            return False
        if self.near_streak >= self.frames_needed:
            self.closing = True
        lost = (self.closing and nearest is None and
                now - self.last_seen >= max(self.lost_seconds, 2.5 * frame_dt))
        if self.streak >= self.frames_needed or lost:
            self.active = True
            self.closing = False
            self.count += 1
            return True
        if self.closing and nearest is None and now - self.last_seen > self.gap_seconds:
            self.closing = False
        return False


class Mission:
    '''Everything the vehicle has to remember over one lap.'''

    def __init__(self):
        self.side = None                 # lane being followed
        self.previous_centre = None
        self.zone = False                # inside the Speed 40 zone
        self.zone_done = False
        self.speed40 = SignTracker(ZONE_ENTRY_RANGE, ZONE_NEAR_RANGE, frames_needed=2, gap_seconds=4.0)
        self.hospital_done = False
        self.hospital_armed = False      # a Hospital sign seen far away and approaching
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

    def note(self, now, text):
        print('[%7.2f] %s' % (now, text), flush=True)

    # ---------------- per frame ----------------
    def step(self, frame, now):
        if self.last_now is not None and now > self.last_now:
            self.frame_dt = 0.7 * self.frame_dt + 0.3 * (now - self.last_now)
        self.last_now = now
        self.approach_cap = None
        steering, speed = self._step(frame, now)
        if self.approach_cap is not None:
            speed = min(speed, self.approach_cap)
        # On a slow machine fewer frames are processed per simulated second; keep
        # the distance driven between two looks at the road bounded.
        speed = min(speed, MAX_TRAVEL_PER_FRAME / (WHEEL_RADIUS * max(self.frame_dt, 1e-3)))
        self.last_speed = speed
        return steering, speed

    def _step(self, frame, now):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        red = _colour_mask(hsv, "red")
        blue = _colour_mask(hsv, "blue")
        red_parts = _components(red, 120)
        blue_parts = _components(blue, 120)
        signs = detect_signs(frame, hsv, red_parts, blue_parts)

        # ---- Speed 40 zone ----
        speed40 = [s for s in signs if s["label"] == "Speed40"]
        if VERBOSE and signs:
            self.note(now, 'signs ' + ', '.join('%s %d r=%.2f' % (s["label"], s["area"],
                      estimate_sign_range(s["bbox"])[0]) for s in signs))
        if self.speed40.update(speed40, now, self.frame_dt):
            if not self.zone and not self.zone_done:
                self.zone = True
                self.note(now, 'Speed 40 sign: entering the zone (<= %.2f rad/s)' % ZONE_CRUISE)
            elif self.zone:
                self.zone = False
                self.zone_done = True
                self.note(now, 'second Speed 40 sign: zone ends')
        cap = ZONE_CRUISE if (self.zone or self.zone_done) else CRUISE
        if self.parker is not None:
            return self._park(frame, now)

        # ---- Hospital halt ----
        if not self.hospital_done:
            halted = self._hospital(frame, signs, now)
            if halted is not None:
                return halted

        # ---- parking hand-over ----
        # The second Speed 40 sign is not always in view from the bend before the
        # bay, so parking only waits for the halt and the zone to have begun.
        if self.hospital_done and (self.zone or self.zone_done):
            corners = self._marker(frame)
            if corners is not None:
                # Fresh estimate each frame: on the straight the heading is ~0.
                pose = PoseEstimator().update(corners, 0.0)
                # The estimate assumes we are parallel to the bay; coming out of the
                # bend it reads too far left, so the gate is tight for the inner lane.
                max_lateral = PARK_MAX_LATERAL if self.side == "left" else PARK_INNER_LATERAL
                lined_up = (pose is not None and pose["forward"] <= PARK_START_FORWARD and
                            0.10 < pose["lateral"] < max_lateral)
                self.park_streak = self.park_streak + 1 if lined_up else 0
                if self.park_streak >= 3:
                    self.note(now, 'parking: marker at %.2f m, lateral %.2f m'
                              % (pose["forward"], pose["lateral"]))
                    self.parker = Parker()
                    self.estimator = PoseEstimator()
                    self.estimator.update(corners, 0.0)
                    return self._drive_parking(pose, now)

        # ---- lane following and obstacles ----
        yellow, white = _lane_masks(hsv)
        lane = detect_lane(yellow, white, self.side, self.previous_centre)
        if not lane["valid"]:
            self.lost_frames += 1
            speed = cap * 0.5 if self.lost_frames < 10 else 0.0
            return self.last_steering, speed
        self.lost_frames = 0
        if self.side is None:
            self.side = lane["side"]
            self.note(now, 'starting in the %s-edged lane' % self.side)

        obstacles = detect_obstacles(hsv, red)
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
    def _hospital(self, frame, signs, now):
        if self.halt_started is not None:
            gray = cv2.resize(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), (80, 60)).astype(np.float32)
            if self.previous_gray is not None:
                moving = float(np.mean(np.abs(gray - self.previous_gray))) > 0.6
                self.still_frames = 0 if moving else self.still_frames + 1
            self.previous_gray = gray
            if self.rest_time is None and (self.still_frames >= 2 or now - self.halt_started > 1.5):
                self.rest_time = now
                self.note(now, 'at rest - holding %.1f s' % (HALT_SECONDS + HALT_MARGIN))
            if self.rest_time is not None and now - self.rest_time >= HALT_SECONDS + HALT_MARGIN:
                self.hospital_done = True
                self.note(now, 'halt complete, driving on')
                return None
            return self.last_steering, 0.0

        hospital = [s for s in signs if s["label"] == "Hospital"]
        if not hospital:
            return None
        ranged = [estimate_sign_range(s["bbox"]) for s in hospital]
        ranged = [r for r in ranged if 0.05 <= r[1] <= 0.30]   # roadside, to the right
        if not ranged:
            return None
        forward, lateral = min(ranged, key=lambda r: r[0])
        if forward > HOSPITAL_ARM_RANGE:
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
        pose = self.estimator.update(corners, self.last_steering)
        return self._drive_parking(pose, now)

    def _drive_parking(self, pose, now=None):
        steering, speed, parked = self.parker.step(pose, now)
        if VERBOSE:
            self.note(now, 'park pose %s -> steer %.3f speed %.2f parked %s' % (
                None if pose is None else {k: round(v, 3) for k, v in pose.items()},
                steering, speed, parked))
        if parked:
            self.finished = True
            return 0.0, 0.0
        self.last_steering = steering
        # The second Speed 40 sign is not reliably in view on the way into the bay,
        # so the zone limit is kept all the way into the spot.
        return steering, min(speed, ZONE_CRUISE)


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
    if len(img) == 0:
        return None
    frame = np.frombuffer(img, dtype=np.uint8).reshape((res[1], res[0], 3))
    frame = cv2.flip(frame, 0)
    return cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)


def drive(sim, handles, steering, speed):
    speed = float(np.clip(speed, 0.0, SPEED_LIMIT - 0.05))
    left, right = ackermann_wheel_angles(float(np.clip(steering, -_virtual_steering_limit(),
                                                       _virtual_steering_limit())))
    sim.setJointTargetPosition(handles['steer_left'], left)
    sim.setJointTargetPosition(handles['steer_right'], right)
    sim.setJointTargetVelocity(handles['motor_left'], speed)
    sim.setJointTargetVelocity(handles['motor_right'], speed)


def main():
    sim, handles = connect_and_locate()
    deadline = time.monotonic() + 120.0
    if sim.getSimulationState() != sim.simulation_advancing_running:
        print('Waiting for the simulation to start - press Play in CoppeliaSim.', flush=True)
    while sim.getSimulationState() != sim.simulation_advancing_running:
        if time.monotonic() > deadline:
            print('The simulation never started.')
            return 1
        time.sleep(0.05)
    print('Simulation running - Task 3 lap.', flush=True)

    mission = Mission()
    frames = 0
    try:
        while sim.getSimulationState() == sim.simulation_advancing_running:
            frame = read_frame(sim, handles)
            if frame is None:
                continue
            frames += 1
            now = sim.getSimulationTime()
            steering, speed = mission.step(frame, now)
            drive(sim, handles, steering, speed)
            if mission.finished:
                mission.note(now, 'parked')
                break
        if mission.finished:
            # Let the vehicle settle so it is at rest when the run ends.
            settle = sim.getSimulationTime()
            while (sim.getSimulationState() == sim.simulation_advancing_running and
                   sim.getSimulationTime() - settle < 1.0):
                drive(sim, handles, 0.0, 0.0)
                time.sleep(0.01)
    except KeyboardInterrupt:
        print('\nInterrupted.')
    except Exception as err:
        print('Loop ended: %s: %s' % (type(err).__name__, err))
    finally:
        try:
            sim.setJointTargetVelocity(handles['motor_left'], 0.0)
            sim.setJointTargetVelocity(handles['motor_right'], 0.0)
        except Exception:
            pass
    print('%d frames processed.' % frames)
    return 0


if __name__ == '__main__':
    sys.exit(main())
