
import pytest

from app.gpx_analysis import MAX_GPX_BYTES, analyze_gpx


VALID_GPX = b"""<?xml version="1.0"?>
<gpx version="1.1" creator="LiftMate"
 xmlns="http://www.topografix.com/GPX/1/1">
  <trk><trkseg>
    <trkpt lat="25.3176" lon="82.9739">
      <ele>80</ele><time>2026-10-21T08:00:00Z</time>
    </trkpt>
    <trkpt lat="25.3276" lon="82.9839">
      <ele>90</ele><time>2026-10-21T08:10:00Z</time>
    </trkpt>
  </trkseg></trk>
</gpx>
"""


def test_analyze_valid_gpx():
    result = analyze_gpx(VALID_GPX)

    assert result["track_points"] == 2
    assert result["distance_km"] > 0
    assert result["duration_seconds"] == 600
    assert result["pace_min_km"] is not None
    assert result["elevation_gain_m"] == 10


def test_rejects_invalid_xml():
    with pytest.raises(ValueError, match="valid GPX/XML"):
        analyze_gpx(b"<gpx>")


def test_rejects_file_with_too_few_track_points():
    with pytest.raises(ValueError, match="at least two"):
        analyze_gpx(
            b'<gpx><trk><trkseg><trkpt lat="25" lon="83"/>'
            b'</trkseg></trk></gpx>'
        )


def test_rejects_empty_file():
    with pytest.raises(ValueError):
        analyze_gpx(b"")


def test_rejects_oversized_file():
    with pytest.raises(ValueError, match="5 MB"):
        analyze_gpx(b"x" * (MAX_GPX_BYTES + 1))
