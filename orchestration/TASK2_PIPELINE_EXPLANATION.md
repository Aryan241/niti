# Task 2A, 2B, and 2C Pipeline Explanation

Our three tasks use three different methods:

| Task | Input | Our method | Output |
|---|---|---|---|
| **2A: lane navigation** | Live camera frames and a stop signal | Colour segmentation, curve fitting, steering feedback | Two wheel angles and motor speed |
| **2B: sign and obstacle detection** | Individual images | Colour segmentation, shape tests, template matching | Sign labels/areas and obstacle presence/area |
| **2C: parking** | Camera-derived position relative to an ArUco marker | Smooth approach path, steering feedback, alignment checks | Steering, speed, and a “parked” flag |

These are **separate submissions**, not one integrated driving program. Task 2C does not call our 2A lane detector or 2B sign detector.

## Task 2A — Seeing the lane and steering through it

Current code: `task2a/task2a.py`.

The objective is to stay near the middle of the assigned lane, complete a lap, and remain stationary whenever the evaluator raises `NV_stop`.

The core idea is:

```text
Camera image
    ↓
Find yellow road boundary and white dashed divider
    ↓
Fit curves to those markings
    ↓
Estimate the lane centre near and ahead of the vehicle
    ↓
Calculate steering and choose speed
    ↓
Convert steering into separate left/right wheel angles
    ↓
Drive, receive next image, repeat
```

### 1. The supplied camera code prepares each image

The simulator supplies raw camera bytes. The provided `read_frame()` does three necessary things:

1. Requests a fresh sensor render with `handleVisionSensor()`.
2. Reshapes the bytes into an image and flips it vertically.
3. Converts RGB into OpenCV’s BGR channel order.

Without these corrections, we could repeatedly process an old frame, see an upside-down road, or threshold the wrong colours.

Our detector therefore receives an ordinary BGR image.

### 2. `detect_lane()` checks that the input is usable

The function expects a NumPy array with three colour channels.

If that structure is wrong, it returns a dictionary with:

```python
{"valid": False, ...}
```

This separates perception from control: the detector reports that it cannot see a usable lane, and the controller chooses how to respond.

For normal images, it reads:

```python
height, width = frame.shape[:2]
```

Most geometric calculations use fractions of these dimensions.

### 3. `_lane_masks()` separates yellow and white pixels

We convert BGR into HSV:

- **Hue:** which colour.
- **Saturation:** how colourful versus grey.
- **Value:** brightness.

HSV makes it straightforward to isolate yellow paint and bright, low-saturation white paint.

The actual thresholds are:

```python
yellow: H 18–43, S 105–255, V 105–255
white:  H 0–179, S 0–105, V 165–255
```

Each output is a binary image: selected pixels are white; everything else is black.

We then apply a small `3 × 3` morphological operation:

- **Closing on yellow:** fills small gaps in a continuous boundary.
- **Opening on white:** removes small isolated specks.

These masks are candidates, not yet confirmed road markings. A white building could also pass a white threshold.

### 4. Find candidate yellow boundaries

`_solid_line_models()` processes the yellow mask.

It only keeps rows between approximately **42% and 90% of image height**. That avoids much of the distant background and the very bottom of the frame.

It finds connected components—groups of touching yellow pixels—and rejects small components:

```text
minimum area = 180 pixels
minimum height = 32 pixels
```

For each surviving component, it gathers the pixel coordinates and fits a curve.

The model represents:

```text
horizontal position x = function of image row y
```

This orientation is useful because we want to ask:

> At this particular distance down the image, where is the road boundary?

A quadratic curve can follow a bend better than a straight-line model.

The model normalizes the vertical coordinate before fitting:

\[
u=\frac{y-0.70H}{0.25H}
\]

Then it fits approximately:

\[
x(u)=au^2+bu+c
\]

Normalization keeps the fitting coordinates reasonably scaled.

There is also an `area × height` score attached to these models, but the current pair-selection function does **not** use that stored score.

### 5. Find the white dashed divider

White dashes are disconnected by design, so we handle them differently.

`_dashed_line_points()`:

- Keeps rows between **50% and 87%** of image height.
- Finds connected white components.
- Rejects components that are too small.
- Rejects components wider than **35% of the image**.
- Represents each surviving component by its centre.

