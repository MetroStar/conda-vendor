import conda_lock
import hashlib
import json
import os
import pytest
import yaml

from contextlib import contextmanager
from copy import deepcopy
from importlib import resources
from pathlib import Path
from requests import Response
from requests.exceptions import ConnectionError
from unittest.mock import patch

from conda_lock.conda_solver import (
    _reconstruct_fetch_actions as reconstruct_fetch_actions,
)
from conda_lock.invoke_conda import conda_pkgs_dir


import conda_vendor
from conda_vendor.conda_vendor import (
    _generate_lock_spec,
    _get_conda_platform,
    _get_environment_name,
    _get_query_list,
    _get_virtual_packages,
    _improved_download,
    _remove_channel,
    create_repodata_json,
    download_packages,
    solve_environment,
    yaml_dump_ironbank_manifest,
)


#####################################################################
# Verify _get_conda_platform()
#####################################################################


@patch("sys.platform", "linux")
@patch("struct.calcsize")
def test_get_conda_platform_32bit(mock_struct) -> None:
    mock_struct.return_value = 4
    expected = "linux-32"
    result = _get_conda_platform()
    assert expected == result
    assert mock_struct.call_count == 1


@patch("sys.platform", "darwin")
@patch("struct.calcsize")
def test_get_conda_platform_64bi(mock_struct) -> None:
    mock_struct.return_value = 8
    expected = "osx-64"
    result = _get_conda_platform()
    assert expected == result
    assert mock_struct.call_count == 1


def test_get_conda_platform_passthrough():
    test_platforms = ["linux-64", "linux-32", "win-64", "win-32", "osx-64"]
    expected_returns = ["linux-64", "linux-32", "win-64", "win-32", "osx-64"]
    actual_returns = [_get_conda_platform(p) for p in test_platforms]
    assert set(actual_returns) == set(expected_returns)


#####################################################################
# The conda-lock requirements for "parse_environment_file"
# from src_parser.environment_yaml changed at v1.2.1 -> v1.3.0
# this is wrapped in the conda_vendor _generate_lock_spec
# these tests make sure the right version is called
#####################################################################


@patch("conda_vendor.conda_vendor.conda_lock_version", "1.2.1")
@patch("conda_vendor.conda_vendor.parse_environment_file")
def test_parse_environment_file_v121(mock_parse_environment_file):
    mock_parse_environment_file.return_value = True
    _generate_lock_spec("test.yml", "linux-64")
    assert len(mock_parse_environment_file.call_args.args) == 1


@patch("conda_vendor.conda_vendor.conda_lock_version", "1.3.0")
@patch("conda_vendor.conda_vendor.parse_environment_file")
def test_parse_environment_file_v130(mock_parse_environment_file):
    mock_parse_environment_file.return_value = True
    _generate_lock_spec("test.yml", "linux-64")
    assert len(mock_parse_environment_file.call_args.args) == 2


#####################################################################
# test _get_environment_name
#####################################################################


def test_generate_lock_spec(tmp_path_factory):
    f = tmp_path_factory.mktemp("test") / "env.yml"
    f.write_text(
        """name: readme
channels:
- main
dependencies:
- python
"""
    )
    name = _get_environment_name(f)
    assert name == "readme"


#####################################################################
# test _get_virtual_packages
#####################################################################


@patch("conda_vendor.conda_vendor.default_virtual_package_repodata")
def test_get_virtual_packages_default(mock_default_virtual_package_repodata):
    mock_default_virtual_package_repodata.return_value = True
    p = _get_virtual_packages("fake-64")
    mock_default_virtual_package_repodata.assert_called_once()


@patch("conda_vendor.conda_vendor.virtual_package_repo_from_specification")
def test_get_virtual_packages_str(mock_virtual_package_repodata_from_spec):
    mock_virtual_package_repodata_from_spec.return_value = True
    p = _get_virtual_packages("fake-64", "test.yml")
    mock_virtual_package_repodata_from_spec.assert_called_once()
    args = mock_virtual_package_repodata_from_spec.call_args.args
    assert isinstance(args[0], Path)


@patch("conda_vendor.conda_vendor.virtual_package_repo_from_specification")
def test_get_virtual_packages_path(mock_virtual_package_repodata_from_spec):
    mock_virtual_package_repodata_from_spec.return_value = True
    p = _get_virtual_packages("fake-64", Path("test.yml"))
    mock_virtual_package_repodata_from_spec.assert_called_once()
    args = mock_virtual_package_repodata_from_spec.call_args.args
    assert isinstance(args[0], Path)


