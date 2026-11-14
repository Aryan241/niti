"""Offline controller checks; run with the project's Python environment."""
import importlib.util
import math
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / 'task2c' / 'task2c.py'


def fresh():
    spec = importlib.util.spec_from_file_location('parking_check', SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check():
    m = fresh()
    pose = dict(lateral=0.0, heading=0.0, forward=0.19, bearing=0.0)
    original = pose.copy()
    for i in range(8):
        steering, speed, parked = m.parking_manoeuvre(pose)
        assert speed == 0.0 and parked == (i == 7)
    assert pose == original

    # The old end pose must no longer count as successful parking.
    m = fresh()
    for _ in range(12):
        assert not m.parking_manoeuvre(dict(lateral=.02, heading=-.082,
                                           forward=.129, bearing=0.0))[2]

    for bad in (None, {}, {'lateral': float('nan'), 'heading': 0,
                          'forward': .3}, {'lateral': 'invalid'}):
        m = fresh()
        for _ in range(310):
            result = m.parking_manoeuvre(bad)
            assert all(math.isfinite(v) for v in result[:2])
            assert not result[2]
        assert result[1] == 0.0

    for lateral in (-.44, -.22, 0, .22, .44):
        for heading in (-.8, -.2, 0, .2, .8):
            m = fresh()
            steering, speed, parked = m.parking_manoeuvre(dict(
                lateral=lateral, heading=heading, forward=.8, bearing=-heading))
            wheels = m.ackermann_wheel_angles(steering)
            assert all(math.isfinite(v) and abs(v) <= math.pi / 4 for v in wheels)
            assert 0 <= speed <= 1.15 and not parked
    print('Task 2C: stable stop, old-pose rejection, malformed input, marker loss, wheel limits PASS')


if __name__ == '__main__':
    check()
