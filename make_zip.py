# make_zip.py
import zipfile
from pathlib import Path

files = ["sample.shp", "sample.shx", "sample.dbf", "sample.prj"]

with zipfile.ZipFile("sample_shapefile.zip", "w", zipfile.ZIP_DEFLATED) as z:
    for f in files:
        p = Path(f)
        if not p.exists():
            print(f"WARNING: {f} not found, skipping")
            continue
        z.write(p, arcname=p.name)  # arcname=p.name keeps files at zip root
        print(f"added {f}")

# verify
with zipfile.ZipFile("sample_shapefile.zip") as z:
    print("Contents:", z.namelist())
