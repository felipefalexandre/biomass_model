import zipfile

from biomass_model.datasets.ibge import _extract, _sha256


def test_extract_and_hash(tmp_path):
    zip_path = tmp_path / "sample.zip"
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr("areas/vege_area.shp", b"dummy")
        archive.writestr("areas/vege_area.dbf", b"dummy")
    out = tmp_path / "out"
    shapefiles = _extract(zip_path, out)
    assert len(shapefiles) == 1
    assert shapefiles[0].endswith("vege_area.shp")
    assert len(_sha256(zip_path)) == 64