#####################################################################
# test _get_query_list
#####################################################################
@pytest.fixture
def query_list_lock_spec(tmp_path_factory):
    f = tmp_path_factory.mktemp("query_list") / "environment.yaml"
    f.write_text(
        """name: query_list_env
channels:
- main
dependencies:
- pkg0
- pkg1=1.0
- pkg2==1.1
- pkg3>=0.5
- pkg4<0.6
- pkg5>=0.2,<1.0
"""
    )
    return _generate_lock_spec(f, ["linux-64"])


def test_get_query_list(query_list_lock_spec):
    specs = _get_query_list(query_list_lock_spec)
    expected = [
        "pkg0",
        "pkg1==1.0.*",
        "pkg2==1.1",
        "pkg3>=0.5",
        "pkg4<0.6",
        "pkg5>=0.2,<1.0",
    ]
    assert set(expected) == set(specs)


#####################################################################
# test _remove_channel
#####################################################################
@pytest.fixture
def pytorch_solution():
    sol = resources.files("tests.resources") / "pytorch_solution.json"
    with open(sol, "r") as f:
        return json.load(f)


# this test tests implementation details, i don't like it
def test_remove_channel(pytorch_solution):
    chan = "https://conda.anaconda.org/conda-forge/linux-64"
    filtered_solution = _remove_channel(pytorch_solution, chan)

    fetch = set(
        [pkg["channel"] for pkg in filtered_solution["actions"]["FETCH"]]
    )
    assert chan not in fetch

    link = set(
        [pkg["base_url"] for pkg in filtered_solution["actions"]["LINK"]]
    )
    assert chan not in link


@pytest.fixture
def download_root(tmp_path_factory):
    f = tmp_path_factory.mktemp("downloads")

    Path.mkdir(f / "linux-64")
    Path.mkdir(f / "noarch")
    return f


@patch("conda_vendor.conda_vendor._improved_download")
def test_remove_channel_download(
    mock_improved_download, download_root, pytorch_solution
):
    chan = "https://conda.anaconda.org/conda-forge/linux-64"
    solution = _remove_channel(pytorch_solution, chan)["actions"]["FETCH"]

    file_data = "JUNK"
    file_sha = hashlib.sha256(bytes(file_data, encoding="utf-8")).hexdigest()
    for pkg in solution:
        pkg["sha256"] = file_sha

    response = Response()
    response._content = bytes(file_data, encoding="utf-8")
    response.status_code = 200

    def _mock_download(url):
        assert url != chan
        return response

    mock_improved_download.side_effect = _mock_download
    download_packages(solution, download_root)


#####################################################################
# test reconstruct_fetch_actions
#####################################################################


@pytest.fixture
def pytorch_environment(tmp_path_factory):
    f = tmp_path_factory.mktemp("pytorch_env") / "environment.yml"
    f.write_text(
        """\
name: pytorch_env
channels:
- conda-forge
dependencies:
- pytorch
- torchvision
"""
    )
    return f


@pytest.fixture
def linux_64_virtual_packages(tmp_path_factory):
    f = tmp_path_factory.mktemp("vpkgs") / "virtual_packages.yml"
    f.write_text(
        """\
subdirs:
  linux-64:
    packages:
      __glibc: 2.28
      __unix: 0
      __linux: 5.15
"""
    )
    return f


def _create_repodata_record_json():
    root = Path(conda_pkgs_dir())

    info_dir = (root / "dummy_package0-0") / "info"
    info_dir.mkdir(parents=True, exist_ok=True)

    f = info_dir / "repodata_record.json"
    f.write_text(
        """{
  "arch": "x86_64",
  "build": "0",
  "build_number": 0,
  "channel": "file:///fake-url/linux-64",
  "constrains": [],
  "depends": [],
  "features": "",
  "fn": "dummy_package0-0.tar.bz2",
  "legacy_bz2_md5": "",
  "license": "",
  "license_family": "",
  "md5": "",
  "name": "dummy_package",
  "platform": "x86_64",
  "sha256": "",
  "size": 1,
  "subdir": "linux-64",
  "timestamp": 1662662340573,
  "track_features": "",
  "url": "file://fake-url/linux-64/dummy_package0-0.tar.bz2",
  "version": "0.0"
}
"""
    )


