# Geospatial File Measurement API

A FastAPI service that accepts KML files and ZIP archives containing a Shapefile, extracts vector features, and calculates geometry measurements in metric units.

## Features

- Upload KML and zipped Shapefile datasets.
- Extract feature geometry, attributes and source CRS.
- Calculate polygon and multipolygon area in square metres.
- Calculate line and multiline length in metres.
- Identify point geometries for which area/length is not applicable.
- Transform geographic coordinates into a projected CRS before measuring.
- Persist upload results in SQLite and retrieve file metadata and measurements.
- Return explicit statuses for missing CRS, invalid geometry and unsupported cases.

## Architecture

```text
HTTP upload
    |
    v
FastAPI validation
    |
    v
Temporary upload workspace
    |
    v
GeoPandas / Pyogrio file reader
    |
    v
Shapely geometry + PyProj CRS transformation
    |
    v
Measurement result
    |
    v
JSON-safe response + SQLite persistence
    |
    v
GET file details / GET measurements
```

## Technology

Python 3.11+, FastAPI, GeoPandas, Pyogrio, Shapely, PyProj, SQLite, Pytest and HTTPX.

## Project structure

```text
app/
  main.py
  services/
    file_reader.py
    measurements.py
    storage.py
tests/
  test_main.py
  test_measurements.py
  test_measurement_collections.py
sample_data/
requirements.txt
README.md
```

## Installation

### Windows PowerShell

```powershell
git clone https://github.com/san613deep/geospatial-measurement-api.git
cd geospatial-measurement-api
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### macOS / Linux

```bash
git clone https://github.com/san613deep/geospatial-measurement-api.git
cd geospatial-measurement-api
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Run the API

```bash
python -m uvicorn app.main:app --reload
```

- API root: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- Health: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
- Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## API endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/files/` | Upload a KML or zipped Shapefile |
| GET | `/api/files/{file_id}/` | Retrieve uploaded-file metadata |
| GET | `/api/files/{file_id}/measurements/` | Retrieve feature measurements |

Upload a sample polygon:

```bash
curl -X POST "http://127.0.0.1:8000/api/files/" \
  -F "file=@sample_data/sample_polygon.kml"
```

Use the returned `id` with the two GET endpoints.

## Measurement model

| Geometry | Result | Unit |
|---|---|---|
| Polygon / MultiPolygon | Area | square metres |
| LineString / MultiLineString | Length | metres |
| Point / MultiPoint | Not required | — |

Geographic longitude/latitude coordinates are angular values, so the service transforms supported geometries into a projected UTM CRS before calculating planar area or length.

## Measurement statuses

The service reports statuses including `COMPLETED`, `NOT_REQUIRED`, `NOT_AVAILABLE`, `CRS_REQUIRED`, `INVALID_CRS`, `INVALID_GEOMETRY`, `UNSUPPORTED_GEOMETRY`, `UNSUPPORTED_CRS_REGION`, `INVALID_COORDINATES`, `TRANSFORMATION_FAILED` and `MEASUREMENT_FAILED`.

## Tests

Run the complete test suite from the repository root:

```bash
python -m pytest -q
```

The tests cover API health, upload and retrieval flows, supported/unsupported files, geometry measurement, CRS errors, invalid geometry and multi-part geometry cases. GitHub Actions runs the same test command on pushes and pull requests.

## Limitations and responsible use

- The current measurement strategy selects a UTM zone from a representative point. Very large geometries or features spanning multiple UTM zones need a more suitable projection/geodesic strategy.
- Results depend on the correctness of the input CRS.
- The API is a portfolio prototype. Authentication, per-user access controls, upload-size limits, rate limiting and production monitoring should be added before public deployment.
- Do not use the current measurements as legal or surveying-grade evidence without independent validation.

## Future improvements

- Add upload size and archive extraction limits.
- Add tests for antimeridian-crossing and multi-zone geometries.
- Add geodesic measurement support for large regions.
- Add authentication and per-user file ownership.
- Add structured logs and deployment monitoring.
