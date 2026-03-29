"""
3D math utilities: matrices, vectors, projection.

All functions use float32 numpy arrays for direct use with OpenGL uniforms.
The coordinate system matches the original demo's convention:
  X right, Y up, Z toward viewer (right-hand).
"""

import math
import numpy as np


def identity() -> np.ndarray:
    return np.eye(4, dtype=np.float32)


def translation(tx: float, ty: float, tz: float) -> np.ndarray:
    m = np.eye(4, dtype=np.float32)
    m[0, 3] = tx
    m[1, 3] = ty
    m[2, 3] = tz
    return m


def scale(sx: float, sy: float, sz: float) -> np.ndarray:
    m = np.eye(4, dtype=np.float32)
    m[0, 0] = sx
    m[1, 1] = sy
    m[2, 2] = sz
    return m


def rot_x(angle_rad: float) -> np.ndarray:
    c, s = math.cos(angle_rad), math.sin(angle_rad)
    m = np.eye(4, dtype=np.float32)
    m[1, 1] =  c;  m[1, 2] = -s
    m[2, 1] =  s;  m[2, 2] =  c
    return m


def rot_y(angle_rad: float) -> np.ndarray:
    c, s = math.cos(angle_rad), math.sin(angle_rad)
    m = np.eye(4, dtype=np.float32)
    m[0, 0] =  c;  m[0, 2] =  s
    m[2, 0] = -s;  m[2, 2] =  c
    return m


def rot_z(angle_rad: float) -> np.ndarray:
    c, s = math.cos(angle_rad), math.sin(angle_rad)
    m = np.eye(4, dtype=np.float32)
    m[0, 0] =  c;  m[0, 1] = -s
    m[1, 0] =  s;  m[1, 1] =  c
    return m


def perspective(fovy_deg: float, aspect: float,
                near: float = 0.1, far: float = 1000.0) -> np.ndarray:
    """Standard perspective projection matrix (column-major, OpenGL convention)."""
    f = 1.0 / math.tan(math.radians(fovy_deg) / 2.0)
    m = np.zeros((4, 4), dtype=np.float32)
    m[0, 0] = f / aspect
    m[1, 1] = f
    m[2, 2] = (far + near) / (near - far)
    m[2, 3] = (2 * far * near) / (near - far)
    m[3, 2] = -1.0
    return m


def look_at(eye: np.ndarray, target: np.ndarray,
            up: np.ndarray) -> np.ndarray:
    f = normalise(target - eye)
    r = normalise(np.cross(f, up))
    u = np.cross(r, f)
    m = np.eye(4, dtype=np.float32)
    m[0, :3] = r
    m[1, :3] = u
    m[2, :3] = -f
    m[0, 3] = -np.dot(r, eye)
    m[1, 3] = -np.dot(u, eye)
    m[2, 3] =  np.dot(f, eye)
    return m


def normalise(v: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(v)
    return v / n if n > 1e-12 else v


def mat_mul(*mats: np.ndarray) -> np.ndarray:
    """Left-to-right matrix multiplication (first transform applied first)."""
    result = mats[0]
    for m in mats[1:]:
        result = result @ m
    return result


def vec3(x: float, y: float, z: float) -> np.ndarray:
    return np.array([x, y, z], dtype=np.float32)


def vec4(x: float, y: float, z: float, w: float = 1.0) -> np.ndarray:
    return np.array([x, y, z, w], dtype=np.float32)