# grab the data right before reconstruct fetch_actions.  This *test* depends
# on _remove_channel being the final call before reconstruct_fetch_actions
# so that we can give reconstruct_fetch_actions the data we want it to have
@patch("conda_vendor.conda_vendor._remove_channel")
@patch("conda_vendor.conda_vendor.solve_specs_for_arch")
def test_reconstruct_fetch_actions(
    mock_solve_specs_for_arch,
    mock_remove_channel,
    pytorch_environment,
    pytorch_solution,
    linux_64_virtual_packages,
):

    # this corresponds to the virtual packages that were made for the file
    # in resources/pytorch_solution.json
    virtual_packages_channel = (
        "file:///var/folders/r0/7mmzfzr15cjbl3qyzjgr8pzw0000gt/T/tmp1le4_9n8"
    )
    filtered = _remove_channel(pytorch_solution, virtual_packages_channel)
    filtered["actions"]["LINK"].append(
        {
            "base_url": "file:///fake-url",
            "build_number": 0,
            "build_string": "0",
            "channel": "fake-url",
            "dist_name": "dummy_package0-0",
            "name": "dummy_package",
            "platform": "linux-64",
            "version": "0",
        }
    )

    mock_solve_specs_for_arch.return_value = {}
    mock_remove_channel.return_value = filtered

    # looking_for {pkgs_dirs}/dummy_packages0-0/info/repodata_record.json
    _create_repodata_record_json()
    solution = solve_environment(
        pytorch_environment, "conda", "linux-64", linux_64_virtual_packages
    )

    assert "dummy_package" in [pkg["name"] for pkg in solution]


#####################################################################
# test create_repodata_json
#####################################################################


@pytest.fixture
def create_repodata_input():
    inp = resources.files("tests.resources") / "create_repodata_input.json"
    with open(inp, "r") as f:
        return json.load(f)


@pytest.fixture
def create_repodata_output():
    inp = resources.files("tests.resources") / "create_repodata_output.json"
    with open(inp, "r") as f:
        data = f.read()

    response = Response()
    response.status_code = 200
    response._content = bytes(data, encoding="utf-8")
    return response


@patch("conda_vendor.conda_vendor._improved_download")
def test_create_repodata_json(
    mock_download,
    create_repodata_input,
    create_repodata_output,
    download_root,
):

    mock_download.return_value = create_repodata_output
    create_repodata_json(
        create_repodata_input["FETCH"], download_root, "linux-64"
    )

    with open(download_root / "linux-64" / "repodata.json", "r") as f:
        repodata = json.load(f)

    _packages = [pkg["name"] for _, pkg in repodata["packages"].items()]
    _conda_packages = [
        pkg["name"] for _, pkg in repodata["packages.conda"].items()
    ]
    repodata_packages = _packages + _conda_packages

    for pkg in create_repodata_input["FETCH"]:
        assert pkg["name"] in repodata_packages


@patch("conda_vendor.conda_vendor._improved_download")
def test_create_repodata_json_both_subdir_empty(
    mock_download,
    create_repodata_output,
    download_root,
):
    mock_download.return_value = create_repodata_output
    create_repodata_json([], download_root, "linux-64")

    assert (download_root / "linux-64" / "repodata.json").exists()
    assert (download_root / "noarch" / "repodata.json").exists()


@patch("conda_vendor.conda_vendor._improved_download")
def test_create_repodata_json_noarch_subdir_empty(
    mock_download,
    create_repodata_input,
    create_repodata_output,
    download_root,
):

    mock_download.return_value = create_repodata_output
    create_repodata_json(
        create_repodata_input["FETCH"], download_root, "linux-64"
    )

    assert (download_root / "linux-64" / "repodata.json").exists()
    assert (download_root / "noarch" / "repodata.json").exists()


#####################################################################
# test download_packages
#####################################################################


