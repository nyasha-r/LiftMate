from __future__ import annotations

import math
import xml.etree.ElementTree as ET
from datetime import datetime


MAX_GPX_BYTES = 5 * 1024 * 1024


def analyze_gpx(data: bytes) -> dict:
    """Extract basic route statistics from a GPX file."""
    if not data or len(data) > MAX_GPX_BYTES:
        raise ValueError("GPX file must be between 1 byte and 5 MB.")

    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        raise ValueError("This file is not valid GPX/XML.") from exc

    points = []
    for element in root.iter():
        if element.tag.rsplit("}", 1)[-1] != "trkpt":
            continue

        try:
            lat = float(element.attrib["lat"])
            lon = float(element.attrib["lon"])
        except (KeyError, ValueError):
            continue

        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            continue

        point = {"lat": lat, "lon": lon, "ele": None, "time": None}
        for child in element:
            name = child.tag.rsplit("}", 1)[-1]
            if name == "ele":
                try:
                    point["ele"] = float(child.text)
                except (TypeError, ValueError):
                    pass
            elif name == "time" and child.text:
                try:
                    point["time"] = datetime.fromisoformat(
                        child.text.strip().replace("Z", "+00:00")
                    )
                except ValueError:
                    pass
        points.append(point)

    if len(points) < 2:
        raise ValueError("No usable track found. Please upload a GPX with at least two track points.")

    distance_km = 0.0
    for a, b in zip(points, points[1:]):
        lat1, lat2 = math.radians(a["lat"]), math.radians(b["lat"])
        dlat = lat2 - lat1
        dlon = math.radians(b["lon"] - a["lon"])
        h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        distance_km += 6371.0088 * 2 * math.asin(min(1.0, math.sqrt(h)))

    times = [p["time"] for p in points if p["time"] is not None]
    duration_seconds = None
    if len(times) >= 2:
        elapsed = (max(times) - min(times)).total_seconds()
        if elapsed >= 0:
            duration_seconds = int(elapsed)

    elevations = [p["ele"] for p in points if p["ele"] is not None]
    elevation_gain_m = None
    if len(elevations) >= 2:
        elevation_gain_m = round(sum(
            max(0.0, b - a) for a, b in zip(elevations, elevations[1:])
        ))

    pace_min_km = None
    if duration_seconds and distance_km > 0:
        pace_min_km = duration_seconds / 60 / distance_km

    return {
        "track_points": len(points),
        "distance_km": round(distance_km, 2),
        "duration_seconds": duration_seconds,
        "pace_min_km": round(pace_min_km, 2) if pace_min_km is not None else None,
        "elevation_gain_m": elevation_gain_m,
    }
