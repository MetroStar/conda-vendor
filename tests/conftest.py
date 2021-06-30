import pytest
from unittest.mock import Mock
import requests
from requests import Response
import json
from conda_vendor.core import CondaLockWrapper
from tests.repodata_fixtures import (
    vendor_manifest_dict,
    dot_conda_and_tar_list,
    python_395_pkg_list,
    repodata_output,
)


@pytest.fixture(scope="function")
def minimal_environment(tmpdir_factory):
    content = """name: minimal_env
channels:
- defaults
dependencies:
- python=3.9.5"""
    fn = tmpdir_factory.mktemp("minimal_env").join("env.yml")
    fn.write(content)
    return fn


@pytest.fixture
def mock_requests_repodata(unfiltered_repo_data_response):
    requests_mock = Mock(spec=requests)
    actual_result_mock = Mock(Response)
    requests_mock.get.return_value = actual_result_mock
    actual_result_mock.json.return_value = unfiltered_repo_data_response
    return requests_mock


@pytest.fixture
def mock_conda_lock(
    unfiltered_repo_data_response, mock_conda_solve_value, mock_conda_parse_value
):
    CondaLockWrapper_mock = Mock(spec=CondaLockWrapper)
    CondaLockWrapper_mock.parse.return_value = mock_conda_parse_value
    CondaLockWrapper_mock.solve.return_value = mock_conda_solve_value
    CondaLockWrapper_mock.solution_from_environment.return_value = (
        mock_conda_solve_value
    )
    return CondaLockWrapper_mock


@pytest.fixture(scope="module")
def unfiltered_repo_data_response():
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


@pytest.fixture(scope="module")
def mock_conda_parse_value():
    return ["python=3.9.5"]


@pytest.fixture(scope="module")
def mock_conda_solve_value():
    return [
        {
            "base_url": "https://conda.anaconda.org/main",
            "build_number": 0,
            "build_string": "main",
            "channel": "main",
            "dist_name": "_libgcc_mutex-0.1-main",
            "name": "_libgcc_mutex",
            "platform": "linux-64",
            "version": "0.1",
        },
        {
            "base_url": "https://conda.anaconda.org/main",
            "build_number": 1,
            "build_string": "h06a4308_1",
            "channel": "main",
            "dist_name": "ca-certificates-2021.5.25-h06a4308_1",
            "name": "ca-certificates",
            "platform": "linux-64",
            "version": "2021.5.25",
        },
        {
            "base_url": "https://conda.anaconda.org/main",
            "build_number": 9,
            "build_string": "h7274673_9",
            "channel": "main",
            "dist_name": "ld_impl_linux-64-2.35.1-h7274673_9",
            "name": "ld_impl_linux-64",
            "platform": "linux-64",
            "version": "2.35.1",
        },
        {
            "base_url": "https://conda.anaconda.org/main",
            "build_number": 17,
            "build_string": "hd4cf53a_17",
            "channel": "main",
            "dist_name": "libstdcxx-ng-9.3.0-hd4cf53a_17",
            "name": "libstdcxx-ng",
            "platform": "linux-64",
            "version": "9.3.0",
        },
        {
            "base_url": "https://conda.anaconda.org/main",
            "build_number": 0,
            "build_string": "h52ac0ba_0",
            "channel": "main",
            "dist_name": "tzdata-2021a-h52ac0ba_0",
            "name": "tzdata",
            "platform": "noarch",
            "version": "2021a",
        },
        {
            "base_url": "https://conda.anaconda.org/main",
            "build_number": 17,
            "build_string": "h5101ec6_17",
            "channel": "main",
            "dist_name": "libgomp-9.3.0-h5101ec6_17",
            "name": "libgomp",
            "platform": "linux-64",
            "version": "9.3.0",
        },
        {
            "base_url": "https://conda.anaconda.org/main",
            "build_number": 17,
            "build_string": "1_gnu",
            "channel": "main",
            "dist_name": "_openmp_mutex-4.5-1_gnu",
            "name": "_openmp_mutex",
            "platform": "linux-64",
            "version": "4.5",
        },
        {
            "base_url": "https://conda.anaconda.org/main",
            "build_number": 17,
            "build_string": "h5101ec6_17",
            "channel": "main",
            "dist_name": "libgcc-ng-9.3.0-h5101ec6_17",
            "name": "libgcc-ng",
            "platform": "linux-64",
            "version": "9.3.0",
        },
        {
            "base_url": "https://conda.anaconda.org/main",
            "build_number": 2,
            "build_string": "he6710b0_2",
            "channel": "main",
            "dist_name": "libffi-3.3-he6710b0_2",
            "name": "libffi",
            "platform": "linux-64",
            "version": "3.3",
        },
        {
            "base_url": "https://conda.anaconda.org/main",
            "build_number": 1,
            "build_string": "he6710b0_1",
            "channel": "main",
            "dist_name": "ncurses-6.2-he6710b0_1",
            "name": "ncurses",
            "platform": "linux-64",
            "version": "6.2",
        },
        {
            "base_url": "https://conda.anaconda.org/main",
            "build_number": 0,
            "build_string": "h27cfd23_0",
            "channel": "main",
            "dist_name": "openssl-1.1.1k-h27cfd23_0",
            "name": "openssl",
            "platform": "linux-64",
            "version": "1.1.1k",
        },
        {
            "base_url": "https://conda.anaconda.org/main",
            "build_number": 0,
            "build_string": "h7b6447c_0",
            "channel": "main",
            "dist_name": "xz-5.2.5-h7b6447c_0",
            "name": "xz",
            "platform": "linux-64",
            "version": "5.2.5",
        },
        {
            "base_url": "https://conda.anaconda.org/main",
            "build_number": 3,
            "build_string": "h7b6447c_3",
            "channel": "main",
            "dist_name": "zlib-1.2.11-h7b6447c_3",
            "name": "zlib",
            "platform": "linux-64",
            "version": "1.2.11",
        },
        {
            "base_url": "https://conda.anaconda.org/main",
            "build_number": 0,
            "build_string": "h27cfd23_0",
            "channel": "main",
            "dist_name": "readline-8.1-h27cfd23_0",
            "name": "readline",
            "platform": "linux-64",
            "version": "8.1",
        },
        {
            "base_url": "https://conda.anaconda.org/main",
            "build_number": 0,
            "build_string": "hbc83047_0",
            "channel": "main",
            "dist_name": "tk-8.6.10-hbc83047_0",
            "name": "tk",
            "platform": "linux-64",
            "version": "8.6.10",
        },
        {
            "base_url": "https://conda.anaconda.org/main",
            "build_number": 0,
            "build_string": "hc218d9a_0",
            "channel": "main",
            "dist_name": "sqlite-3.36.0-hc218d9a_0",
            "name": "sqlite",
            "platform": "linux-64",
            "version": "3.36.0",
        },
        {
            "base_url": "https://conda.anaconda.org/main",
            "build_number": 4,
            "build_string": "h12debd9_4",
            "channel": "main",
            "dist_name": "python-3.9.5-h12debd9_4",
            "name": "python",
            "platform": "linux-64",
            "version": "3.9.5",
        },
    ]
