# make_shapefile.py
import shapefile  # pyshp

w = shapefile.Writer("sample", shapeType=shapefile.POLYGON)
w.field("name", "C")

# Polygon
w.poly(
    [[[72.80, 19.00], [72.85, 19.00], [72.85, 19.05], [72.80, 19.05], [72.80, 19.00]]]
)
w.record("Polygon 1")
w.close()

# Write .prj for EPSG:4326
with open("sample.prj", "w") as f:
    f.write(
        'GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",'
        'SPHEROID["WGS_1984",6378137,298.257223563]],'
        'PRIMEM["Greenwich",0],UNIT["Degree",0.0174532925199433]]'
    )
