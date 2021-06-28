import subprocess
from unittest.mock import Mock

import pytest
import requests
from requests import Response
import os

from conda_vendor.core import (
    conda_vendor_artifacts_from_specs,
    fetch_repodata,
    parse_environment,
    CondaChannel,
    create_channel_directories,
    download_and_validate,
)
from tests.repodata_fixture import (
    vendor_manifest_dict,
    dot_conda_and_tar_list,
    python_395_pkg_list,
    repodata_output,
)


def expected_repodata_response():
    return {
        "info": {"subdir": "linux-64"},
        "packages": {
            "python-3.9.5-h12debd9_4.tar.bz2": {
                "build": "h12debd9_4",
                "build_number": 4,
                "depends": [
                    "ld_impl_linux-64",
                    "libffi >=3.3,<3.4.0a0",
                    "libgcc-ng >=7.5.0",
                    "libstdcxx-ng >=7.5.0",
                    "ncurses >=6.2,<7.0a0",
                    "openssl >=1.1.1k,<1.1.2a",
                    "readline >=8.0,<9.0a0",
                    "sqlite >=3.35.4,<4.0a0",
                    "tk >=8.6.10,<8.7.0a0",
                    "tzdata",
                    "xz >=5.2.5,<6.0a0",
                    "zlib >=1.2.11,<1.3.0a0",
                ],
                "license": "Python-2.0",
                "md5": "eb1bc6ccb2cbb43adb5a09e5802efef8",
                "name": "python",
                "sha256": "7fc98fe684cb716a8d19cf20a77ccce3cda3f6da968abaade63edbe006d8f3ba",
                "size": 23740654,
                "subdir": "linux-64",
                "timestamp": 1622828217909,
                "version": "3.9.5",
            },
            "_openmp_mutex-4.5-1_gnu.tar.bz2": {
                "build": "1_gnu",
                "build_number": 17,
                "constrains": ["openmp_impl 9999"],
                "depends": ["_libgcc_mutex 0.1 main", "libgomp >=7.5.0"],
                "license": "BSD-3-Clause",
                "md5": "84414b0edb0a36bd7e25fc4936c1abb5",
                "name": "_openmp_mutex",
                "sha256": "2c269ff2e33d3c158b4744485b7fe11ee132814c55a70b33b3e68d588375d465",
                "size": 22165,
                "subdir": "linux-64",
                "timestamp": 1612961522265,
                "version": "4.5",
            },
        },
        "packages.conda": {
            "tk-8.6.10-hbc83047_0.conda": {
                "build": "hbc83047_0",
                "build_number": 0,
                "depends": ["libgcc-ng >=7.3.0", "zlib >=1.2.11,<1.3.0a0"],
                "license": "Tcl/Tk",
                "license_family": "BSD",
                "md5": "9ba14aaba4818a66c820f85f5bf34ca0",
                "name": "tk",
                "sha256": "99fba40357115be361759731fc5a19b7833b4884310f2851f3faadbf33484991",
                "size": 3108365,
                "subdir": "linux-64",
                "timestamp": 1592503345885,
                "version": "8.6.10",
            },
            "xz-5.2.5-h7b6447c_0.conda": {
                "build": "h7b6447c_0",
                "build_number": 0,
                "depends": ["libgcc-ng >=7.3.0"],
                "license": "LGPL-2.1 and GPL-2.0",
                "md5": "73a16ea8ba890175a1ce94a3a87c8f68",
                "name": "xz",
                "sha256": "58045af0e1f23ea72b6759c4f5aac3e2fb98da9585758853d09961126d66f9ce",
                "size": 349481,
                "subdir": "linux-64",
                "timestamp": 1587011767250,
                "version": "5.2.5",
            },
        },
    }


@pytest.fixture
def mock_requests_repodata():
    requests_mock = Mock(spec=requests)
    actual_result_mock = Mock(Response)
    requests_mock.get.return_value = actual_result_mock
    actual_result_mock.json.return_value = expected_repodata_response()
    return requests_mock


def test_fetch_repodata_for_a_list_of_packages(mock_requests_repodata):
    input_packages = ["python-3.9.5-h12debd9_4.tar.bz2", "tk-8.6.10-hbc83047_0.conda"]
    result = fetch_repodata(input_packages, requests=mock_requests_repodata)
    assert result == {
        "info": {"subdir": "linux-64"},
        "packages": {
            "python-3.9.5-h12debd9_4.tar.bz2": {
                "build": "h12debd9_4",
                "build_number": 4,
                "depends": [
                    "ld_impl_linux-64",
                    "libffi >=3.3,<3.4.0a0",
                    "libgcc-ng >=7.5.0",
                    "libstdcxx-ng >=7.5.0",
                    "ncurses >=6.2,<7.0a0",
                    "openssl >=1.1.1k,<1.1.2a",
                    "readline >=8.0,<9.0a0",
                    "sqlite >=3.35.4,<4.0a0",
                    "tk >=8.6.10,<8.7.0a0",
                    "tzdata",
                    "xz >=5.2.5,<6.0a0",
                    "zlib >=1.2.11,<1.3.0a0",
                ],
                "license": "Python-2.0",
                "md5": "eb1bc6ccb2cbb43adb5a09e5802efef8",
                "name": "python",
                "sha256": "7fc98fe684cb716a8d19cf20a77ccce3cda3f6da968abaade63edbe006d8f3ba",
                "size": 23740654,
                "subdir": "linux-64",
                "timestamp": 1622828217909,
                "version": "3.9.5",
            },
        },
        "packages.conda": {
            "tk-8.6.10-hbc83047_0.conda": {
                "build": "hbc83047_0",
                "build_number": 0,
                "depends": ["libgcc-ng >=7.3.0", "zlib >=1.2.11,<1.3.0a0"],
                "license": "Tcl/Tk",
                "license_family": "BSD",
                "md5": "9ba14aaba4818a66c820f85f5bf34ca0",
                "name": "tk",
                "sha256": "99fba40357115be361759731fc5a19b7833b4884310f2851f3faadbf33484991",
                "size": 3108365,
                "subdir": "linux-64",
                "timestamp": 1592503345885,
                "version": "8.6.10",
            },
        },
    }


