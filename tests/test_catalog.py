import pytest

from biomass_model import catalog


def test_catalog_unique_ids():
    ids = [spec.id for spec in catalog.DATASETS]
    assert len(ids) == len(set(ids))


@pytest.mark.parametrize("dataset_id", ["s2", "dem", "era5", "gedi"])
def test_catalog_required_fields(dataset_id):
    spec = catalog.get(dataset_id)
    assert spec.module
    assert spec.account
    assert spec.license
    assert spec.doc.startswith("docs/")


def test_catalog_unknown():
    with pytest.raises(KeyError):
        catalog.get("inexistente")