Instead of fitting every white pixel, we fit through the centres of the likely dashes.

`_dashed_line_models()` tries up to three models:

1. All candidate dash centres.
2. Centres on the left portion of the image.
3. Centres on the right portion.

The left/right regions overlap slightly. This provides alternatives when unrelated white objects would distort a fit through all points.

This is heuristic candidate generation, not a robust estimator such as RANSAC.

### 6. Choose the most plausible boundary/divider pair

`_choose_lane_pair()` tries every yellow model against every white model.

At row `0.78 × height`, it calculates:

```python
lane_width = abs(divider_x - boundary_x)
lane_center = (divider_x + boundary_x) / 2
```

It rejects pairs whose apparent width is outside:

```text
16% to 96% of image width
```

Then it scores the remaining pairs:

\[
\text{score}
=
\frac{|c-W/2|}{W}
+
0.28\frac{|w_{\text{lane}}-0.67W|}{W}
\]

This favours:

- A lane whose middle is reasonably near the image centre.
- A plausible apparent lane width.

The lowest-scoring pair wins.

The stored `"left"`/`"right"` label describes whether the yellow boundary is left or right of the divider in the image. It is not a world-coordinate lane identifier.

### 7. Estimate the lane centre at multiple distances

For the selected boundary and divider, the code averages their positions at three rows:

```python
0.62 * height
0.74 * height
0.84 * height
```

At each row:

\[
x_{\text{centre}}=\frac{x_{\text{yellow}}+x_{\text{divider}}}{2}
\]

It fits a centre curve through these points, then extracts:

```python
center_near = centre at 84% image height
center_far  = centre at 60% image height
```

These answer two different questions:

- **Near centre:** Where should I be positioned now?
- **Far centre:** Where is the lane heading ahead?

That second measurement lets the controller anticipate a bend rather than react only after drifting sideways.

### 8. Keep the lane identity consistent

`_LANE_TRACK` remembers the previous lane side and centre measurements.

If a new frame suddenly says the boundary/divider ordering has flipped, the code:

- Keeps the previous near/far estimates.
- Keeps the previous lane identity.
- Marks the detection `uncertain=True`.

The reason is that the evaluator starts a fresh controller process for each lap. During one lap, an apparent lane switch is more likely to be a perception mistake than a legitimate change of lane.

This protects against fragmented markings on tight bends causing a sudden steering reversal.

The limitation is that this is a consistency rule, not proof the previous estimate was correct. It can preserve an incorrect initial choice.

### 9. `compute_control()` gives stopping highest priority

The first decision is:

```python
if stop_requested:
    return previous_left_angle, previous_right_angle, 0.0
```

The vehicle keeps its steering orientation but commands zero motor speed.

The loop continues reading frames and checking the signal. When `NV_stop` becomes false, normal driving resumes.

**We do not detect designated stopping locations ourselves in 2A.** The evaluator knows the stop locations and raises the flag. Our responsibility is to obey it continuously.

### 10. Convert lane positions into steering error

The detector returns positions in pixels. The controller normalizes them by image width:

\[
e_n=\frac{x_{\text{near}}-W/2}{W}
\]

\[
e_f=\frac{x_{\text{far}}-W/2}{W}
\]

Positive error means the desired centre is to the right of the image centre.

Our steering formula is:

\[
\delta=-2.05e_n-1.35(e_f-e_n)
\]

The two terms have distinct purposes:

- `-2.05 × near_error`: correct current lateral displacement.
- `-1.35 × (far_error - near_error)`: respond to how the lane bends ahead.

The minus signs matter because the simulator’s **positive steering turns left**.

For example:

```text
Near centre: 20 pixels right
Far centre: 60 pixels right
Image width: 640 pixels
```

Then:

```text
near error = 20/640 = 0.03125
far error  = 60/640 = 0.09375
```

The steering becomes approximately:

```text
-0.148 radians ≈ -8.5 degrees
```

Negative means steer right.

This is a proportional geometric controller with an ahead-looking term. It is **not a full PID controller**: there is no accumulated integral error or time derivative.

### 11. Split virtual steering into two wheel angles

A car’s front wheels should not turn by identical angles during a bend. The wheel on the inside follows a tighter circle.

We use Ackermann geometry with:

```text
Wheelbase L = 0.120 m
Effective steering width T = 0.110 − 2 × 0.0275 = 0.055 m
```

