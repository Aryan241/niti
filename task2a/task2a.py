'''
*****************************************************************************************
*
*  ===============================================
*     Niti Vahan (NV) Theme of eYRC 2026-27
*  ===============================================
*
*  This script is intended for implementation of Task 2A of Niti Vahan (NV) Theme.
*
*  Filename:         task2a.py
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
# Filename:         task2a.py
# Functions:        detect_lane, compute_control
# Global variables: < List any global variables you add, "None" if you add none >


####################### IMPORT MODULES #######################
import sys
import time

import cv2
import numpy as np

from coppeliasim_zmqremoteapi_client import RemoteAPIClient
##############################################################


##################### SCENE CONSTANTS ########################
# Paths into the CoppeliaSim scene hierarchy, read off Task_2A.ttt.
VISION_SENSOR = '/Niti_Vahan/Camera_joint/Cuboid/visionSensor'
STEER_LEFT    = '/steeringLeft'
STEER_RIGHT   = '/steeringRight'
MOTOR_LEFT    = '/motorLeft'
MOTOR_RIGHT   = '/motorRight'

# The integer signal the evaluation raises when the vehicle must stop.
STOP_SIGNAL = 'NV_stop'
##############################################################


##############################################################
############### ADD YOUR IMPLEMENTATION HERE #################
##############################################################

def detect_lane(frame):
    '''
    Purpose:
    ---
    Work out, from a single camera frame, how wrong the vehicle currently is -
    and hand back whatever `compute_control()` needs in order to correct it.

    This is your Task 1C detector, extended. Task 1C answered *where the lane
    centre is* and *which lane the vehicle is in*; a controller cannot use
    either of those directly. It needs to know how far the vehicle is from
    where it should be, and which way it is pointing.

    Input Arguments:
    ---
    `frame` :   [ numpy.ndarray ]
        One BGR frame from the vehicle's camera, of shape (height, width, 3),
        the right way up and in the right colour order.

    Returns:
    ---
    Anything you like - a tuple, a dictionary, your own class. Whatever you
    return here is passed straight to compute_control() and nowhere else, so
    the two functions only have to agree with each other.

    Example call:
    ---
    detection = detect_lane(frame)

    REMEMBER:
    ---
    Both lanes are driven during evaluation, and the arena looks mirrored from
    the other one. Do not hard-code which side the boundary is on.

    Do NOT call cv2.imshow() or cv2.imwrite() from inside this function.

    You are marked on how closely you hold the MIDDLE of your lane, not merely
    on staying the correct side of the dashed line.
    '''

    global _LANE_TRACK

    if not isinstance(frame, np.ndarray) or frame.ndim != 3 or frame.shape[2] != 3:
        return {"valid": False, "lane": "unknown", "center_near": 0.0,
                "center_far": 0.0, "image_center": 0.0}

    height, width = frame.shape[:2]
    yellow, white = _lane_masks(frame)
    y_min = int(height * 0.42)
    y_max = int(height * 0.90)

    yellow_models = _solid_line_models(yellow, y_min, y_max, 180, 32)
    white_points = _dashed_line_points(white, height, width)
    white_models = _dashed_line_models(white_points, height, width)
    pair = _choose_lane_pair(yellow_models, white_models, height, width)

    if pair is None:
        return {"valid": False, "lane": "unknown", "center_near": width * 0.5,
                "center_far": width * 0.5, "image_center": width * 0.5}

    outer_model, divider_model, lane_side = pair
    reference_rows = (height * 0.62, height * 0.74, height * 0.84)
    centres = [(row, 0.5 * (_model_x(outer_model, row, height) +
                             _model_x(divider_model, row, height)))
               for row in reference_rows]
    if not all(np.isfinite(value) for _, value in centres):
        return {"valid": False, "lane": lane_side, "center_near": width * 0.5,
                "center_far": width * 0.5, "image_center": width * 0.5}

    centre_model = _fit_point_model(np.asarray(centres, dtype=np.float32), height)
    near = _model_x(centre_model, height * 0.84, height)
    far = _model_x(centre_model, height * 0.60, height)
    valid = bool(np.isfinite(near) and np.isfinite(far))
    if not valid:
        return {"valid": False, "lane": lane_side,
                "center_near": width * 0.5, "center_far": width * 0.5,
                "image_center": width * 0.5}

    uncertain = False
    if _LANE_TRACK is not None:
        lane_changed = lane_side != _LANE_TRACK["lane"]
        if lane_changed:
            # Each evaluated lap starts a fresh controller process, so the
            # lane identity must remain fixed for that run. At a tight bend
            # the visible outer edge can fragment and look like the opposite
            # lane; switching here reverses the steering direction.
            uncertain = True
            near = _LANE_TRACK["near"]
            far = _LANE_TRACK["far"]
            lane_side = _LANE_TRACK["lane"]

    _LANE_TRACK = {"lane": lane_side, "near": float(near),
                   "far": float(far)}
    return {"valid": True, "lane": lane_side, "center_near": float(near),
            "center_far": float(far), "image_center": width * 0.5,
            "uncertain": uncertain}


def compute_control(detection, stop_requested):
    '''
    Purpose:
    ---
    Turn the errors from detect_lane() into the three numbers the vehicle is
    driven with, and obey the stop flag.

    This is where your Task 1B controller and your Task 1A steering geometry
    meet: work out one steering angle from the error, then split it into the
    two front-wheel angles the joints actually take.

    Input Arguments:
    ---
    `detection` :   [ any ]
        Whatever detect_lane() returned for this frame.

    `stop_requested` :  [ bool ]
        True while the evaluation is holding the vehicle at a stop point.
        This is a LEVEL, not a pulse: it stays True for the whole duration of
        the stop and goes False when the wait is over. While it is True the
        vehicle must be STATIONARY, so return a speed of 0.0. There is no
        stopwatch for you to write and no duration to hard-code.

    Returns:
    ---
    `left_angle`, `right_angle` :   [ float ]
        The two front-wheel steering angles, in RADIANS, written straight to
        the steering joints. The scene's steering joints are POSITIVE TO THE
        LEFT. Nothing is clamped for you - the vehicle's own limit is 45
        degrees, and commanding past it will not steer any harder.

    `speed` :   [ float ]
        Target velocity for both drive motors, in rad/s. 0.0 holds the
        vehicle still.

    Example call:
    ---
    left_angle, right_angle, speed = compute_control(detection, stop_requested)

    REMEMBER:
    ---
    Keep the loop running while stopped - set the SPEED to zero, not your
    program. If you stop reading frames you will not see the flag drop.

    Sooner or later a frame comes back with nothing usable in it. Holding the
    last steering angle, easing off the throttle and stopping dead are all
    defensible - doing nothing is not.
    '''

    global _LAST_SPEED, _LAST_WHEELS, _INVALID_FRAMES

    if bool(stop_requested):
        return float(_LAST_WHEELS[0]), float(_LAST_WHEELS[1]), 0.0

    valid = isinstance(detection, dict) and detection.get("valid", False)
    if not valid:
        return _invalid_control()

    try:
        scale = max(float(detection["image_center"]) * 2.0, 1.0)
        near_error = (float(detection["center_near"]) -
                      float(detection["image_center"])) / scale
        far_error = (float(detection["center_far"]) -
                     float(detection["image_center"])) / scale
    except (KeyError, TypeError, ValueError, OverflowError):
        return _invalid_control()

    if not np.isfinite(near_error) or not np.isfinite(far_error):
        return _invalid_control()

    _INVALID_FRAMES = 0
    virtual_limit = _virtual_steering_limit()
    virtual = -2.05 * near_error - 1.35 * (far_error - near_error)
    virtual = float(np.clip(virtual, -virtual_limit, virtual_limit))
    left_angle, right_angle = _ackermann_angles(virtual)
    _LAST_WHEELS = (left_angle, right_angle)

    turn_fraction = min(abs(virtual) / virtual_limit, 1.0)
    _LAST_SPEED = 1.22 * (1.0 - 0.80 * turn_fraction)
    if turn_fraction > 0.55:
        _LAST_SPEED = min(_LAST_SPEED, 0.42 - 0.35 * (turn_fraction - 0.55))
    if bool(detection.get("uncertain", False)):
        _LAST_SPEED = min(_LAST_SPEED, 0.28)
    _LAST_SPEED = float(np.clip(_LAST_SPEED, 0.24, 1.22))
    return float(left_angle), float(right_angle), float(_LAST_SPEED)


_LAST_SPEED = 1.0
_LAST_WHEELS = (0.0, 0.0)
_INVALID_FRAMES = 0
_LANE_TRACK = None


def _invalid_control():
    global _LAST_SPEED, _INVALID_FRAMES, _LANE_TRACK
    _INVALID_FRAMES += 1
    if _INVALID_FRAMES >= 8:
        _LANE_TRACK = None
        _LAST_SPEED = 0.0
        return float(_LAST_WHEELS[0]), float(_LAST_WHEELS[1]), 0.0
    _LAST_SPEED = max(0.45, _LAST_SPEED * 0.72)
    return float(_LAST_WHEELS[0]), float(_LAST_WHEELS[1]), float(_LAST_SPEED)


def _lane_masks(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    yellow = cv2.inRange(hsv, (18, 105, 105), (43, 255, 255))
    white = cv2.inRange(hsv, (0, 0, 165), (179, 105, 255))
    kernel = np.ones((3, 3), np.uint8)
    yellow = cv2.morphologyEx(yellow, cv2.MORPH_CLOSE, kernel)
    white = cv2.morphologyEx(white, cv2.MORPH_OPEN, kernel)
    return yellow, white


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
        ys, xs = np.where(labels == index)
        if len(xs) < 20:
            continue
        points = np.column_stack((ys, xs)).astype(np.float32)
        model = _fit_point_model(points, mask.shape[0])
        model["score"] = float(area) * float(height)
        models.append(model)
    return models


def _dashed_line_points(mask, height, width):
    work = mask.copy()
    work[:int(height * 0.50)] = 0
    work[int(height * 0.87):] = 0
    count, labels, stats, _ = cv2.connectedComponentsWithStats(work, 8)
    points = []
    for index in range(1, count):
        x, y, component_width, component_height, area = stats[index]
        if area < 30 or component_height < 5 or component_width < 4:
            continue
        if component_width > width * 0.35:
            continue
        ys, xs = np.where(labels == index)
        points.append((float(np.mean(ys)), float(np.mean(xs)), float(area)))
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


def _choose_lane_pair(yellow_models, white_models, height, width):
    if not yellow_models or not white_models:
        return None
    reference = height * 0.78
    candidates = []
    for yellow_model in yellow_models:
        for white_model in white_models:
            outer = _model_x(yellow_model, reference, height)
            divider = _model_x(white_model, reference, height)
            width_px = abs(divider - outer)
            centre = 0.5 * (divider + outer)
            if not (np.isfinite(outer) and np.isfinite(divider)):
                continue
            if width * 0.16 <= width_px <= width * 0.96:
                centre_cost = abs(centre - width * 0.5) / width
                width_cost = abs(width_px - width * 0.67) / width
                score = centre_cost + 0.28 * width_cost
                candidates.append((score, yellow_model, white_model,
                                   "left" if outer < divider else "right"))
    if not candidates:
        return None
    candidates.sort(key=lambda item: item[0])
    _, outer_model, divider_model, side = candidates[0]
    return outer_model, divider_model, side


def _fit_point_model(points, height):
    points = np.asarray(points, dtype=np.float32)
    degree = min(2, len(points) - 1)
    yn = (points[:, 0] - height * 0.70) / max(height * 0.25, 1.0)
    coefficients = np.polyfit(yn, points[:, 1], degree)
    return {"coefficients": coefficients, "height": float(height)}


def _model_x(model, row, height):
    coefficients = model["coefficients"]
    yn = (float(row) - height * 0.70) / max(height * 0.25, 1.0)
    return float(np.polyval(coefficients, yn))


def _virtual_steering_limit():
    return float(np.arctan(0.120 / (0.120 + 0.055 / 2.0)) - 1e-3)


def _ackermann_angles(delta):
    wheelbase = 0.120
    effective_track = 0.110 - 2.0 * 0.0275
    sine, cosine = np.sin(delta), np.cos(delta)
    left = np.arctan2(2.0 * wheelbase * sine,
                       2.0 * wheelbase * cosine - effective_track * sine)
    right = np.arctan2(2.0 * wheelbase * sine,
                        2.0 * wheelbase * cosine + effective_track * sine)
    return float(left), float(right)


##############################################################
############## END OF YOUR IMPLEMENTATION ####################
##############################################################


#################### DO NOT EDIT BELOW THIS LINE ####################
#
# Connecting to the simulator, reading the camera and writing to the joints.
# None of it involves a decision you are being marked on - it is here so that
# every team reads the same picture and drives the same vehicle.
#
#####################################################################

def connect_and_locate():
    '''Open the remote API connection and look up every scene handle once.

    Each getObject() is a network round trip, which is why they all happen
    here rather than inside the loop.
    '''
    try:
        sim = RemoteAPIClient().getObject('sim')
        sim.getSimulationTime()
    except Exception as err:
        raise ConnectionError(
            f'Could not reach CoppeliaSim on the ZMQ Remote API port.\n'
            f'  Is CoppeliaSim running with Task_2A.ttt open?\n'
            f'  Simulator said: {err}')

    handles = {}
    for name, path in (('vision_sensor', VISION_SENSOR),
                       ('steer_left', STEER_LEFT),
                       ('steer_right', STEER_RIGHT),
                       ('motor_left', MOTOR_LEFT),
                       ('motor_right', MOTOR_RIGHT)):
        try:
            handles[name] = sim.getObject(path)
        except Exception as err:
            raise RuntimeError(
                f'No object at "{path}" in the open scene.\n'
                f'  Open Task_2A.ttt from the repository.\n'
                f'  Simulator said: {err}')
    return sim, handles


def read_frame(sim, handles):
    '''Grab one frame from the vehicle's camera as a BGR image.

    The vision sensor hands back a raw byte buffer and a resolution, not an
    image, and three corrections are needed to turn one into the other. None
    of these problems announces itself - each produces a detector that looks
    like it is working on a frame that is wrong:

      * handleVisionSensor() - this scene's sensor renders only when asked.
        Without it every read returns the SAME frame for the whole lap.
      * cv2.flip(frame, 0) - the buffer's first row is the BOTTOM of the
        image, so the road comes out vertically mirrored.
      * RGB2BGR - the buffer is RGB and OpenCV assumes BGR. Without the swap
        every HSV threshold you tuned in Task 1C selects the wrong colour.

    Note `res[1], res[0]` in the reshape too: the resolution comes back as
    (width, height) while NumPy wants rows first.

    Returns None if no frame is ready yet, which happens on the first few
    iterations after the simulation starts.
    '''
    sim.handleVisionSensor(handles['vision_sensor'])
    img, res = sim.getVisionSensorImg(handles['vision_sensor'], 0)
    if len(img) == 0:
        return None
    frame = np.frombuffer(img, dtype=np.uint8).reshape((res[1], res[0], 3))
    frame = cv2.flip(frame, 0)
    return cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)


def drive(sim, handles, left_angle, right_angle, speed):
    '''Write the two steering angles and the drive speed to the joints.'''
    sim.setJointTargetPosition(handles['steer_left'], float(left_angle))
    sim.setJointTargetPosition(handles['steer_right'], float(right_angle))
    sim.setJointTargetVelocity(handles['motor_left'], float(speed))
    sim.setJointTargetVelocity(handles['motor_right'], float(speed))


def main():
    sim, handles = connect_and_locate()

    # While you are developing you press Play yourself. Under evaluation the
    # harness resets the scene, places the vehicle in the lane being tested
    # and starts the simulation - so wait for that rather than starting your
    # own, which would race the harness into position.
    #
    # Your script must never call startSimulation(), stopSimulation() or move
    # the vehicle. Reading the camera and driving the joints is all it does.
    deadline = time.monotonic() + 120.0
    while sim.getSimulationState() != sim.simulation_advancing_running:
        if time.monotonic() > deadline:
            print('The simulation never started. Press Play in CoppeliaSim, '
                  'then run this script again.')
            return 1
        time.sleep(0.05)
    print('Simulation running - driving.')

    frames = 0
    try:
        # The harness stops the simulation when the lap is over, which is the
        # cue to exit - hence testing the state rather than looping forever.
        while sim.getSimulationState() == sim.simulation_advancing_running:
            frame = read_frame(sim, handles)
            if frame is None:
                continue
            frames += 1

            # getInt32Signal() returns None until the signal is first set, so
            # "not set" reads as "not stopping" and the first frames behave.
            stop_requested = bool(sim.getInt32Signal(STOP_SIGNAL))

            detection = detect_lane(frame)
            left_angle, right_angle, speed = compute_control(detection,
                                                             stop_requested)
            drive(sim, handles, left_angle, right_angle, speed)
    except KeyboardInterrupt:
        print('\nInterrupted.')
    except Exception as err:
        # A call raising because the simulation stopped mid-frame is normal at
        # the end of a run; anything else is a bug worth seeing.
        print(f'Loop ended: {type(err).__name__}: {err}')
    finally:
        # Without this, whatever speed was last commanded is still being
        # applied and the vehicle drives on unsteered.
        try:
            sim.setJointTargetVelocity(handles['motor_left'], 0.0)
            sim.setJointTargetVelocity(handles['motor_right'], 0.0)
        except Exception:
            pass

    print(f'{frames} frames processed.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
