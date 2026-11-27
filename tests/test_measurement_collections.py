"""Regression tests for multi-part geometry measurement support."""
from shapely.geometry import LineString, MultiLineString, MultiPolygon, Polygon

from app.services.measurements import calculate_measurement


def test_multiline_string_length_is_measured():
    geometry = MultiLineString(
        [
            LineString([(-74.0060, 40.7128), (-74.0050, 40.7128)]),
            LineString([(-74.0040, 40.7128), (-74.0030, 40.7128)]),
        ]
    )

    result = calculate_measurement(geometry, "EPSG:4326")

    assert result["status"] == "COMPLETED"
    assert result["measurement_type"] == "length"
    assert result["unit"] == "meters"
    assert result["value"] > 0


def test_multipolygon_area_is_measured():
    first = Polygon(
        [(-74.0060, 40.7120), (-74.0050, 40.7120), (-74.0050, 40.7130),
         (-74.0060, 40.7130), (-74.0060, 40.7120)]
    )
    second = Polygon(
        [(-74.0040, 40.7120), (-74.0030, 40.7120), (-74.0030, 40.7130),
         (-74.0040, 40.7130), (-74.0040, 40.7120)]
    )

    result = calculate_measurement(MultiPolygon([first, second]), "EPSG:4326")

    assert result["status"] == "COMPLETED"
    assert result["measurement_type"] == "area"
    assert result["unit"] == "square_meters"
    assert result["value"] > 0
