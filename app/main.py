from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4
import pandas as pd

import geopandas as gpd
from fastapi import File, HTTPException, UploadFile

from app.services.file_reader import read_geospatial_file
from fastapi import FastAPI
from app.services.measurements import calculate_measurement
import math
from numbers import Real
from app.services.storage import (
    initialize_db,
    save_file,
    get_file as load_saved_file,
)

app = FastAPI(
    title="Geospatial File Measurement API",
    description="Upload geospatial files and calculate feature measurements.",
    version="1.0.0",
)

initialize_db()


def make_json_safe(value):
    """Convert missing and non-finite values into JSON-safe values."""

    if isinstance(value, dict):
        return {str(key): make_json_safe(item) for key, item in value.items()}

    if isinstance(value, (list, tuple)):
        return [make_json_safe(item) for item in value]

    # Handle pandas NaT, NaN, and other missing values.
    if value is None or pd.isna(value):
        return None

    # Convert NumPy scalar values to ordinary Python values.
    if hasattr(value, "item") and callable(value.item):
        try:
            value = value.item()
        except (ValueError, TypeError):
            pass

    if value is None:
        return None

    if isinstance(value, Real) and not math.isfinite(value):
        return None

    return value


@app.get("/")
def home():
    return {"message": "Geospatial File Measurement API is running"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post("/api/files/")
async def upload_file(file: UploadFile = File(...)):
    filename = Path(file.filename or "").name
    suffix = Path(filename).suffix.lower()

    if suffix not in {".kml", ".zip"}:
        raise HTTPException(
            status_code=400,
            detail="Only .kml and .zip files are supported.",
        )

    file_id = str(uuid4())

    try:
        with TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / f"upload{suffix}"

            content = await file.read()

            if not content:
                raise HTTPException(status_code=400, detail="The upload file is empty.")

            file_path.write_bytes(content)

            try:
                gdf = read_geospatial_file(file_path)
            except (ValueError, OSError) as exc:
                raise HTTPException(
                    status_code=400,
                    detail=str(exc),
                ) from exc
            except Exception as exc:
                print(f"DEBUG: {type(exc).__name__}: {exc}")
                raise HTTPException(
                    status_code=400,
                    detail="The geospatial file could not be read.",
                ) from exc

            features = []

            for index, row in gdf.iterrows():
                geometry = row.geometry

                measurement = calculate_measurement(
                    geometry,
                    gdf.crs,
                )

                features.append(
                    {
                        "feature_id": index,
                        "geometry_type": (
                            geometry.geom_type if geometry is not None else None
                        ),
                        "geometry": (
                            geometry.__geo_interface__ if geometry is not None else None
                        ),
                        "crs": (str(gdf.crs) if gdf.crs is not None else None),
                        "properties": row.drop(labels=[gdf.geometry.name]).to_dict(),
                        "measurement": measurement,
                    }
                )

            response_data = {
                "id": file_id,
                "filename": filename,
                "feature_count": len(gdf),
                "crs": (str(gdf.crs) if gdf.crs is not None else None),
                "status": "COMPLETED",
                "features": features,
            }

            safe_response = make_json_safe(response_data)

            save_file(safe_response)

            return safe_response

    finally:
        await file.close()


@app.get("/api/files/{file_id}/")
def get_file(file_id: str):
    file_data = load_saved_file(file_id)

    if file_data is None:
        raise HTTPException(
            status_code=404,
            detail="File not found.",
        )

    return {
        "id": file_data["id"],
        "filename": file_data["filename"],
        "feature_count": file_data["feature_count"],
        "crs": file_data["crs"],
        "status": file_data["status"],
    }


@app.get("/api/files/{file_id}/measurements/")
def get_file_measurements(file_id: str):
    file_data = load_saved_file(file_id)

    if file_data is None:
        raise HTTPException(
            status_code=404,
            detail="File not found.",
        )

    return {
        "id": file_data["id"],
        "filename": file_data["filename"],
        "feature_count": file_data["feature_count"],
        "measurements": [
            {
                "feature_id": feature["feature_id"],
                "geometry_type": feature["geometry_type"],
                "measurement": feature["measurement"],
            }
            for feature in file_data["features"]
        ],
    }
