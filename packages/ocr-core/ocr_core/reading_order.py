"""Reading-order reconstruction and block grouping.

1. Lines are clustered into *blocks* (union-find on vertical proximity + horizontal overlap), so
   side-by-side columns (message | address, contacts | address) are not interleaved.
2. Blocks are ordered top-to-bottom; blocks whose vertical extents overlap form a band that is
   read right-to-left when the page is predominantly RTL, otherwise left-to-right.
3. Inside a block, lines are ordered top-to-bottom; lines on the same row follow the row's
   dominant direction.
"""

from __future__ import annotations

import math
import statistics

from shared_types import BBox, Direction, OcrLine


def _v_overlap(a: BBox, b: BBox) -> float:
    top = max(a.y, b.y)
    bot = min(a.y2, b.y2)
    return max(0.0, bot - top) / max(1.0, min(a.h, b.h))


def _h_overlap(a: BBox, b: BBox, slack: float) -> bool:
    return a.x - slack <= b.x2 and b.x - slack <= a.x2


def _rtl_weight(lines: list[OcrLine]) -> bool:
    rtl = sum(len(l.text) for l in lines if l.direction == Direction.rtl)
    ltr = sum(len(l.text) for l in lines if l.direction == Direction.ltr)
    return rtl > ltr


def _order_rows(lines: list[OcrLine]) -> list[OcrLine]:
    rows: list[list[OcrLine]] = []
    for ln in sorted(lines, key=lambda l: l.bbox.cy):
        for row in rows:
            if any(_v_overlap(ln.bbox, o.bbox) > 0.5 for o in row):
                row.append(ln)
                break
        else:
            rows.append([ln])
    out: list[OcrLine] = []
    for row in rows:
        rtl = _rtl_weight(row)
        out.extend(sorted(row, key=lambda l: -l.bbox.x2 if rtl else l.bbox.x))
    return out


def _union(boxes: list[BBox]) -> BBox:
    x0 = min(b.x for b in boxes)
    y0 = min(b.y for b in boxes)
    return BBox(x=x0, y=y0, w=max(b.x2 for b in boxes) - x0, h=max(b.y2 for b in boxes) - y0)


def _skew(lines: list[OcrLine]) -> float:
    """Median baseline angle (radians) of wide detected text polygons."""
    angles = []
    for l in lines:
        if l.polygon and len(l.polygon) >= 2 and l.bbox.w > 2 * l.bbox.h:
            (x0, y0), (x1, y1) = l.polygon[0][:2], l.polygon[1][:2]
            if x1 - x0 > 1:
                angles.append(math.atan2(y1 - y0, x1 - x0))
    if len(angles) < 2:
        return 0.0
    a = statistics.median(angles)
    return a if abs(a) < math.radians(20) else 0.0


def _deskewed(lines: list[OcrLine], theta: float) -> list[OcrLine]:
    """Copies with boxes expressed in a frame rotated by -theta (used only for ordering)."""
    if abs(theta) < math.radians(0.5):
        return lines
    c, s = math.cos(-theta), math.sin(-theta)
    out = []
    for l in lines:
        pts = l.polygon or [[l.bbox.x, l.bbox.y], [l.bbox.x2, l.bbox.y], [l.bbox.x2, l.bbox.y2], [l.bbox.x, l.bbox.y2]]
        xs = [p[0] * c - p[1] * s for p in pts]
        ys = [p[0] * s + p[1] * c for p in pts]
        out.append(l.model_copy(update={"bbox": BBox(x=min(xs), y=min(ys), w=max(xs) - min(xs), h=max(ys) - min(ys))}))
    return out


def assign_reading_order(lines: list[OcrLine]) -> list[OcrLine]:
    if not lines:
        return lines
    originals = {l.id: l for l in lines}
    lines = _deskewed(lines, _skew(lines))
    n = len(lines)
    parent = list(range(n))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    med_h = statistics.median(l.bbox.h for l in lines) or 1.0
    for i in range(n):
        a = lines[i].bbox
        for j in range(i + 1, n):
            b = lines[j].bbox
            gap = max(a.y, b.y) - min(a.y2, b.y2)
            if gap <= 1.2 * med_h and _h_overlap(a, b, slack=0.5 * med_h) and max(a.h, b.h) < 2.2 * min(a.h, b.h) + med_h:
                parent[find(j)] = find(i)
    groups: dict[int, list[OcrLine]] = {}
    for i, ln in enumerate(lines):
        groups.setdefault(find(i), []).append(ln)
    blocks = [(_union([l.bbox for l in g]), g) for g in groups.values()]

    page_rtl = _rtl_weight(lines)
    bands: list[list[tuple[BBox, list[OcrLine]]]] = []
    for blk in sorted(blocks, key=lambda b: b[0].y):
        for band in bands:
            if any(_v_overlap(blk[0], o[0]) > 0.3 for o in band):
                band.append(blk)
                break
        else:
            bands.append([blk])

    out: list[OcrLine] = []
    block_idx = 0
    for band in bands:
        band.sort(key=lambda b: -b[0].x2 if page_rtl else b[0].x)
        for _, g in band:
            for ln in _order_rows(g):
                out.append(originals[ln.id].model_copy(update={"line_index": len(out), "block_index": block_idx}))
            block_idx += 1
    return out
