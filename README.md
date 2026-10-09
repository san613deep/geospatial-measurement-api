
# Geospatial File Measurement API

A REST API built with FastAPI that accepts geospatial files, reads their features, and calculates measurements for supported geometries.

## Features

- Upload KML files and ZIP archives containing a Shapefile.
- Extract feature geometry, geometry type, properties, and coordinate reference system (CRS).
- Calculate polygon area in square meters.
- Calculate line length in meters.
- Identify point geometries that do not require area or length measurements.
- Transform geometries into a projected coordinate system before measuring.
- Store uploaded file results in SQLite for later retrieval.
- Retrieve file details and feature measurements using API endpoints.
- Validate common file and geometry errors.

## Technology Stack

- **Python** — application language
- **FastAPI** — REST API framework
- **GeoPandas** — geospatial file reading and feature handling
- **Shapely** — geometry operations
- **PyProj** — coordinate reference system transformations
- **Pyogrio** — geospatial data reading engine
- **SQLite** — persistent storage
- **Pytest** — automated testing

## Project Structure

```text
geospatial-measurement-api/
├── app/
│   ├── main.py
│   └── services/
│       ├── file_reader.py
│       ├── measurements.py
│       └── storage.py
├── tests/
│   ├── test_main.py
│   └── test_measurements.py
├── requirements.txt
├── README.md
└── geospatial_api.db
```

The database file is created by the application. It may not exist until the application initializes.

## Requirements

- Python 3.12 or a compatible Python version
- pip
- A terminal such as PowerShell on Windows

## Installation

### 1. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd geospatial-measurement-api
```

Replace the placeholder with your actual GitHub repository URL.

### 2. Create a virtual environment

On Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

## Run the API

Start the development server from the project root:

```powershell
python -m uvicorn app.main:app --reload
```

The API will normally be available at:

- API root: http://127.0.0.1:8000/
- Health check: http://127.0.0.1:8000/health
- Interactive API documentation: http://127.0.0.1:8000/docs

## API Endpoints

### 1. Upload a geospatial file

**Endpoint:** `POST /api/files/`

Accepts a `.kml` file or a `.zip` archive containing exactly one Shapefile.

Example using curl:

```bash
curl -X POST "http://127.0.0.1:8000/api/files/" \
  -F "file=@sample_polygon.kml"
```

The response includes a file ID and extracted feature information, including geometry, properties, CRS, and measurement results.

Save the returned file ID for the retrieval endpoints.

### 2. Retrieve file details

**Endpoint:** `GET /api/files/{id}/`

Returns the stored information for a previously uploaded file.

Example:

```bash
curl "http://127.0.0.1:8000/api/files/1/"
```

Replace `1` with an ID returned by your upload request.

### 3. Retrieve measurements

**Endpoint:** `GET /api/files/{id}/measurements/`

Returns the measurement results for the stored file's features.

Example:

```bash
curl "http://127.0.0.1:8000/api/files/1/measurements/"
```

## Measurement Logic

| Geometry | Measurement | Unit |
|---|---|---|
| Polygon | Area | Square meters |
| MultiPolygon | Combined polygon area | Square meters |
| LineString | Length | Meters |
| MultiLineString | Combined line length | Meters |
| Point | Not required | None |
| MultiPoint | Not required | None |

Measurements are calculated after transforming the geometry into a projected coordinate system. The current implementation chooses a UTM zone based on a representative point.

Geographic coordinates such as longitude and latitude are angular coordinates. Measuring their raw coordinate values would not produce reliable areas in square meters or lengths in meters.

## Measurement Statuses

The measurement service can return statuses such as:

- `COMPLETED` — measurement calculated successfully.
- `NOT_REQUIRED` — the geometry does not require area or length measurement.
- `NOT_AVAILABLE` — geometry is missing or empty.
- `CRS_REQUIRED` — a source coordinate reference system is required.
- `INVALID_CRS` — the source CRS could not be interpreted.
- `INVALID_GEOMETRY` — the geometry is invalid.
- `UNSUPPORTED_GEOMETRY` — the geometry type is not supported for measurement.
- `UNSUPPORTED_CRS_REGION` — the location is outside the supported UTM latitude range.
- `INVALID_COORDINATES` — transformed coordinates are invalid.
- `TRANSFORMATION_FAILED` — a coordinate transformation failed.
- `MEASUREMENT_FAILED` — the resulting measurement is not finite.

## Coordinate Reference Systems (CRS)

A CRS describes how coordinates relate to locations on Earth.

This application uses PyProj to interpret the source CRS and transform supported geometries into a local UTM CRS before calculating measurements.

The CRS used for the measurement is included in successful measurement results.

**Limitations:** UTM is best suited to relatively local features. Large geometries or geometries spanning multiple UTM zones may require a different projection strategy to improve measurement accuracy. Measurements also depend on the correctness of the input CRS.

## Data Storage

The application uses SQLite to store uploaded file results. This allows file details and measurements to be retrieved after an API request finishes and after the development server restarts.

## Run Automated Tests

From the project root, run:

```powershell
python -m pytest -q
```

The current test suite covers file upload, measurement calculations, file retrieval, unsupported formats, invalid ZIP files, missing Shapefiles, invalid CRS values, and invalid polygons.

## Current Test Status

The project currently has **16 passing automated tests** in the development environment.

Run the test command above to verify the results in your own environment.

## Future Improvements

- Add more tests for malformed KML, missing Shapefile components, and unusual coordinate systems.
- Improve measurement accuracy for large geometries and features spanning multiple UTM zones.
- Add upload size limits and stronger resource-exhaustion protections.
- Improve API error responses and request validation.
- Add authentication and authorization if the API is deployed for multiple users.
- Add deployment configuration and production monitoring.

## Learning Outcomes

This project demonstrates:

- Building REST APIs with FastAPI.
- Reading geospatial formats with GeoPandas.
- Working with vector geometries and CRS transformations.
- Calculating polygon areas and line lengths.
- Persisting application data using SQLite.
- Writing automated tests with Pytest.
- Handling invalid files and measurement errors.
