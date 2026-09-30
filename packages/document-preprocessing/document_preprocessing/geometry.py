"""Document boundary detection, perspective correction and rotation."""

from __future__ import annotations

import cv2
import numpy as np


def _order_quad(pts: np.ndarray) -> np.ndarray:
    pts = pts.reshape(4, 2).astype("float32")
    s = pts.sum(axis=1)
    d = np.diff(pts, axis=1).ravel()
    return np.array([pts[np.argmin(s)], pts[np.argmin(d)], pts[np.argmax(s)], pts[np.argmax(d)]], dtype="float32")


def detect_document_quad(rgb: np.ndarray, min_area_ratio: float = 0.25, max_area_ratio: float = 0.98) -> np.ndarray | None:
    """Return the 4 corners (tl, tr, br, bl) of the card if a convincing quadrilateral is found.

    Returns ``None`` when the card already fills the frame or no clean boundary exists –
    we then keep the image as-is rather than warping on a bad guess.
    """
    h, w = rgb.shape[:2]
    scale = 800 / max(h, w)
    small = cv2.resize(rgb, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA) if scale < 1 else rgb.copy()
    scale = min(scale, 1.0)
    gray = cv2.cvtColor(small, cv2.COLOR_RGB2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(gray, 50, 150)
    edges = cv2.dilate(edges, np.ones((3, 3), np.uint8), iterations=2)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    area_total = small.shape[0] * small.shape[1]
    best = None
    best_area = 0.0
    for c in sorted(contours, key=cv2.contourArea, reverse=True)[:8]:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        area = cv2.contourArea(approx)
        if len(approx) == 4 and cv2.isContourConvex(approx) and min_area_ratio * area_total < area < max_area_ratio * area_total:
            if area > best_area:
                best, best_area = approx, area
    if best is None:
        return None
    return _order_quad(best / scale)


def four_point_transform(rgb: np.ndarray, quad: np.ndarray) -> np.ndarray:
    tl, tr, br, bl = quad
    width = int(max(np.linalg.norm(br - bl), np.linalg.norm(tr - tl)))
    height = int(max(np.linalg.norm(tr - br), np.linalg.norm(tl - bl)))
    dst = np.array([[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]], dtype="float32")
    m = cv2.getPerspectiveTransform(quad.astype("float32"), dst)
    return cv2.warpPerspective(rgb, m, (width, height), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)


def estimate_skew_angle(rgb: np.ndarray, max_angle: float = 15.0) -> float:
    """Small-angle skew estimate (degrees, positive = counter-clockwise) from text-like strokes."""
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    scale = 1200 / max(gray.shape)
    if scale < 1:
        gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    bw = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 25, 15)
    # join characters into line blobs
    bw = cv2.morphologyEx(bw, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (25, 3)))
    contours, _ = cv2.findContours(bw, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    angles: list[float] = []
    weights: list[float] = []
    for c in contours:
        (cx, cy), (rw, rh), ang = cv2.minAreaRect(c)
        if rw < rh:
            rw, rh = rh, rw
            ang = ang - 90
        if rw < 40 or rw / max(rh, 1) < 4:
            continue
        if ang < -45:
            ang += 90
        if ang > 45:
            ang -= 90
        if abs(ang) <= max_angle:
            angles.append(ang)
            weights.append(rw)
    if len(angles) < 3:
        return 0.0
    order = np.argsort(angles)
    a = np.array(angles)[order]
    wts = np.array(weights)[order]
    cum = np.cumsum(wts)
    median = float(a[np.searchsorted(cum, cum[-1] / 2)])
    # OpenCV minAreaRect angle is clockwise-positive in image coordinates.
    return -median


def rotate_bound(rgb: np.ndarray, angle: float) -> np.ndarray:
    """Rotate counter-clockwise by ``angle`` degrees keeping the full image."""
    h, w = rgb.shape[:2]
    m = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
    cos, sin = abs(m[0, 0]), abs(m[0, 1])
    nw, nh = int(h * sin + w * cos), int(h * cos + w * sin)
    m[0, 2] += nw / 2 - w / 2
    m[1, 2] += nh / 2 - h / 2
    return cv2.warpAffine(rgb, m, (nw, nh), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)


def rotate_quadrant(rgb: np.ndarray, degrees_cw: int) -> np.ndarray:
    k = (degrees_cw // 90) % 4
    if k == 0:
        return rgb
    codes = {1: cv2.ROTATE_90_CLOCKWISE, 2: cv2.ROTATE_180, 3: cv2.ROTATE_90_COUNTERCLOCKWISE}
    return cv2.rotate(rgb, codes[k])
