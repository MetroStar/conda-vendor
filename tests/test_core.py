import subprocess
from unittest.mock import Mock, patch
import requests
from requests import Response
import os
import pytest
import hashlib
import json
from unittest import TestCase
from yaml import safe_load
from yaml.loader import SafeLoader
import yaml

from conda_vendor.core import (
    CondaChannel,
    get_manifest,
    create_manifest,
    get_local_environment_yaml,
    create_local_environment_yaml
)


def test_conda_channel_init(conda_channel_fixture):
    assert type(conda_channel_fixture) == CondaChannel
    assert conda_channel_fixture.base_url == "https://repo.anaconda.com/pkgs/main/"
    assert type(conda_channel_fixture.platforms) == list
    assert conda_channel_fixture.platforms[0] == "linux-64"
    assert conda_channel_fixture.platforms[1] == "noarch"
    assert conda_channel_fixture._repodata_dict == None


def test_create_directories(conda_channel_fixture):
    conda_channel_fixture.create_directories()
    for platform, info in conda_channel_fixture.channel_info.items():
        assert info["dir"].exists()

@patch("requests.get")
def test_conda_channel_fetch(mock_get, conda_channel_fixture,unfiltered_repo_data_response):
    mock_get.return_value = _mock_response(json_data=unfiltered_repo_data_response)
    expected = {
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
    input_packages = ["python-3.9.5-h12debd9_4.tar.bz2", "tk-8.6.10-hbc83047_0.conda"]
    conda_channel_fixture.fetch()
    result = conda_channel_fixture._repodata_dict
    assert set(result["linux-64"].keys()) == set(expected.keys())


def test_filter_repodata_linux_package(conda_channel_fixture, tmp_path):
    test_pkgs = ["LINUX_DUMMY_PACKAGE1"]
    test_repodata_dict = {
        "linux-64": {
            "info": {"subdir": "linux-64"},
            "packages": {
                "LINUX_DUMMY_PACKAGE1": {},
                "LINUX_DUMMY_PACKAGE2": {},
            },
            "packages.conda": {"DUMMY_LINUX_CONDA_PACKAGE": {}},
        },
        "noarch": {
            "info": {"subdir": "noarch"},
            "packages": {
                "NOARCH_DUMMER_PACKAGE1": {},
                "NOARCH_DUMMER_PACKAGE2": {},
            },
            "packages.conda": {"DUMMY_NOARCH_CONDA_PACKAGE": {}},
        },
    }
    expected_linux = {
        "packages": {
            "LINUX_DUMMY_PACKAGE1": {},
        },
        "packages.conda": {},
        "info": {"subdir": "linux-64"},
    }
    expected_file_path = tmp_path / "linux-64" / "repodata.json"
    conda_channel_fixture._repodata_dict = test_repodata_dict
    result_linux = conda_channel_fixture.filter_repodata(test_pkgs, platform="linux-64")
    assert set(expected_linux.keys()) == set(result_linux.keys())
    for key in expected_linux.keys():
        assert expected_linux[key] == result_linux[key]


def test_filter_repodata_noarch_package(conda_channel_fixture):
    test_pkgs = ["NOARCH_DUMMER_PACKAGE2"]
    test_repodata_dict = {
        "linux-64": {},
        "noarch": {
            "info": {"subdir": "noarch"},
            "packages": {
                "NOARCH_DUMMER_PACKAGE1": {},
                "NOARCH_DUMMER_PACKAGE2": {},
            },
            "packages.conda": {"DUMMY_NOARCH_CONDA_PACKAGE": {}},
        },
    }
    expected_noarch = {
        "packages": {
            "NOARCH_DUMMER_PACKAGE2": {},
        },
        "packages.conda": {},
        "info": {"subdir": "noarch"},
    }
    conda_channel_fixture._repodata_dict = test_repodata_dict
    result_noarch = conda_channel_fixture.filter_repodata(test_pkgs, platform="noarch")
    assert set(expected_noarch.keys()) == set(result_noarch.keys())
    for key in expected_noarch.keys():
        assert expected_noarch[key] == result_noarch[key]


def test_filter_repodata_conda_noarch_package(conda_channel_fixture):
    test_pkgs = ["NOARCH_DUMMER_CONDA_PACKAGE2", "NOARCH_DUMMER_CONDA_PACKAGE1"]
    test_repodata_dict = {
        "linux-64": {},
        "noarch": {
            "info": {"subdir": "noarch"},
            "packages": {
                "NOARCH_DUMMER_PACKAGE1": {},
            },
            "packages.conda": {
                "NOARCH_DUMMER_CONDA_PACKAGE1": {},
                "NOARCH_DUMMER_CONDA_PACKAGE2": {},
            },
        },
    }
    expected_noarch = {
        "packages": {},
        "packages.conda": {
            "NOARCH_DUMMER_CONDA_PACKAGE1": {},
            "NOARCH_DUMMER_CONDA_PACKAGE2": {},
        },
        "info": {"subdir": "noarch"},
    }
    conda_channel_fixture._repodata_dict = test_repodata_dict
    result_noarch = conda_channel_fixture.filter_repodata(test_pkgs, platform="noarch")
    assert set(expected_noarch.keys()) == set(result_noarch.keys())
    for key in expected_noarch.keys():
        assert expected_noarch[key] == result_noarch[key]


def test_generate_repodata(conda_channel_fixture, tmp_path):
    test_pkgs = [
        "NOARCH_DUMMER_CONDA_PACKAGE2",
        "NOARCH_DUMMER_CONDA_PACKAGE1",
        "DUMMY_LINUX1",
    ]
    test_repodata_dict = {
        "linux-64": {
            "info": {"subdir": "linux-64"},
            "packages": {"DUMMY_LINUX1": {}},
            "packages.conda": {},
        },
        "noarch": {
            "info": {"subdir": "noarch"},
            "packages": {
                "NOARCH_DUMMER_PACKAGE1": {},
            },
            "packages.conda": {
                "NOARCH_DUMMER_CONDA_PACKAGE1": {},
                "NOARCH_DUMMER_CONDA_PACKAGE2": {},
            },
        },
    }
    expected_noarch = {
        "packages": {},
        "packages.conda": {
            "NOARCH_DUMMER_CONDA_PACKAGE1": {},
            "NOARCH_DUMMER_CONDA_PACKAGE2": {},
        },
        "info": {"subdir": "noarch"},
    }

    expected_linux = {
        "packages": {"DUMMY_LINUX1": {}},
        "packages.conda": {},
        "info": {"subdir": "linux-64"},
    }
    ## noarch
    expected_file_path_noarch = tmp_path / "local_channel" / "noarch" / "repodata.json"
    conda_channel_fixture._repodata_dict = test_repodata_dict
    conda_channel_fixture.generate_repodata(test_pkgs)
    with open(expected_file_path_noarch, "r") as f:
        result_data = json.loads(f.read())
        assert expected_noarch == result_data

    # linux
    expected_file_path_linux = tmp_path / "local_channel" / "linux-64" / "repodata.json"
    with open(expected_file_path_linux, "r") as f:
        result_data = json.loads(f.read())
        assert expected_linux == result_data



@patch("requests.get")
def test_fetch_repodata(mock_get,unfiltered_repo_data_response):
    mock_get.return_value = _mock_response(json_data=unfiltered_repo_data_response)
    input_packages = ["python-3.9.5-h12debd9_4.tar.bz2", "tk-8.6.10-hbc83047_0.conda"]
    expected_value = {
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

    result = fetch_repodata(input_packages)
    assert result == expected_value


def test_parse_environment_file(minimal_environment):
    expected_output = ["python=3.9.5"]
    actual_output = parse_environment(minimal_environment)
    assert actual_output == expected_output


def test__fix_extensions(
    conda_channel_fixture, python_395_pkg_list, dot_conda_and_tar_list, repodata_output
):
    test_conda_channel = conda_channel_fixture

    test_conda_channel._repodata_dict = {"linux-64": repodata_output}

    actual_result = test_conda_channel._fix_extensions(
        python_395_pkg_list, platform="linux-64"
    )
    expected_result = dot_conda_and_tar_list

    assert set(actual_result) == set(expected_result)


def test_format_manifest(conda_channel_fixture, repodata_output):
    test_conda_channel = conda_channel_fixture
    test_conda_channel._repodata_dict = {"linux-64": repodata_output}

    actual_result = test_conda_channel.format_manifest(
        ["python-3.9.5-h12debd9_4.tar.bz2"],
        platform="linux-64",
    )

    expected_result = [
        {
            "url": "https://repo.anaconda.com/pkgs/main/linux-64/python-3.9.5-h12debd9_4.tar.bz2",
            "name": "python-3.9.5-h12debd9_4.tar.bz2",
            "validation": {
                "type": "sha256",
                "value": "7fc98fe684cb716a8d19cf20a77ccce3cda3f6da968abaade63edbe006d8f3ba"
            },
        }
    ]

    if actual_result != expected_result:
        print('act', actual_result)
        print('exp', expected_result)

    assert actual_result == expected_result


@patch("conda_vendor.core.CondaChannel.improved_download")
def test_download_and_validate_correct_sha(mock_get, tmp_path):

    expected_raw = bytearray([45, 23, 8, 64, 1])
    mock_get.return_value = _mock_response(content=expected_raw)
    expected_hash = hashlib.sha256(expected_raw).hexdigest()

    output = tmp_path / "downloads"
    fake_url = "https://my.downloads.to/data.tar.bz2"
    CondaChannel.download_and_validate(
        output, fake_url, expected_hash
    )

    with open(output, "rb") as f:
        assert f.read() == expected_raw


@patch("conda_vendor.core.CondaChannel.improved_download")
def test_download_and_validate_incorrect_sha(mock_get, tmp_path):
    expected_raw = bytearray([45, 23, 8, 64, 1])
    mock_get.return_value = _mock_response(content=expected_raw)
    expected_incorrect_hash = hashlib.sha256(bytearray([8, 64, 1])).hexdigest()

    output = tmp_path / "downloads"
    fake_url = "https://my.downloads.to/data.tar.bz2"
    with pytest.raises(RuntimeError) as error:
        CondaChannel.download_and_validate(
            output, fake_url, expected_incorrect_hash
        )
        assert "invalid checksum type: " in str(error)


def _mock_response(
        status=200,
        content= b"CONTENT",
        json_data=None,
        raise_for_status=None):
    """
    since we typically test a bunch of different
    requests calls for a service, we are going to do
    a lot of mock responses, so its usually a good idea
    to have a helper function that builds these things
    """
    mock_resp = Mock()
    # mock raise_for_status call w/optional error
    mock_resp.raise_for_status = Mock()
    if raise_for_status:
        mock_resp.raise_for_status.side_effect = raise_for_status
    # set status code and content
    mock_resp.status_code = status
    mock_resp.content = content
    # add json data if provided
    if json_data:
        mock_resp.json = Mock(
            return_value=json_data
        )
    return mock_resp

@patch("conda_vendor.core.CondaChannel.improved_download")
def test_download_binaries_core( mock_get, tmp_path, conda_channel_fixture):
    expected_sha = hashlib.sha256(bytearray([9, 9, 9])).hexdigest()
    test_manifest_dict =  {
        "resources": [
            {
                "url": "https://repo.anaconda.com/pkgs/main/linux-64/_libgcc_mutex-0.1-main.conda",
                "name": "_libgcc_mutex-0.1-main.conda",
                "validation": {
                    "type": "sha256",
                    "value": expected_sha,
                },
            },
            {
                "url": "https://repo.anaconda.com/pkgs/main/noarch/tzdata-2020f-h52ac0ba_0.conda",
                "name": "tzdata-2020f-h52ac0ba_0.conda",
                "validation": {
                    "type": "sha256",
                    "value": expected_sha,
                },
            },
        ]
    }
    conda_channel_fixture.manifest = test_manifest_dict
    mock_resp = _mock_response(content=bytearray([9, 9, 9]))
    mock_get.return_value = mock_resp
    
    expected_linux_package_file_name = test_manifest_dict["resources"][0]["name"]
    expected_noarch_package_file_name = test_manifest_dict["resources"][1]["name"]
    expected_file_data = bytearray([9, 9, 9])
    conda_channel_fixture._requires_fetch = False
    conda_channel_fixture.download_binaries() 

    expected_linux_package_path = (
        tmp_path / "local_channel" / "linux-64" / expected_linux_package_file_name
    )
    expected_noarch_package_path = (
        tmp_path / "local_channel" / "noarch" / expected_noarch_package_file_name
    )

    assert expected_linux_package_path.exists()
    assert expected_noarch_package_path.exists()
    assert mock_get.call_count == 2
    for i, call in enumerate(mock_get.get.call_args_list):
        args, kwargs = call
        assert args[0] == test_manifest_dict["resources"][i]["url"]

    with open(expected_linux_package_path, "rb") as f:
        result_linux_file_data = f.read()
    assert expected_file_data == result_linux_file_data

    with open(expected_noarch_package_path, "rb") as f:
        result_no_arch_file_data = f.read()
    assert expected_file_data == result_no_arch_file_data


"""
      {
                "url": "https://repo.anaconda.com/pkgs/main/linux-64/libgcc-ng-9.3.0-h5101ec6_17.conda",
                "name": "libgcc-ng-9.3.0-h5101ec6_17.conda",
                "validation": {
                    "type": "sha256",
                    "value": "49a808720a51c107241a42ac3641cce3d8451ef7cfaf3d68b6e4a3fec2da0676",
                },

"""
@patch("conda_vendor.core.CondaChannel.solve_environment")
def test_get_manifest_conda_forge(mock, fixture_conda_lock_solve_response,conda_channel_fixture):
    expected_name = "conda-mirror-0.8.2-py_1.tar.bz2"
    mock.return_value = fixture_conda_lock_solve_response
    result_manifest = get_manifest(conda_channel_fixture)
    result_pkg_names = [d['name'] for d in result_manifest]

    assert expected_name in result_pkg_names

@patch("conda_vendor.core.CondaChannel.solve_environment")
def test_create_manifest_small(mock, fixture_conda_lock_small_response ,conda_channel_fixture, tmp_path):

     expected_manifest =    [
        {
        'url': 'https://conda.anaconda.org/main/linux-64/readline-8.1-h27cfd23_0.tar.bz2', 
        'name': 'readline-8.1-h27cfd23_0.tar.bz2', 
        'validation': {'type': 'sha256', 'value': 'fa1a041badf4beeba06f51b17a3214a5509015eef4daf1925d01c207f6b00ca7'}
        }
     ]
     expected_path = tmp_path / "vendor_manifest.yaml"
     mock.return_value = fixture_conda_lock_small_response
     create_manifest(conda_channel_fixture)
     assert expected_path.exists()
     with open(expected_path, "r") as f : 
         result_manifest = yaml.load(f, Loader=SafeLoader)
     TestCase().assertDictEqual(result_manifest[0], expected_manifest[0])


@patch("conda_vendor.core.CondaChannel.solve_environment")
def test_create_manifest_count_entries(mock, fixture_conda_lock_solve_response, conda_channel_fixture, tmp_path):
     expected_path = tmp_path / "vendor_manifest.yaml"
     mock.return_value = fixture_conda_lock_solve_response
     create_manifest(conda_channel_fixture)
     assert expected_path.exists()
     with open(expected_path, "r") as f : 
         result_manifest = yaml.load(f, Loader=SafeLoader)
     assert len(result_manifest) == len(fixture_conda_lock_solve_response)


def test_get_local_environment_yaml(conda_channel_fixture,tmp_path):
     result_yaml = get_local_environment_yaml(conda_channel_fixture)
     expected_yaml = {'name': 'local_minimal_env', 
     'channels': [f'file://{tmp_path}/local_channel', 'nodefaults'], 
     'dependencies': ['python=3.9.5', 'conda-mirror']}
     TestCase().assertDictEqual(expected_yaml, result_yaml)

def test_get_local_environment_yaml_custom_name(conda_channel_fixture,tmp_path):
     result_yaml = get_local_environment_yaml(conda_channel_fixture,local_environment_name="THE_BEST_ENV")
     expected_yaml = {'name': 'THE_BEST_ENV', 
     'channels': [f'file://{tmp_path}/local_channel', 'nodefaults'], 
     'dependencies': ['python=3.9.5', 'conda-mirror']}
     TestCase().assertDictEqual(expected_yaml, result_yaml)

def test_create_local_environment(conda_channel_fixture,tmp_path):
     create_local_environment_yaml(conda_channel_fixture)
     expected_path = tmp_path /"local_yaml.yaml"
     expected_yaml = {'name': 'local_minimal_env', 
     'channels': [f'file://{tmp_path}/local_channel', 'nodefaults'], 
     'dependencies': ['python=3.9.5', 'conda-mirror']}
     with open(expected_path,  "r" ) as f:
         result_yaml = yaml.load(f, Loader=SafeLoader)
     TestCase().assertDictEqual(expected_yaml, result_yaml)


def test_create_local_environment_named(conda_channel_fixture,tmp_path):
     filename = 'out.yml'
     create_local_environment_yaml(conda_channel_fixture,
        local_environment_name='DUMMY_ENV',
        local_environment_filename=filename
     )
     expected_path = tmp_path / filename
     expected_yaml = {'name': 'DUMMY_ENV', 
     'channels': [f'file://{tmp_path}/local_channel', 'nodefaults'], 
     'dependencies': ['python=3.9.5', 'conda-mirror']}
     with open(expected_path,  "r" ) as f:
         result_yaml = yaml.load(f, Loader=SafeLoader)
     TestCase().assertDictEqual(expected_yaml, result_yaml)



@patch("conda_vendor.core.CondaChannel.solve_environment")
def test_generate_repo_data(mock, fixture_conda_lock_small_response,  conda_channel_fixture):
    expected_repo_data_dict = {
    'linux-64': {
        'info': {'subdir': 'linux-64'}, 
        'packages': {'readline-8.1-h27cfd23_0.tar.bz2': 
            {'build': 'h27cfd23_0', 
            'build_number': 0, 'constrains': [], 'depends': ['libgcc-ng >=7.3.0', 
            'ncurses >=6.2,<7.0a0'], 
            'license': 'GPL-3.0',
            'md5': 'b3a5e0e61af068595cfd411db9960e1f', 
            'name': 'readline', 
            'platform': 'linux', 
            'sha256': 'fa1a041badf4beeba06f51b17a3214a5509015eef4daf1925d01c207f6b00ca7',
            'size': 475570, 
            'subdir': 'linux-64',
            'timestamp': 1611868595060, 
            'version': '8.1'}
            }, 
        'packges.conda': {}
        }, 
     'noarch': {
        'info': {'subdir': 'noarch'}, 
        'packages': {}, 
        'packges.conda': {}
        }
    }
    mock.return_value = fixture_conda_lock_small_response
    result = conda_channel_fixture.generate_repo_data()
    print(result)
    TestCase().assertDictEqual(expected_repo_data_dict, result)

def test_write_arch_repo_data(conda_channel_fixture):
    expected_path = conda_channel_fixture.local_channel /"linux-64" / "repodata.json"
    expected_repo_data = {
        'info': {'subdir': 'linux-64'}, 
        'packages': {'readline-8.1-h27cfd23_0.tar.bz2': 
            {'build': 'h27cfd23_0', 
            'build_number': 0, 'constrains': [], 'depends': ['libgcc-ng >=7.3.0', 
            'ncurses >=6.2,<7.0a0'], 
            'license': 'GPL-3.0',
            'md5': 'b3a5e0e61af068595cfd411db9960e1f', 
            'name': 'readline', 
            'platform': 'linux', 
            'sha256': 'fa1a041badf4beeba06f51b17a3214a5509015eef4daf1925d01c207f6b00ca7',
            'size': 475570, 
            'subdir': 'linux-64',
            'timestamp': 1611868595060, 
            'version': '8.1'}
            }, 
        'packges.conda': {}
        }

    conda_channel_fixture.all_repo_data = {
    'linux-64': {
        'info': {'subdir': 'linux-64'}, 
        'packages': {'readline-8.1-h27cfd23_0.tar.bz2': 
            {'build': 'h27cfd23_0', 
            'build_number': 0, 'constrains': [], 'depends': ['libgcc-ng >=7.3.0', 
            'ncurses >=6.2,<7.0a0'], 
            'license': 'GPL-3.0',
            'md5': 'b3a5e0e61af068595cfd411db9960e1f', 
            'name': 'readline', 
            'platform': 'linux', 
            'sha256': 'fa1a041badf4beeba06f51b17a3214a5509015eef4daf1925d01c207f6b00ca7',
            'size': 475570, 
            'subdir': 'linux-64',
            'timestamp': 1611868595060, 
            'version': '8.1'}
            }, 
        'packges.conda': {}
        }, 
     'noarch': {
        'info': {'subdir': 'noarch'}, 
        'packages': {}, 
        'packges.conda': {}
        }
    }

    conda_channel_fixture.write_arch_repo_data("linux-64")
    with open(expected_path, "r") as f :
        result =  json.loads(f.read())

    TestCase().assertDictEqual(expected_repo_data, result)
    
    

    



def test_write_repo_data( conda_channel_fixture, tmp_path):
    expected_path_linux = conda_channel_fixture.local_channel /"linux-64" / "repodata.json"
    expected_path_noarch = conda_channel_fixture.local_channel /"noarch" / "repodata.json"
    conda_channel_fixture.all_repo_data = {
    'linux-64': {
        'info': {'subdir': 'linux-64'}, 
        'packages': {'readline-8.1-h27cfd23_0.tar.bz2': 
            {'build': 'h27cfd23_0', 
            'build_number': 0, 'constrains': [], 'depends': ['libgcc-ng >=7.3.0', 
            'ncurses >=6.2,<7.0a0'], 
            'license': 'GPL-3.0',
            'md5': 'b3a5e0e61af068595cfd411db9960e1f', 
            'name': 'readline', 
            'platform': 'linux', 
            'sha256': 'fa1a041badf4beeba06f51b17a3214a5509015eef4daf1925d01c207f6b00ca7',
            'size': 475570, 
            'subdir': 'linux-64',
            'timestamp': 1611868595060, 
            'version': '8.1'}
            }, 
        'packges.conda': {}
        }, 
     'noarch': {
        'info': {'subdir': 'noarch'}, 
        'packages': {}, 
        'packges.conda': {}
        }
    }
    expected_linux = conda_channel_fixture.all_repo_data['linux-64']
    expected_noarch = conda_channel_fixture.all_repo_data['noarch']
    conda_channel_fixture.write_repo_data()

    with open(expected_path_linux, "r") as f :
        result_linux =  json.loads(f.read())
    TestCase().assertDictEqual(expected_linux, result_linux)

    with open(expected_path_noarch, "r") as f :
        result_noarch =  json.loads(f.read())
    TestCase().assertDictEqual(expected_noarch, result_noarch)


    
    
    



    




     


