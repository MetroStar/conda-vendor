import yaml
from conda_vendor.custom_manifest import IBManifest, CustomManifest
from unittest.mock import Mock, patch, call, mock_open

# "mymethod" in dir(dyn)


def test_custom_manifest():
    assert "__init__" in dir(CustomManifest)
    assert "read_meta_manifest" in dir(CustomManifest)
    assert "write_custom_manifest" in dir(CustomManifest)
    assert "format_custom_manifest" in dir(CustomManifest)


@patch("conda_vendor.custom_manifest.CustomManifest.read_meta_manifest")
def test_load_manifest(mock, tmp_path):
    mock.return_value = "booboobeedoop"
    test_manifest_path = tmp_path / "test_manifest.yml"
    c = IBManifest(manifest_path=test_manifest_path)
    mock.assert_called_once_with = [test_manifest_path]
    assert "write_custom_manifest" in dir(IBManifest)
    assert "format_custom_manifest" in dir(IBManifest)

@patch("conda_vendor.custom_manifest.CustomManifest.read_meta_manifest")
def test_write_custom_manifest(mock_read_meta_manifest, tmp_path):
    mock_read_meta_manifest.return_value = None
    c = IBManifest(manifest_path=tmp_path)

    test_custom_manifest = {"foomanchu": True}
    c.custom_manifest = test_custom_manifest
    expected_custom_manifest = test_custom_manifest

    test_custom_manifest_destination = tmp_path / 'ironbank_manifest.yml'

    
    c.write_custom_manifest(test_custom_manifest_destination)

    with open(test_custom_manifest_destination) as f:
        actual_custom_manifest = yaml.load(f, Loader=yaml.SafeLoader)

    assert actual_custom_manifest == expected_custom_manifest
    
def test_IBManifest_strip_lead_underscore():
    test_str = "_poobear"
    expected_str = "poobear"
    actual_result = IBManifest.strip_lead_underscore(test_str)

    assert expected_str == actual_result


@patch("conda_vendor.custom_manifest.CustomManifest.read_meta_manifest")
def test_format_custom_manifest(mock):

    test_meta_manifest = {
        "main": {
            "noarch": {"repodata_url": [], "entries": []},
            "linux-64": {
                "repodata_url": [],
                "entries": [
                    {
                        "url": f"https://conda.anaconda.org/main/linux-64/brotlipy-0.7.0-py39h27cfd23_1003.tar.bz2",
                        "name": "brotlipy",
                        "version": "0.7.0",
                        "channel": f"https://conda.anaconda.org/main/linux-64",
                        "sha256": "omega_yoyo",
                    }
                ],
            },
        },
        "conda-forge": {
            "noarch": {
                "repodata_url": [],
                "entries": [
                    {
                        "url": "https://conda.anaconda.org/conda-forge/noarch/ensureconda-1.4.1-pyhd8ed1ab_0.tar.bz2",
                        "name": "ensureconda",
                        "version": "1.4.1",
                        "channel": "https://conda.anaconda.org/conda-forge/noarch",
                        "sha256": "yoyo",
                    }
                ],
            },
            "linux-64": {"repodata_url": [], "entries": []},
        },
    }

    expected_iron_bank_manifest = {
        "resources": [
            {
                "url": "https://conda.anaconda.org/main/linux-64/brotlipy-0.7.0-py39h27cfd23_1003.tar.bz2",
                "filename": "brotlipy",
                "validation": {"type": "sha256", "value": "omega_yoyo"},
            },
            {
                "url": "https://conda.anaconda.org/conda-forge/noarch/ensureconda-1.4.1-pyhd8ed1ab_0.tar.bz2",
                "filename": "ensureconda",
                "validation": {"type": "sha256", "value": "yoyo"},
            },
        ]
    }

    mock.return_value = test_meta_manifest

    c = IBManifest()
    actual_manifest = c.format_custom_manifest()
    assert actual_manifest == expected_iron_bank_manifest