For virtual steering angle \(\delta\):

\[
\delta_L=
\operatorname{atan2}
(2L\sin\delta,\ 2L\cos\delta-T\sin\delta)
\]

\[
\delta_R=
\operatorname{atan2}
(2L\sin\delta,\ 2L\cos\delta+T\sin\delta)
\]

The virtual steering limit is approximately **39°**, chosen so the more sharply turned physical wheel stays below its approximately **45°** limit.

### 12. Slow down as steering increases

The controller computes the fraction of maximum steering being used:

```python
turn_fraction = abs(virtual) / virtual_limit
```

The basic speed rule is:

```python
speed = 1.22 * (1 - 0.80 * turn_fraction)
```

It adds further slowing for tight turns and uncertain detections.

Normal valid-frame speed is clamped between:

```text
0.24 and 1.22 rad/s
```

These are **motor angular speeds**, not metres per second.

The purpose is simple: a tight turn gives the visual controller less room for error, so the vehicle advances more slowly.

### 13. Handle missing lane detections

`_invalid_control()` remembers how many consecutive detections were invalid.

For the first seven invalid frames:

- Hold the last wheel angles.
- Update speed using:

```python
max(0.45, previous_speed * 0.72)
```

At eight invalid frames:

- Stop.
- Clear the stored lane track so it can be reacquired.

An important detail: the `0.45` floor means this is **not always deceleration**. If the previous speed was below `0.45`, it increases to `0.45` during this fallback. Also, eight frames is a frame count, not a fixed duration.

Those are limitations of the current implementation worth understanding.

### 14. What the evaluator measures

It drives one outer and one inner lap, recording the vehicle trajectory and stop flags.

From the submission page:

- Lane holding: **26 marks**.
- Stops: **6 marks**.
- Lap completion: **8 marks**.
- Outer lane weight: **40%**.
- Inner lane weight: **60%**.

Our latest recorded run completed both laps and triggered both stops on each lap. That establishes usable recordings, not a guaranteed lane-centering score.

## Task 2B — Classifying signs and detecting the obstacle

Current code: `task2b/sign_obstacle_detection.py`.

This task is image analysis only. It does not steer or stop the robot.

For each image, we return:

```python
[
    {"label": "Parking", "area": 2552},
    {"label": "Speed40", "area": 1238},
]
```

and separately:

```python
{"present": True, "area": 4536}
```

Our approach is **classical computer vision**. There is no trained neural network.

```text
Image
 ├─ Red components
 │   ├─ White interior + triangular outline → School
 │   ├─ White interior + other accepted outline → Speed40
 │   └─ Little white interior → obstacle candidate
 │
 └─ Blue components
     └─ Extract white symbol → compare P and H templates
```

### 1. `_colour_components()` finds coloured objects

The function converts the image into HSV and thresholds either red or blue.

Red uses two hue intervals:

```python
H 0–14
H 166–179
```

This is because red wraps around the ends of OpenCV’s hue scale.

Both red intervals require:

```text
Saturation ≥ 80
Brightness ≥ 50
```

Blue uses:

```text
Hue 85–145
Saturation ≥ 60
Brightness ≥ 30
```

Unlike 2A, this helper does not apply morphological opening or closing.

### 2. Describe each connected component

For every connected coloured region, the helper calculates:

- Bounding box.
- Binary component mask.
- Number of coloured pixels.
- External contour.
- Contour area.
- Solidity.

Two areas are deliberately different:

**Pixel area** counts only selected coloured pixels.

**Contour area** measures the area enclosed by the outer outline.

For a red-bordered sign with a white middle, counting red pixels alone would mostly measure the border. The external contour gives an estimate of the complete sign face.

The reported detection area uses rounded contour area, not bounding-box area.

### 3. Solidity filters irregular blobs

Solidity is:

\[
\text{solidity}
=
\frac{\text{contour area}}{\text{convex hull area}}
\]

A convex hull is the smallest convex outline enclosing the contour.

A clean triangle, circle, or rectangle tends to have high solidity. An irregular or deeply indented blob has lower solidity.

This helps reject coloured scenery that does not resemble a sign or obstacle.

It is a shape-quality test, not a complete object classifier.

### 4. Red sign candidates need a white interior

For red sign detection, the code requires:

