from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi.testclient import TestClient

from app.main import app
from app.services.storage import get_file as load_saved_file

client = TestClient(app)


def create_polygon_kml() -> bytes:
    """Create a small valid KML polygon for integration testing."""
    return b"""<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <Placemark>
      <name>Test Polygon</name>
      <Polygon>
        <outerBoundaryIs>
          <LinearRing>
            <coordinates>
              -74.0060,40.7120,0
              -74.0050,40.7120,0
              -74.0050,40.7130,0
              -74.0060,40.7130,0
              -74.0060,40.7120,0
            </coordinates>
          </LinearRing>
        </outerBoundaryIs>
      </Polygon>
    </Placemark>
  </Document>
</kml>"""


def test_home():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["message"] == ("Geospatial File Measurement API is running")


def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_upload_polygon_and_calculate_area():
    response = client.post(
        "/api/files/",
        files={
            "file": (
                "test_polygon.kml",
                create_polygon_kml(),
                "application/vnd.google-earth.kml+xml",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert data["filename"] == "test_polygon.kml"
    assert data["feature_count"] == 1
    assert data["status"] == "COMPLETED"

    feature = data["features"][0]
    assert feature["geometry_type"] == "Polygon"
    assert feature["measurement"]["measurement_type"] == "area"
    assert feature["measurement"]["unit"] == "square_meters"
    assert feature["measurement"]["status"] == "COMPLETED"
    assert feature["measurement"]["value"] > 0


def test_get_file_details_after_upload():
    upload = client.post(
        "/api/files/",
        files={
            "file": (
                "details_test.kml",
                create_polygon_kml(),
                "application/vnd.google-earth.kml+xml",
            )
        },
    )

    assert upload.status_code == 200
    file_id = upload.json()["id"]

    response = client.get(f"/api/files/{file_id}/")

    assert response.status_code == 200
    assert response.json()["id"] == file_id
    assert response.json()["filename"] == "details_test.kml"
    assert response.json()["feature_count"] == 1


def test_get_measurements_after_upload():
    upload = client.post(
        "/api/files/",
        files={
            "file": (
                "measurements_test.kml",
                create_polygon_kml(),
                "application/vnd.google-earth.kml+xml",
            )
        },
    )

    assert upload.status_code == 200
    file_id = upload.json()["id"]

    response = client.get(f"/api/files/{file_id}/measurements/")

    assert response.status_code == 200

    data = response.json()
    assert data["id"] == file_id
    assert data["feature_count"] == 1

    measurement = data["measurements"][0]["measurement"]
    assert measurement["measurement_type"] == "area"
    assert measurement["unit"] == "square_meters"
    assert measurement["status"] == "COMPLETED"
    assert measurement["value"] > 0


def test_unknown_file_returns_404():
    response = client.get("/api/files/unknown-test-file-id/")

    assert response.status_code == 404
    assert response.json()["detail"] == "File not found."


def test_unknown_measurements_return_404():
    response = client.get("/api/files/unknown-test-file-id/measurements/")

    assert response.status_code == 404
    assert response.json()["detail"] == "File not found."


def test_unsupported_file_extension():
    response = client.post(
        "/api/files/",
        files={
            "file": (
                "document.txt",
                b"This is not a geospatial file.",
                "text/plain",
            )
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == ("Only .kml and .zip files are supported.")


def test_upload_invalid_zip_returns_error():
    from fastapi.testclient import TestClient
    from app.main import app

    with TestClient(app) as client:
        response = client.post(
            "/api/files/",
            files={
                "file": (
                    "broken.zip",
                    b"This is not a ZIP file",
                    "application/zip",
                )
            },
        )

    assert response.status_code == 400
    assert "invalid" in response.json()["detail"].lower()


def test_upload_zip_without_shapefile_returns_error():
    import io
    import zipfile

    from fastapi.testclient import TestClient
    from app.main import app

    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w") as archive:
        archive.writestr("readme.txt", "No shapefile here")

    with TestClient(app) as client:
        response = client.post(
            "/api/files/",
            files={
                "file": (
                    "no_shapefile.zip",
                    zip_buffer.getvalue(),
                    "application/zip",
                )
            },
        )

    assert response.status_code == 400
    assert "shapefile" in response.json()["detail"].lower()