@pytest.fixture
def download_package_lists():
    package_list = [
        {
            "fn": "fake-1.tar.gz",
            "url": "https://fake-repo/linux-64/fake-1.tar.bz2",
            "subdir": "linux-64",
            "sha256": 0,
        },
        {
            "fn": "fake-2.tar.gz",
            "url": "https://fake-repo/linux-64/fake-2.tar.bz2",
            "subdir": "linux-64",
            "sha256": 0,
        },
        {
            "fn": "fake-3.tar.gz",
            "url": "https://fake-repo/linux-64/fake-3.tar.bz2",
            "subdir": "linux-64",
            "sha256": 0,
        },
        {
            "fn": "fake-4.tar.gz",
            "url": "https://fake-repo/linux-64/fake-4.tar.bz2",
            "subdir": "linux-64",
            "sha256": 0,
        },
    ]

    package_data = {}
    for i, pkg in enumerate(package_list):
        data = bytes(f"package-data-{i}", encoding="utf-8")
        h = hashlib.sha256(data).hexdigest()
        pkg["sha256"] = h
        package_data[pkg["url"]] = data

    return {"packages": package_list, "data": package_data}


@patch("conda_vendor.conda_vendor._improved_download")
def test_download_packages(
    mock_download, download_package_lists, download_root
):

    packages = download_package_lists["packages"]
    data = download_package_lists["data"]

    def _mock_download(url):
        response = Response()
        response.status_code = 200
        response._content = data[url]
        return response

    mock_download.side_effect = _mock_download
    download_packages(packages, download_root)

    for pkg in packages:
        loc = download_root / "linux-64" / pkg["fn"]

        # test file was saved to the right place
        assert loc.exists()

        # test that it was saved with the right data
        with open(loc, "rb") as f:
            h = hashlib.sha256(f.read()).hexdigest()
            assert h == pkg["sha256"]


@patch("conda_vendor.conda_vendor._improved_download")
def test_download_packages_bad_sha(
    mock_download, download_package_lists, download_root
):

    packages = download_package_lists["packages"]
    data = download_package_lists["data"]

    packages[0]["sha256"] = ""

    def _mock_download(url):
        response = Response()
        response.status_code = 200
        response._content = data[url]
        return response

    mock_download.side_effect = _mock_download

    with pytest.raises(SystemExit) as e:
        download_packages(packages[:1], download_root)

        assert e.type == SystemExit
        assert e.value.code == 1


# 404's come back with a valid page
@patch("conda_vendor.conda_vendor._improved_download")
def test_download_packages_404(
    mock_download, download_package_lists, download_root
):

    packages = download_package_lists["packages"]
    data = download_package_lists["data"]

    packages[0]["url"] = "https://github.com/thisshould404.html"

    def _mock_download(url):
        response = Response()
        response.status_code = 404
        response._content = bytes(
            "<html><body> File not Found! 404 </body></html>",
            encoding="utf-8",
        )
        return response

    mock_download.side_effect = _mock_download
    with pytest.raises(SystemExit) as e:
        download_packages(packages[:1], download_root)

        assert e.type == SystemExit
        assert e.value.code == 1


# requests raises a ConnectionError after timeout for a bad url
@patch("conda_vendor.conda_vendor._improved_download")
def test_download_packages_bad_url(
    mock_download, download_package_lists, download_root
):

    packages = download_package_lists["packages"]
    data = download_package_lists["data"]

    def _mock_download(url):
        raise ConnectionError()

    mock_download.side_effect = _mock_download
    with pytest.raises(Exception):
        download_packages(packages[:1], download_root)
        assert True


#####################################################################
# test yaml_dump_ironbank_manifest
#####################################################################

# remove virtual packages from th pytorch solution
@pytest.fixture
def pytorch_solution_clean(pytorch_solution):
    chan = (
        "file:///var/folders/r0/7mmzfzr15cjbl3qyzjgr8pzw0000gt/T/tmp1le4_9n8"
    )
    return _remove_channel(pytorch_solution, chan)["actions"]["FETCH"]


@contextmanager
def set_cwd(new_dir):
    cur = os.getcwd()
    os.chdir(new_dir)
    try:
        yield new_dir
    finally:
        os.chdir(cur)


def test_yaml_dump_ironbank_manifest(
    pytorch_solution_clean, tmp_path_factory
):
    import os

    cur = os.getcwd()

    package_list = pytorch_solution_clean

    root = tmp_path_factory.mktemp("dump_ironbank_manifest")
    with set_cwd(root):
        yaml_dump_ironbank_manifest(package_list)
        with open("ib_manifest.yaml", "r") as f:
            ib_manifest = yaml.load(f, Loader=yaml.SafeLoader)

        expected_packages = set([pkg["fn"] for pkg in package_list])
        actual_packages = set(
            [pkg["filename"] for pkg in ib_manifest["resources"]]
        )

        assert expected_packages == actual_packages