```text
Contour area ≥ 650
Solidity ≥ 0.88
White interior ratio ≥ 0.10
```

`_white_ratio_inside()` fills the external contour, thresholds white pixels, and measures how much white lies inside it.

This is how we distinguish:

- A red border surrounding a white sign face.
- A mostly solid red obstacle.

The white threshold here is:

```text
Saturation ≤ 105
Brightness ≥ 150
```

The ratio is calculated using white-pixel count divided by contour area, so it is an approximate occupancy measurement rather than a mathematically exact fraction of identical pixel sets.

### 5. Distinguish School from Speed40 by outline

The contour is simplified:

```python
polygon = cv2.approxPolyDP(contour, 0.04 * perimeter, True)
```

This replaces a detailed pixel contour with a smaller polygon.

Then:

```python
label = "School" if len(polygon) == 3 else "Speed40"
```

So:

- Three vertices → triangular School sign.
- Any other accepted red/white shape → Speed40.

**The code does not read the digits “40” and does not recognize the school pictogram.**

It relies on the task’s limited sign vocabulary and shape/colour conventions. That makes it simple and fast, but a different red-bordered, non-triangular object could be incorrectly labelled Speed40.

### 6. Filter blue sign candidates

Parking and Hospital signs are both blue, so colour alone cannot distinguish them.

Before examining their symbols, we require:

```text
Blue pixel area ≥ 500
Top of component at least 5 pixels below image top
Top of component above 75% image height
Bounding-box width/height between 0.80 and 1.35
```

These filters reject tiny patches, some image-edge regions, and shapes that are far from roughly square.

They are useful for the task images, but the absolute pixel thresholds and position assumptions can reject very small, heavily tilted, or unusually placed signs.

### 7. Normalize the blue sign into a 64 × 64 image

`_rectified_white_mask()`:

1. Finds the component’s external contour.
2. Fits a minimum-area rotated rectangle.
3. Orders its corners.
4. Warps that rectangle into a `64 × 64` square.
5. Thresholds the white symbol.

Now a large nearby P and a small distant P are compared at the same size.

The corner ordering is:

```text
top-left → top-right → bottom-right → bottom-left
```

One distinction matters: the corners come from a **minimum-area rectangle**, not an explicitly detected four-corner perspective quadrilateral. The normalization handles rotation and scale, but it is not a complete correction for every strong perspective distortion.

### 8. Load the P and H reference templates

At module import time:

```python
_PARKING_TEMPLATE
_HOSPITAL_TEMPLATE
```

are created from:

```text
reference_images/P.jpg
reference_images/Hospital.png
```

The reference images go through the same blue-region extraction and white-symbol normalization.

This makes the comparison consistent: candidate and reference are both white-symbol masks.

If a reference cannot be loaded, the code falls back to a small hand-written binary P or H pattern enlarged to `64 × 64`.

The official submission page says not to include `reference_images/` because the grader supplies the same folder beside the submitted script.

### 9. Compare candidate and template

`_template_score()` uses:

```python
cv2.matchTemplate(
    symbol,
    template,
    cv2.TM_CCOEFF_NORMED
)
```

This is normalized correlation: it measures how similarly the white patterns are arranged after accounting for their mean intensity.

Since both arrays are `64 × 64`, there is one comparison score. It is not sliding a small template around a large image.

The code rejects a candidate if:

```python
parking_score < 0.045 and hospital_score < 0.075
```

Otherwise, the higher score determines the label:

```python
Parking if parking_score >= hospital_score else Hospital
```

These scores are similarity measurements, **not probabilities**. A score of `0.8` does not mean “80% confidence.”

### 10. Return every detected sign

The red and blue results are added to one list.

That supports images containing multiple signs, such as Parking and Speed40 together.

The results are sorted by label and area for consistent output. Sorting does not affect the official set-based label matching.

### 11. Detect the obstacle separately

`detect_obstacle()` searches the red components again.

It accepts candidates with:

```text
Contour area ≥ 700
Solidity ≥ 0.85
White interior ratio < 0.10
```

That last condition is the opposite of the red-sign test.

If multiple candidates survive, it selects the one with the largest contour area.

If none survive:

```python
{"present": False, "area": 0}
```

Otherwise:

```python
{"present": True, "area": rounded_contour_area}
```