@pytest.fixture()
def minimal_environment(tmpdir_factory):
    content = """name: minimal_env
channels:
- defaults
dependencies:
- python=3.9.5"""
    fn = tmpdir_factory.mktemp("minimal_env").join("env.yml")
    fn.write(content)
    return fn


def test_parse_environment_file(minimal_environment):
    expected_output = ["python=3.9.5"]
    actual_output = parse_environment(minimal_environment)
    assert actual_output == expected_output


@pytest.fixture
def conda_channel_fixture():
    conda_channel = CondaChannel()

    return conda_channel


def test_create_dot_conda_and_tar_pkg_list(
    conda_channel_fixture, python_395_pkg_list, dot_conda_and_tar_list, repodata_output
):
    test_conda_channel = conda_channel_fixture
    test_conda_channel._repodata_dict = {"linux-64": repodata_output}

    actual_result = test_conda_channel.create_dot_conda_and_tar_pkg_list(
        python_395_pkg_list
    )
    expected_result = dot_conda_and_tar_list

    assert set(actual_result) == set(expected_result)


def test_format_manifest(conda_channel_fixture, repodata_output):
    test_conda_channel = conda_channel_fixture
    test_conda_channel._repodata_dict = {"linux-64": repodata_output}

    actual_result = test_conda_channel.format_manifest(
        ["python-3.9.5-h12debd9_4.tar.bz2"],
        base_url="https://repo.anaconda.com/pkgs/main",
        platform="linux-64",
    )

    expected_result = [
        {
            "url": "https://repo.anaconda.com/pkgs/main/linux-64/python-3.9.5-h12debd9_4.tar.bz2",
            "name": "python-3.9.5-h12debd9_4.tar.bz2",
            "validation": {
                "type": "sha256",
                "value": "7fc98fe684cb716a8d19cf20a77ccce3cda3f6da968abaade63edbe006d8f3ba",
            },
        }
    ]

    assert actual_result == expected_result


def test_conda_vendor_artifacts_from_specs():
    specs = ["python=3.9.5"]
    actual_result = conda_vendor_artifacts_from_specs(specs)
    expected_result = vendor_manifest_dict()
    assert len(actual_result["resources"]) == len(expected_result["resources"])


#  assert actual_result["resources"][0] == expected_result["resources"][6]


def test_create_channel_directories(tmp_path):
    returned_local_channel = create_channel_directories(str(tmp_path.absolute()))

    expected_root_dir = tmp_path / "local_channel"
    expected_linux_dir = expected_root_dir / "linux-64"
    expected_noarch_dir = expected_root_dir / "noarch"

    assert expected_root_dir.is_dir()
    assert expected_linux_dir.is_dir()
    assert expected_noarch_dir.is_dir()
    assert returned_local_channel == expected_root_dir


@pytest.fixture
def mock_requests_download():
    requests_mock = Mock(spec=requests)
    requests_mock.get.return_value = bytearray([9, 9, 9])
    return requests_mock


def test_download_and_validate(mock_requests_download, tmp_path):
    test_linux_path = tmp_path / "linux-64"
    test_linux_path.mkdir()

    test_noarch_path = tmp_path / "noarch"
    test_noarch_path.mkdir()

    test_manifest_dict = {
        "resources": [
            {
                "url": "https://repo.anaconda.com/pkgs/main/linux-64/_libgcc_mutex-0.1-main.conda",
                "name": "_libgcc_mutex-0.1-main.conda",
                "validation": {
                    "type": "sha256",
                    "value": "476626712f60e5ef0fe04c354727152b1ee5285d57ccd3575c7be930122bd051",
                },
            },
            {
                "url": "https://repo.anaconda.com/pkgs/main/noarch/tzdata-2020f-h52ac0ba_0.conda",
                "name": "tzdata-2020f-h52ac0ba_0.conda",
                "validation": {
                    "type": "sha256",
                    "value": "6635dd74510ab7c399d43781e866c977d7d715147e942f10a21aed4f00251f80",
                },
            },
        ]
    }

    expected_linux_package_path = (
        test_linux_path / test_manifest_dict["resources"][0]["name"]
    )
    expected_linux_package_file_name = test_manifest_dict["resources"][0]["name"]

    expected_noarch_package_path = (
        test_noarch_path / test_manifest_dict["resources"][1]["name"]
    )
    expected_noarch_package_file_name = test_manifest_dict["resources"][1]["name"]

    expected_file_data = mock_requests_download.get.return_value

    download_and_validate(test_manifest_dict, tmp_path, requests=mock_requests_download)

    assert expected_linux_package_path.exists()
    assert expected_noarch_package_path.exists()

    assert mock_requests_download.get.call_count == 2
    for i, call in enumerate(mock_requests_download.get.call_args_list):
        args, kwargs = call
        assert args[0] == test_manifest_dict["resources"][i]["url"]

    file_name = test_manifest_dict["resources"][0]["name"]
    with open(tmp_path / "linux-64" / expected_linux_package_file_name, "rb") as f:
        result_linux_file_data = f.read()

    assert expected_file_data == result_linux_file_data

    with open(tmp_path / "noarch" / expected_noarch_package_file_name, "rb") as f:
        result_no_arch_file_data = f.read()

    assert expected_file_data == result_no_arch_file_data
