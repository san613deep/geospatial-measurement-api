from pathlib import Path, PurePosixPath, PureWindowsPath
import tempfile
import zipfile

import geopandas as gpd


def read_geospatial_file(file_path: Path) -> gpd.GeoDataFrame:
    """
    Read a KML file or a ZIP containing exactly one Shapefile.

    Returns a GeoDataFrame containing the extracted features.
    Raises ValueError when the uploaded file is invalid or unsupported.
    """
    suffix = file_path.suffix.lower()

    if suffix == ".kml":
        try:
            gdf = gpd.read_file(file_path, engine="pyogrio")
        except Exception as exc:
            raise ValueError("The KML file could not be read.") from exc

        if gdf.empty:
            raise ValueError("The KML file contains no features.")

        return gdf

    if suffix != ".zip":
        raise ValueError("Unsupported file format. Upload a .kml or .zip file.")

    if not zipfile.is_zipfile(file_path):
        raise ValueError("The uploaded ZIP file is invalid.")

    try:
        with zipfile.ZipFile(file_path) as archive:
            members = [member for member in archive.infolist() if not member.is_dir()]

            if not members:
                raise ValueError("The ZIP archive is empty.")

            # Reject unsafe paths and symbolic links before extracting.
            for member in members:
                name = member.filename

                posix_path = PurePosixPath(name)
                windows_path = PureWindowsPath(name)

                if (
                    posix_path.is_absolute()
                    or windows_path.is_absolute()
                    or ".." in posix_path.parts
                    or ".." in windows_path.parts
                    or windows_path.drive
                    or "\x00" in name
                ):
                    raise ValueError("The ZIP archive contains an unsafe file path.")

                # Unix ZIP entries can mark symbolic links in their mode.
                unix_mode = member.external_attr >> 16
                if (unix_mode & 0o170000) == 0o120000:
                    raise ValueError(
                        "The ZIP archive contains an unsupported symbolic link."
                    )

            shp_files = [
                member.filename
                for member in members
                if PurePosixPath(member.filename).suffix.lower() == ".shp"
            ]

            if not shp_files:
                raise ValueError("The ZIP archive does not contain a Shapefile (.shp).")

            if len(shp_files) > 1:
                raise ValueError("The ZIP archive must contain exactly one Shapefile.")

            shp_path_in_zip = PurePosixPath(shp_files[0])
            folder = shp_path_in_zip.parent
            stem = shp_path_in_zip.stem.lower()

            # Shapefiles normally require matching .shx and .dbf files.
            same_folder_files = {
                PurePosixPath(member.filename).name.lower()
                for member in members
                if PurePosixPath(member.filename).parent == folder
            }

            required_files = {
                f"{stem}.shx",
                f"{stem}.dbf",
            }
            missing_files = required_files - same_folder_files

            if missing_files:
                missing_text = ", ".join(sorted(missing_files))
                raise ValueError(
                    f"The Shapefile is missing required component(s): {missing_text}."
                )

            # Limit uncompressed size to reduce ZIP-bomb risk.
            max_uncompressed_bytes = 100 * 1024 * 1024
            total_uncompressed_bytes = sum(member.file_size for member in members)

            if total_uncompressed_bytes > max_uncompressed_bytes:
                raise ValueError(
                    "The ZIP archive is too large after extraction (limit: 100 MB)."
                )

            with tempfile.TemporaryDirectory() as temp_dir:
                extraction_root = Path(temp_dir).resolve()

                for member in members:
                    destination = (
                        extraction_root / Path(*PurePosixPath(member.filename).parts)
                    ).resolve()

                    # Confirm each destination remains inside the temp folder.
                    if not destination.is_relative_to(extraction_root):
                        raise ValueError(
                            "The ZIP archive contains an unsafe file path."
                        )

                    destination.parent.mkdir(
                        parents=True,
                        exist_ok=True,
                    )

                    with archive.open(member) as source:
                        with destination.open("wb") as target:
                            while True:
                                chunk = source.read(1024 * 1024)
                                if not chunk:
                                    break
                                target.write(chunk)

                shp_path = extraction_root.joinpath(*shp_path_in_zip.parts)

                try:
                    gdf = gpd.read_file(shp_path, engine="pyogrio")
                except Exception as exc:
                    raise ValueError(
                        "The Shapefile could not be read. Check that its "
                        "components are valid and belong to the same dataset."
                    ) from exc

                if gdf.empty:
                    raise ValueError("The Shapefile contains no features.")

                return gdf

    except zipfile.BadZipFile as exc:
        raise ValueError("The uploaded ZIP file is corrupt.") from exc