This detects the task’s red obstacle appearance. It is not a general-purpose detector for pedestrians, cars, arbitrary boxes, or every object blocking a road.

### 12. Validate output types

The supplied validators check things such as:

- Sign results are a list.
- Every entry is a dictionary.
- Labels belong to the allowed four classes.
- Areas have valid numeric structure.
- Obstacle presence is Boolean.
- An absent obstacle has zero area.

They catch interface mistakes. They do not establish whether the objects were correctly detected.

### 13. Why this method fits—and where it can fail

It uses the strong visual structure of this task:

- A small, fixed set of labels.
- Distinctive red/blue sign colours.
- Different outlines for the red signs.
- Supplied references for P and H.
- A distinctive obstacle colour.

That avoids needing labelled training data or model weights.

Its weaknesses are equally concrete:

- Fixed colour thresholds can fail under different lighting.
- Absolute area thresholds can miss small objects.
- Fragmented borders can split a single object into components.
- Strong perspective changes can hurt template similarity.
- Unrelated red/blue objects can pass the filters.
- Private images can expose cases absent from the public set.

The latest public evaluation processed all 11 supplied images without errors and produced sensible labels and obstacle detections. It did not measure accuracy against the private set.

The submission page allocates:

- Sign labels: **15 marks**.
- Sign areas: **10 marks**.
- Obstacle presence: **10 marks**.
- Obstacle areas: **5 marks**.

Area errors within **15%** receive full credit; within **35%**, half credit.

## Task 2C — Approaching a bay and parking straight

Current code: `task2c/task2c.py`.

Here, the challenge is not simply to drive toward a marker. The vehicle must arrive:

- Inside the correct bay.
- Near its centre line.
- Parallel to the bay.
- At rest.

Pointing directly at a marker can leave the vehicle diagonally across a narrow bay. Our method instead generates a smooth sideways approach and then tightens alignment before stopping.

```text
Camera image
    ↓
Find target ArUco marker
    ↓
Supplied estimator computes relative position and heading
    ↓
Our controller builds a smooth approach reference
    ↓
Combine predicted curve steering with position/heading corrections
    ↓
Slow down, align, verify position across several frames
    ↓
Stop and report parked
```

### 1. Select the target marker

The scene uses ArUco marker IDs:

```text
0 → bay 0
1 → bay 1
```

The supplied detector uses `DICT_4X4_50`.

The evaluator runs the script with:

```text
--bay 0
--bay 1
```

This overrides the default `TARGET_ID`, which is currently `1`.

Our parking function uses the measured pose rather than a separate hard-coded manoeuvre for each bay. A larger starting lateral offset naturally asks for more sideways movement.

### 2. The supplied estimator turns marker corners into a pose

This part is boilerplate, not our parking implementation.

ArUco detection produces the four image corners of the chosen marker. The estimator knows:

```text
Image size: 640 × 480
Horizontal camera FOV: 95°
Camera downward pitch: 30°
Marker pattern size: 0.096 m
Camera forward offset from vehicle centre: 0.047 m
```

With known marker dimensions and camera geometry, `solvePnPGeneric()` estimates the marker’s orientation and distance.

It uses `SOLVEPNP_IPPE_SQUARE`, suited to square planar markers.

### 3. Resolve noisy or ambiguous heading estimates

A nearly front-facing square can produce two plausible pose solutions.

The supplied estimator:

- Sorts solutions by reprojection error.
- Only trusts the yaw measurement when one solution is sufficiently better.
- Smooths range using:

```python
filtered_range = 0.6 * previous_range + 0.4 * measured_range
```

It also predicts heading change from the previous steering command and estimated distance travelled:

\[
\Delta\theta\approx\frac{\tan\delta}{L}\Delta s
\]

A sufficiently consistent visual yaw measurement then corrects that prediction by a small fraction:

```text
Yaw correction blend: 0.12
Yaw acceptance gate: 15°
```

This combines geometry-based prediction with camera correction. It is not a Kalman filter.

### 4. What our `parking_manoeuvre()` receives

The estimator returns:

```python
{
    "lateral": ...,
    "heading": ...,
    "forward": ...,
    "bearing": ...,
}
```

