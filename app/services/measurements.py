import math

from pyproj import CRS, Transformer
from shapely.geometry.base import BaseGeometry
import shapely


def _measurement_result(
    status: str,
    measurement_type: str | None = None,
    value: float | None = None,
    unit: str | None = None,
    measurement_crs: str | None = None,
) -> dict:
    """Build a consistent measurement result."""
    result = {
        "measurement_type": measurement_type,
        "value": value,
        "unit": unit,
        "status": status,
    }

    if measurement_crs is not None:
        result["measurement_crs"] = measurement_crs

    return result


def calculate_measurement(
    geometry: BaseGeometry,
    source_crs: str | CRS | None,
) -> dict:
    """
    Calculate polygon area or line length in metric units.

    Geographic coordinates are transformed into a local UTM CRS
    before measurement. Errors are returned as statuses rather
    than being allowed to crash the API.
    """
    # 1. Handle missing or empty geometry.
    if geometry is None or geometry.is_empty:
        return _measurement_result("NOT_AVAILABLE")

    geometry_type = geometry.geom_type

    # 2. Points do not need area or length measurements.
    if geometry_type in {"Point", "MultiPoint"}:
        return _measurement_result("NOT_REQUIRED")

    # 3. Only these geometry types are measured.
    supported_types = {
        "Polygon",
        "MultiPolygon",
        "LineString",
        "MultiLineString",
    }

    if geometry_type not in supported_types:
        return _measurement_result("UNSUPPORTED_GEOMETRY")

    # 4. A CRS is required to interpret coordinate values correctly.
    if source_crs is None:
        return _measurement_result("CRS_REQUIRED")

    # 5. Reject invalid geometries before measuring.
    try:
        if not geometry.is_valid:
            return _measurement_result("INVALID_GEOMETRY")
    except Exception:
        return _measurement_result("INVALID_GEOMETRY")

    # 6. Parse and validate the source CRS.
    try:
        crs = CRS.from_user_input(source_crs)
    except Exception:
        return _measurement_result("INVALID_CRS")

    # 7. Transform a representative point to longitude/latitude
    # to choose a local UTM zone.
    try:
        to_geographic = Transformer.from_crs(
            crs,
            "EPSG:4326",
            always_xy=True,
        )

        representative_point = geometry.representative_point()

        longitude, latitude = to_geographic.transform(
            representative_point.x,
            representative_point.y,
            errcheck=True,
        )

        if not math.isfinite(longitude) or not math.isfinite(latitude):
            return _measurement_result("INVALID_COORDINATES")

        # UTM is generally suitable between 80°S and 84°N.
        if not (-80 <= latitude <= 84):
            return _measurement_result("UNSUPPORTED_CRS_REGION")

        if not (-180 <= longitude <= 180):
            return _measurement_result("INVALID_COORDINATES")

    except Exception:
        return _measurement_result("TRANSFORMATION_FAILED")

    # 8. Select a UTM zone for the representative point.
    zone = min(60, int((longitude + 180) // 6) + 1)

    if latitude >= 0:
        target_epsg = 32600 + zone
    else:
        target_epsg = 32700 + zone

    # 9. Transform the entire geometry before calculating its
    # area or length. Do not measure geographic degrees directly.
    try:
        target_crs = CRS.from_epsg(target_epsg)

        transformer = Transformer.from_crs(
            crs,
            target_crs,
            always_xy=True,
        )

        projected_geometry = shapely.transform(
            geometry,
            transformer.transform,
            interleaved=False,
        )

        if projected_geometry.is_empty:
            return _measurement_result("NOT_AVAILABLE")

        if not projected_geometry.is_valid:
            return _measurement_result("INVALID_GEOMETRY")

        if geometry_type in {"Polygon", "MultiPolygon"}:
            value = projected_geometry.area
            measurement_type = "area"
            unit = "square_meters"
        else:
            value = projected_geometry.length
            measurement_type = "length"
            unit = "meters"

        if not math.isfinite(value):
            return _measurement_result("MEASUREMENT_FAILED")

        return _measurement_result(
            status="COMPLETED",
            measurement_type=measurement_type,
            value=float(value),
            unit=unit,
            measurement_crs=f"EPSG:{target_epsg}",
        )

    except Exception:
        return _measurement_result("TRANSFORMATION_FAILED")
