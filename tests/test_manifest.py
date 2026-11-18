import hashlib
import json

from biomass_model.manifest import build_manifest, write_manifest


def test_sha256_and_manifest(tmp_path):
    data = tmp_path / "a.bin"
    data.write_bytes(b"biomass")
    expected = hashlib.sha256(b"biomass").hexdigest()
    manifest = build_manifest("test", {"x": 1}, [data])
    assert manifest["outputs"][0]["sha256"] == expected
    assert manifest["outputs"][0]["bytes"] == 7
    assert manifest["dataset"] == "test"
    assert manifest["params"] == {"x": 1}

    path = write_manifest(manifest, tmp_path / "manifests")
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert loaded["dataset"] == "test"
    assert "earthdata_token" not in path.read_text(encoding="utf-8").lower()