| Field | Meaning |
|---|---|
| `lateral` | Front axle’s sideways offset from the bay centre line; positive means left |
| `heading` | Vehicle angle relative to the bay axis; positive means turned left |
| `forward` | Distance along the bay axis from vehicle centre to marker line |
| `bearing` | Where the marker appears horizontally relative to the camera; positive means left |

`forward` is **not distance remaining to the desired stopping point**.

The desired stopping location is:

```python
BAY_MIDDLE_FORWARD = 0.19
```

So a forward value of `0.19 m` means we are at the intended bay-middle position, not still 19 cm away from parking.

If the marker is not detected, the function receives `None`.

### 5. Store state between frames

The controller remembers:

- Last valid pose.
- Last steering and speed.
- Consecutive missing-marker frames.
- Consecutive good parking frames.
- Initial lateral offset.
- Initial forward distance.

The initial pose defines the approach path. Later frames provide feedback about whether the car is actually following it.

### 6. Handle missing or invalid pose data

Before the first valid pose, the fallback is:

```python
steering = -0.24
speed = 0.38
```

This slowly turns right to seek the bay marker.

After previously seeing the marker:

- Steering gradually decays toward straight.
- Speed is kept between `0.16` and `0.36 rad/s`.
- At 300 consecutive missing frames, it stops.

Malformed values and NaN/infinity are handled as missing detections.

This recovery is heuristic. In particular, 300 frames is not a fixed time interval, and the vehicle can still move during a prolonged marker loss.

There is also a missing-marker branch that returns parked when at least eight good frames were already accumulated. Under the normal loop, the valid-pose branch already returns parked at eight, so that extra branch is largely redundant.

### 7. Adjust lateral error for heading

The input lateral position refers to the front axle.

The code calculates:

```python
lateral_error = lateral - WHEELBASE * np.sin(heading)
```

This converts it into a rear-axle-like tracking quantity using the wheelbase and heading.

Why adjust it?

When a car is angled, its front axle and rear axle have different sideways positions. A steering controller should not treat those positions as interchangeable.

The final parking checks still use the original `lateral` measurement.

### 8. Build a smooth sideways approach

We aim to finish most sideways movement **before entering the narrow bay**.

The path’s nominal alignment point is:

```python
path_end_forward = BAY_MOUTH_FORWARD + 0.13
                 = 0.50 m
```

The bay mouth is at `0.37 m`, so this point is 13 cm before it.

The code computes a normalized progress variable:

\[
r=
\operatorname{clip}
\left(
\frac{f-f_{\text{end}}}{\text{path span}},
0,1
\right)
\]

where `f` is current forward distance.

Typically:

- Start of approach: \(r\approx1\).
- Alignment point: \(r=0\).

Then it uses the smoothstep polynomial:

\[
s(r)=3r^2-2r^3
\]

The desired sideways position is:

\[
l_{\text{ref}}=l_{\text{start}}s(r)
\]

This has a useful property: its slope is zero at both endpoints.

That means the intended path begins and ends parallel to the bay axis, with the sideways transition happening between them.

### 9. Derive the desired heading and curvature

The path slope is:

\[
l'=
\frac{l_{\text{start}}(6r-6r^2)}{\text{path span}}
\]

The desired heading is:

