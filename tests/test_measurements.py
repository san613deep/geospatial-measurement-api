from shapely.geometry import LineString, Point, Polygon

from app.services.measurements import calculate_measurement


def test_point_requires_no_measurement():
    result = calculate_measurement(
        Point(-74.006, 40.7128),
        "EPSG:4326",
    )

    assert result["status"] == "NOT_REQUIRED"


def test_line_length_is_measured_in_meters():
    line = LineString(
        [
            (-74.0060, 40.7128),
            (-74.0050, 40.7128),
        ]
    )

    result = calculate_measurement(line, "EPSG:4326")

    assert result["status"] == "COMPLETED"
    assert result["measurement_type"] == "length"
    assert result["unit"] == "meters"
    assert result["value"] > 0


def test_polygon_area_is_measured_in_square_meters():
    polygon = Polygon(
        [
            (-74.0060, 40.7120),
            (-74.0050, 40.7120),
            (-74.0050, 40.7130),
            (-74.0060, 40.7130),
            (-74.0060, 40.7120),
        ]
    )

    result = calculate_measurement(polygon, "EPSG:4326")

    assert result["status"] == "COMPLETED"
    assert result["measurement_type"] == "area"
    assert result["unit"] == "square_meters"
    assert result["value"] > 0


def test_missing_crs_is_reported():
    result = calculate_measurement(
        LineString([(0, 0), (1, 1)]),
        None,
    )

    assert result["status"] == "CRS_REQUIRED"


from shapely.geometry import Polygon


def test_invalid_crs_returns_invalid_crs():
    polygon = Polygon(
        [
            (0, 0),
            (1, 0),
            (1, 1),
            (0, 1),
            (0, 0),
        ]
    )

    result = calculate_measurement(polygon, "not-a-valid-crs")

    assert result["status"] == "INVALID_CRS"
    assert result["value"] is None


def test_invalid_polygon_returns_invalid_geometry():
    # This polygon crosses itself, making it invalid.
    polygon = Polygon(
        [
            (0, 0),
            (2, 2),
            (0, 2),
            (2, 0),
            (0, 0),
        ]
    )

    result = calculate_measurement(polygon, "EPSG:4326")

    assert result["status"] == "INVALID_GEOMETRY"
    assert result["value"] is None