\[
\theta_{\text{ref}}=-\arctan(l')
\]

For a bay to our right, this creates a rightward approach angle during the middle of the transition, then returns toward zero heading.

The second derivative provides curvature:

\[
\kappa=\frac{l''}{(1+(l')^2)^{3/2}}
\]

From bicycle-model geometry, the steering needed to follow that curvature is approximately:

\[
\delta_{\text{feedforward}}=\arctan(L\kappa)
\]

“Feedforward” means steering predicted from the planned curve, before considering tracking errors.

### 10. Add feedback corrections

The full steering command is:

\[
\delta=
\arctan(L\kappa)
+
K_h(\theta_{\text{ref}}-\theta)
-
K_l(l_{\text{error}}-l_{\text{ref}})
\]

Each piece has a role:

1. **Curve term:** steering that should follow the reference path.
2. **Heading term:** correct pointing direction.
3. **Lateral term:** correct sideways displacement.

The gains change with distance:

| Region | Lateral gain | Heading gain |
|---|---:|---:|
| Before the alignment point | 7.0 | 2.8 |
| Closer than `forward = 0.50 m` | 45.0 | 4.0 |

Far away, the controller follows the gradual approach.

Near the bay, it strongly prioritizes small lateral and heading errors.

This is a geometric path-following controller with feedback. It does not perform trajectory optimization or model predictive control.

### 11. Keep the marker within a useful viewing angle

Large turns can push the marker outside the camera view.

The controller therefore modifies steering when:

```text
Heading magnitude exceeds 0.65 rad ≈ 37°
Bearing magnitude exceeds 0.42 rad ≈ 24°
```

These corrections encourage a less extreme heading or bring the marker back toward a safer viewing direction.

They are soft corrective rules, not a guarantee that the marker cannot disappear.

Finally, steering is clipped to the Ackermann-compatible virtual limit, approximately 39°.

### 12. Check whether the vehicle fits

The bay width is `0.22 m`; vehicle width is approximately `0.18 m`.

The nominal clearance on each side is:

\[
\frac{0.22-0.18}{2}=0.02\text{ m}
\]

That is only **20 mm per side**.

The controller subtracts a 4 mm margin, leaving a 16 mm allowance for its estimated footprint error:

```python
footprint_error = abs(lateral) + WHEELBASE * abs(sin(heading))
strictly_inside = footprint_error <= 0.016
```

This combines sideways offset and the additional sideways spread caused by an angled vehicle.

It is an **approximate footprint test**, not an exact calculation of every corner of the full vehicle body. The portal uses its own surveyed geometry to judge actual containment.

### 13. Require precise alignment and position

The separate alignment test is:

```python
abs(lateral) <= 0.008
abs(heading) <= 0.035
```

That means:

- Within **8 mm** laterally.
- Within approximately **2°** of straight.

The target position test is:

```python
abs(forward - 0.19) <= 0.008
```

That means within **8 mm** of the intended longitudinal position.

All three conditions must hold:

```text
Estimated footprint inside
AND aligned
AND at target distance
```

### 14. Stop first, then confirm across eight frames

When all conditions first become true, speed is commanded to zero.

The controller does not immediately report success. It requires **eight consecutive valid frames** satisfying the conditions.

Then it returns:

```python
0.0, 0.0, True
```

This reduces the chance that one noisy pose estimate falsely declares successful parking.

However, the function has no measured velocity input. Eight good frames confirm stable estimated pose; they do not independently prove zero physical speed. The evaluator records the actual subsequent motion.

### 15. Reduce speed as the target approaches

The base speed schedule is:

| Forward distance | Motor speed |
|---|---:|
| More than `0.43 m` | `1.15 rad/s` |
| `0.33–0.43 m` | `0.80 rad/s` |
| `0.235–0.33 m` | `0.65 rad/s` |
| Closer | `0.30 rad/s` |

Inside `0.225 m`, speed becomes proportional to remaining distance:

```python
speed = clip(9 * (forward - 0.19), 0.08, 0.30)
```

It also slows when:

- Alignment is poor.
- Steering is close to its limit.

This lets the vehicle make final corrections without charging past the target.

### 16. Stop if it overshoots

If:

```python
forward < 0.19 - 0.008
```

the controller returns zero steering and speed, but `parked=False`.

That prevents continuing farther forward and falsely claiming success.

There is no reversing recovery in the current manoeuvre. If it overshoots while misaligned, it can remain stopped until the evaluator ends the run.

This is one reason a forward-only parking controller must complete alignment early.

### 17. The supplied code applies the command

The boilerplate:

1. Splits virtual steering into Ackermann wheel angles.
2. Commands the two steering joints.
3. Commands both drive motors.
4. Reads the next camera frame.
5. Repeats.

When `parked=True`, it commands zero speed and exits its control loop.

The evaluator runs both bays separately and records their trajectories.

### 18. What the evaluator grades

From the submission instructions, each bay is evaluated for:

- Entire vehicle inside the correct bay: **8 marks**.
- Centred and straight: **8 marks**.
- Stopped cleanly: **4 marks**.

Then:

```text
Bay 0 contributes 70%
Bay 1 contributes 30%
```

Both existing recordings say `parked: 1` and correspond to the current script hash. That tells us the controller reached its success condition in those recordings. The portal still decides whether the actual vehicle footprint and alignment deserve full credit.

The main distinction across the three methods is: **2A estimates where the road goes, 2B classifies what is visible, and 2C uses marker-relative geometry to control a precise final position.**
