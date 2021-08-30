import hashlib
import json
import yaml
from requests import Response
from unittest import TestCase
from unittest.mock import Mock, patch, call, mock_open
from yaml import safe_load
from yaml.loader import SafeLoader

from conda_vendor.core import (
    improved_download,
    get_conda_platform,
    get_manifest,
    create_manifest,
    CondaChannel,
    get_local_environment_yaml,
    create_local_environment_yaml,
    LockWrapper,
)
from .conftest import mock_response


@patch("requests.Session.get")
def test_improved_download(mock) -> None:
    mock.return_value = Mock(Response)
    test_url = "https://NOT_REAL.com"
    result = improved_download(test_url)
    result_called_with = mock.call_args[0][0]
    assert result_called_with == test_url
    assert mock.call_count == 1
    assert isinstance(result, Response)


@patch("struct.calcsize")
def test_get_conda_platform(mock_struct) -> None:
    test_platform = "linux"
    mock_struct.return_value = 4
    expected = "linux-32"
    result = get_conda_platform(test_platform)
    assert expected == result
    assert mock_struct.call_count == 1


def test_CondaChannel_init(minimal_environment):
    conda_channel = CondaChannel(minimal_environment)

    expected_platforms = [conda_channel.platform, "noarch"]
    for platform in expected_platforms:
        assert platform in conda_channel.valid_platforms
    assert "python=3.9.5" in conda_channel.env_deps["specs"]
    assert "main" in conda_channel.channels


# need init test hurrr
def test_CondaChannel_init_manifest_exist(minimal_environment, tmp_path):
    dummy_manifest = {}
    dummy_manifest_data = [
        {
            "url": "https://conda.anaconda.org/wonderland/osx-64/wrong_rabbit-1.0-pyhfhfhfhf.tar.bz2",
            "filename": "wrong_rabbit.tar.bz2",
            "validation": {"type": "sha256", " value": "POOOBEAR"},
        }
    ]
    dummy_manifest["resources"] = dummy_manifest_data

    expected_manifest = dummy_manifest

    dummy_manifest_path = tmp_path / "dummy_manifest.yml"
    with open(dummy_manifest_path, "w") as f:
        yaml.dump(dummy_manifest, f, sort_keys=False)

    conda_channel = CondaChannel(
        minimal_environment, channel_root=tmp_path, manifest_path=dummy_manifest_path
    )
    result_manifest = conda_channel.manifest
    result_platforms = [conda_channel.platform, "noarch"]

    for platform in result_platforms:
        assert platform in conda_channel.valid_platforms
    assert "wrong_rabbit=1.0" in conda_channel.env_deps["specs"]
    assert "wonderland" in conda_channel.channels
    TestCase().assertDictEqual(result_manifest, expected_manifest)


def test_CondaChannel_init_conda_forge(minimal_conda_forge_environment):
    conda_channel = CondaChannel(minimal_conda_forge_environment)

    expected_platforms = [conda_channel.platform, "noarch"]
    for platform in expected_platforms:
        assert platform in conda_channel.valid_platforms

    expected_packages = ["python=3.9.5", "conda-mirror=0.8.2"]
    for pkg in expected_packages:
        assert pkg in conda_channel.env_deps["specs"]

    expected_channels = ["main", "conda-forge"]
    for chan in expected_channels:
        assert chan in conda_channel.channels


def test_CondaChannel_init_excludes_nodefaults(tmp_path):
    def create_environment(tmp_path):
        content = """name: minimal_env
channels:
- main
- nodefaults
dependencies:
- python=3.9.5"""
        fn = tmp_path / "env.yml"
        with fn.open("w") as f:
            f.write(content)
        return fn

    environment_yml = create_environment(tmp_path)
    conda_channel = CondaChannel(environment_yml)

    assert "main" in conda_channel.channels
    assert "nodefaults" not in conda_channel.channels


@patch("conda_vendor.core.LockWrapper.solve")
def test_CondaChannel_solve_environment(mock, conda_channel_fixture):
    platform = conda_channel_fixture.platform
    mock_data = {"actions": {"FETCH": [{"DUMMY_KEY": "DUMMY_VAL"}], "LINK": []}}
    mock.return_value = mock_data
    expected = mock_data["actions"]["FETCH"]
    result = conda_channel_fixture.solve_environment()
    assert mock.call_count == 1
    mock.assert_called_with(
        "conda",
        ["main", "conda-forge"],
        specs=["python=3.9.5", "conda-mirror=0.8.2"],
        platform=platform,
    )
    TestCase().assertDictEqual(result[0], expected[0])


def test_CondaChannel_get_extended_data(conda_channel_fixture):
    platform = conda_channel_fixture.platform
    test_env_deps_solution = {
        "actions": {
            "FETCH": [
                {"channel": f"https://conda.anaconda.org/main/{platform}"},
                {"channel": "https://conda.anaconda.org/main/noarch"},
                {"channel": "https://conda.anaconda.org/conda-forge/noarch"},
                {"channel": f"https://conda.anaconda.org/main/{platform}"},
            ],
            "LINK": [],
        }
    }

    expected = {
        "main": {
            f"{platform}": {
                "repodata_url": [
                    f"https://conda.anaconda.org/main/{platform}/repodata.json"
                ],
                "entries": [
                    {"channel": f"https://conda.anaconda.org/main/{platform}"},
                    {"channel": f"https://conda.anaconda.org/main/{platform}"},
                ],
            },
            "noarch": {
                "repodata_url": [
                    "https://conda.anaconda.org/main/noarch/repodata.json"
                ],
                "entries": [{"channel": "https://conda.anaconda.org/main/noarch"}],
            },
        },
        "conda-forge": {
            f"{platform}": {"repodata_url": [], "entries": []},
            "noarch": {
                "repodata_url": [
                    "https://conda.anaconda.org/conda-forge/noarch/repodata.json"
                ],
                "entries": [
                    {"channel": "https://conda.anaconda.org/conda-forge/noarch"}
                ],
            },
        },
    }

    conda_channel_fixture.env_deps["solution"] = test_env_deps_solution
    result = conda_channel_fixture.get_extended_data()
    TestCase().assertDictEqual(result, expected)


def test_CondaChannel_get_manifest(conda_channel_fixture):
    platform = conda_channel_fixture.platform

    test_env_deps_solution = {
        "actions": {
            "FETCH": [
                {
                    "channel": f"http://fake.com/main/{platform}",
                    "url": f"https://fake.com/main/{platform}/name1",
                    "fn": "name1",
                    "sha256": "sha1",
                },
                {
                    "channel": f"http://fake.com/main/noarch",
                    "url": f"https://fake.com/main/noarch/name2",
                    "fn": "name2",
                    "sha256": "sha2",
                },
                {
                    "channel": f"http://fake.com/conda-forge/{platform}",
                    "url": f"https://fake.com/conda-forge/{platform}/name3",
                    "fn": "name3",
                    "sha256": "sha3",
                },
                {
                    "channel": f"http://fake.com/main/{platform}",
                    "url": f"https://fake.com/main/{platform}/_name4",
                    "fn": "name4",
                    "sha256": "sha4",
                },
            ],
            "LINK": [],
        }
    }
    conda_channel_fixture.env_deps["solution"] = test_env_deps_solution

    expected_vendor_manifest = {
        "resources": [
            {
                "url": f"https://fake.com/main/{platform}/name1",
                "filename": "name1",
                "validation": {"type": "sha256", "value": "sha1",},
            },
            {
                "url": f"https://fake.com/main/noarch/name2",
                "filename": "name2",
                "validation": {"type": "sha256", "value": "sha2",},
            },
            {
                "url": f"https://fake.com/conda-forge/{platform}/name3",
                "filename": "name3",
                "validation": {"type": "sha256", "value": "sha3",},
            },
            {
                "url": f"https://fake.com/main/{platform}/_name4",
                "filename": "name4",
                "validation": {"type": "sha256", "value": "sha4",},
            },
        ]
    }

    result = conda_channel_fixture.get_manifest()
    expected = expected_vendor_manifest
    TestCase().assertDictEqual(result, expected)


@patch("conda_vendor.core.CondaChannel.get_manifest")
def test_CondaChannel_create_manifest(mock, conda_channel_fixture):
    platform = conda_channel_fixture.platform
    expected_path = conda_channel_fixture.channel_root / "vendor_manifest.yaml"
    expected = {
        "resources": [
            {
                "url": f"https://fake.com/main/{platform}/name1",
                "filename": "name1",
                "validation": {"type": "sha256", "value": "sha1",},
            }
        ]
    }
    mock.return_value = expected
    conda_channel_fixture.create_manifest()
    with open(expected_path, "r") as f:
        result = yaml.load(f, Loader=SafeLoader)
    TestCase().assertDictEqual(result, expected)
    mock.assert_called_with()
    assert mock.call_count == 1


def test_CondaChannel_get_local_environment_yaml(conda_channel_fixture):
    expected = {
        "name": "local_minimal_conda_forge_env",
        "channels": [
            f"file://{conda_channel_fixture.channel_root}/local_main",
            f"file://{conda_channel_fixture.channel_root}/local_conda-forge",
            "nodefaults",
        ],
        "dependencies": ["python=3.9.5", "conda-mirror=0.8.2"],
    }

    result = conda_channel_fixture.get_local_environment_yaml()
    TestCase().assertDictEqual(result, expected)


@patch("conda_vendor.core.CondaChannel.get_local_environment_yaml")
def test_CondaChannel_create_local_environment_yaml(mock, conda_channel_fixture):
    expected = {
        "name": "local_minimal_conda_forge_env",
        "channels": ["dummy_channel"],
        "dependencies": ["python=3.9.5", "conda-mirror=0.8.2"],
    }
    mock.return_value = expected
    conda_channel_fixture.create_local_environment_yaml()
    expected_file = conda_channel_fixture.channel_root / "local_yaml.yaml"
    with open(expected_file, "r") as f:
        result = yaml.load(f, Loader=SafeLoader)
    TestCase().assertDictEqual(result, expected)
    mock.assert_called_with(local_environment_name=None)
    assert mock.call_count == 1


@patch("conda_vendor.core.improved_download")
def test_CondaChannel_fetch_and_filter(mock_download, conda_channel_fixture):
    platform = conda_channel_fixture.platform
    fake_extended_repo_data = {
        "repodata_url": ["https://url1", "https://url2"],
        "entries": [{"fn": "file1"}, {"fn": "file2"}, {"fn": "file3"},],
    }
    fake_live_repo_data_json = {
        "info": {"subdir": "fake_subdir"},
        "packages": {
            "file1": {"id": 1},
            "badfile1": {"id": 2},
            "file2": {"id": 3},
            "badfile2": {"id": 4},
        },
        "packages.conda": {
            "file3": {"id": 5},
            "badfile3": {"id": 6},
            "file4": {"id": 7},
            "badfile4": {"id": 8},
        },
    }
    expected = {
        "info": {"subdir": "fake_subdir"},
        "packages": {"file1": {"id": 1}, "file2": {"id": 3},},
        "packages.conda": {"file3": {"id": 5}},
    }

    allowed_calls = [call(url) for url in fake_extended_repo_data["repodata_url"]]

    mock_download.return_value = mock_response(json_data=fake_live_repo_data_json)

    result = conda_channel_fixture.fetch_and_filter(
        "fake_subdir", fake_extended_repo_data
    )

    assert mock_download.call_args in allowed_calls
    assert mock_download.call_count == 1

    print("allowed_calls", allowed_calls)
    print("mock", mock_download.call_args)
    assert 0
    TestCase().assertDictEqual(result, expected)


def test_CondaChannel_fetch_and_filter_nopackages(conda_channel_fixture):
    expected = {"info": {"subdir": "fake_subdir"}, "packages": {}, "packages.conda": {}}
    fake_repo_data = {"repodata_url": []}
    result = conda_channel_fixture.fetch_and_filter("fake_subdir", fake_repo_data)
    TestCase().assertDictEqual(result, expected)


@patch("conda_vendor.core.CondaChannel.fetch_and_filter")
@patch("conda_vendor.core.CondaChannel.get_extended_data")
def test_CondaChannel_get_all_repo_data(mock_data, mock_fetch, conda_channel_fixture):
    platform = conda_channel_fixture.platform
    conda_channel_fixture.channels = ["chan1", "chan2"]
    fake_extended_repo_data = {
        "chan1": {
            platform: {
                "repodata_url": ["https://url1", "https://url2"],
                "entries": [{"fn": "file1"}, {"fn": "file2"}],
            },
            "noarch": {
                "repodata_url": ["https://url3"],
                "entries": [{"fn": "file3"}, {"fn": "file4"}],
            },
        },
        "chan2": {
            platform: {
                "repodata_url": ["https://url4"],
                "entries": [{"fn": "file5"},],
            },
            "noarch": {
                "repodata_url": ["https://url5"],
                "entries": [{"fn": "file6"},],
            },
        },
    }

    expected_calls = [
        call(
            platform,
            {
                "repodata_url": ["https://url1", "https://url2"],
                "entries": [{"fn": "file1"}, {"fn": "file2"}],
            },
        ),
        call(
            "noarch",
            {
                "repodata_url": ["https://url3"],
                "entries": [{"fn": "file3"}, {"fn": "file4"}],
            },
        ),
        call(
            platform, {"repodata_url": ["https://url4"], "entries": [{"fn": "file5"}]}
        ),
        call(
            "noarch", {"repodata_url": ["https://url5"], "entries": [{"fn": "file6"}]}
        ),
    ]

    mock_data.return_value = fake_extended_repo_data
    mock_fetch.return_value = {}

    result = conda_channel_fixture.get_all_repo_data()
    TestCase().assertListEqual(mock_fetch.call_args_list, expected_calls)


def test_CondaChannel_local_channel_name(conda_channel_fixture):
    expected = "local_TEST_CHANNEL_NAME"
    result = conda_channel_fixture.local_channel_name(chan="TEST_CHANNEL_NAME")
    assert expected == result


@patch("conda_vendor.core.CondaChannel.local_channel_name")
def test_CondaChannel_local_dir(mock, conda_channel_fixture):
    mock_local_dir_name = "local_TEST_CHANNEL_NAME"
    mock.return_value = mock_local_dir_name
    test_channel_name = "TEST_CHANNEL_NAME"
    test_subdir = "dummy-64"
    expected = conda_channel_fixture.channel_root / mock_local_dir_name / test_subdir
    result = conda_channel_fixture.local_dir(chan=test_channel_name, subdir=test_subdir)
    assert result == expected
    mock.assert_called_with(test_channel_name)


@patch("conda_vendor.core.CondaChannel.local_dir")
def test_CondaChannel_make_local_dir(mock, conda_channel_fixture):
    mock_local_dir_name = "local_TEST_CHANNEL_NAME"
    test_local_dir_subdir = "dummy-64"
    expected_path = (
        conda_channel_fixture.channel_root / mock_local_dir_name / test_local_dir_subdir
    )

    test_channel_name = "TEST_CHANNEL_NAME"
    mock.return_value = expected_path
    result = conda_channel_fixture.make_local_dir(
        chan=test_channel_name, subdir=test_local_dir_subdir
    )
    assert result == expected_path
    assert expected_path.exists()
    mock.assert_called_with("TEST_CHANNEL_NAME", "dummy-64")


@patch("conda_vendor.core.CondaChannel.make_local_dir")
def test_CondaChannel_write_arch_repo_data(mock_mkdir, conda_channel_fixture):
    new_dir = conda_channel_fixture.channel_root / "tmp"
    new_dir.mkdir(exist_ok=True, parents=True)
    new_file = new_dir / "repodata.json"

    assert not new_file.exists()

    expected_chan = "dummy_chan"
    expected_subdir = "dummy_subdir"
    expected = {"data": "garbage"}

    def on_mkdir(chan, subdir):
        assert chan == expected_chan
        assert subdir == expected_subdir
        return new_dir

    mock_mkdir.side_effect = on_mkdir

    conda_channel_fixture.write_arch_repo_data(
        chan=expected_chan, subdir=expected_subdir, repo_data=expected
    )

    with new_file.open("r") as f:
        result = json.load(f)

    TestCase().assertDictEqual(result, expected)


@patch("conda_vendor.core.CondaChannel.write_arch_repo_data")
@patch("conda_vendor.core.CondaChannel.get_all_repo_data")
def test_CondaChannel_write_repo_data(mock_get, mock_write, conda_channel_fixture):
    platform = conda_channel_fixture.platform
    fake_repo_data = {
        "chan1": {platform: {"data": 1}, "noarch": {"data": 2}},
        "chan2": {platform: {"data": 3}, "noarch": {"data": 4}},
    }
    expected_calls = [
        call("chan1", platform, {"data": 1}),
        call("chan1", "noarch", {"data": 2}),
        call("chan2", platform, {"data": 3}),
        call("chan2", "noarch", {"data": 4}),
    ]
    mock_get.return_value = fake_repo_data
    conda_channel_fixture.write_repo_data()
    TestCase().assertListEqual(mock_write.call_args_list, expected_calls)


def test_CondaChannel__calc_sha256():
    test_data = b"DUMMY"
    expected = hashlib.sha256(b"DUMMY").hexdigest()
    result = CondaChannel._calc_sha256(test_data)
    assert expected == result


@patch("conda_vendor.core.improved_download")
def test_CondaChannel_download_and_validate(mock, tmp_path):
    expected_raw = b"DUMMY_DATA"
    expected_path = tmp_path / "dummy.data"
    expected_hash = hashlib.sha256(expected_raw).hexdigest()
    expected_url = "https://should_have_been_a_doctor.com"
    mock.return_value = mock_response(content=expected_raw)
    CondaChannel.download_and_validate(
        out=expected_path, url=expected_url, sha256=expected_hash
    )
    with open(expected_path, "rb") as f:
        assert f.read() == expected_raw
    mock.assert_called_with(expected_url)
    assert mock.call_count == 1


@patch("conda_vendor.core.CondaChannel.make_local_dir")
@patch("conda_vendor.core.CondaChannel.download_and_validate")
def test_CondaChannel_download_arch_binaries(
    mock_download_and_validate, mock_make_local_dir, conda_channel_fixture, tmp_path
):
    platform = conda_channel_fixture.platform
    test_channel = "dummy"
    test_subdir = "dummy-64"
    test_entries = [
        {
            "channel": f"http://fake.com/main/{platform}",
            "url": f"https://fake.com/main/{platform}/name1",
            "fn": "name1",
            "sha256": "sha1",
        }
    ]

    mock_path = tmp_path / test_channel / test_subdir
    expected_name = "name1"
    expected_destination = mock_path / expected_name
    expected_download_and_validate_calls = (
        expected_destination,
        f"https://fake.com/main/{platform}/name1",
        "sha1",
    )
    mock_make_local_dir.return_value = mock_path
    conda_channel_fixture.download_arch_binaries(
        chan=test_channel, subdir=test_subdir, entries=test_entries
    )

    mock_download_and_validate.call_count == 1
    mock_make_local_dir.call_count == 1
    mock_make_local_dir.assert_called_with("dummy", "dummy-64")
    mock_download_and_validate.assert_called_with(*expected_download_and_validate_calls)


@patch("conda_vendor.core.CondaChannel.download_arch_binaries")
@patch("conda_vendor.core.CondaChannel.get_extended_data")
def test_CondaChannel_download_binaries(
    mock_data, mock_download, conda_channel_fixture
):

    platform = conda_channel_fixture.platform
    mock_extended_data = {
        "main": {
            f"{platform}": {
                "repodata_url": ["https://url1"],
                "entries": [{"id": 1}, {"id": 2}],
            },
            "noarch": {"repodata_url": ["https://url2"], "entries": [{"id": 3}]},
        },
        "conda-forge": {
            f"{platform}": {"repodata_url": [], "entries": []},
            "noarch": {"repodata_url": ["https://url3"], "entries": [{"id": 4}]},
        },
    }
    mock_data.return_value = mock_extended_data
    expected_calls = [
        call("main", platform, [{"id": 1}, {"id": 2}]),
        call("main", "noarch", [{"id": 3}]),
        call("conda-forge", platform, []),
        call("conda-forge", "noarch", [{"id": 4}]),
    ]

    conda_channel_fixture.download_binaries()

    actual_calls = mock_download.call_args_list
    TestCase().assertListEqual(expected_calls, actual_calls)


@patch("conda_vendor.core.CondaChannel.get_manifest")
def test_get_manifest(mock_get_manifest, conda_channel_fixture):
    mock_get_manifest.return_value = {}
    result = get_manifest(conda_channel_fixture)
    assert mock_get_manifest.call_count == 1


@patch("conda_vendor.core.CondaChannel.create_manifest")
def test_create_manifest(mock_create_manifest, conda_channel_fixture):
    test_manifest_name = "FAKE_NAME"
    mock_create_manifest.return_value = {}
    result = create_manifest(
        conda_channel_fixture, manifest_filename=test_manifest_name
    )
    mock_create_manifest.assert_called_once_with(manifest_filename="FAKE_NAME")


def test_get_local_environment_yaml(conda_channel_fixture):
    root = conda_channel_fixture.channel_root
    local_env_name = "TROPICAL_ENVIRONMENT_NAME"
    expected = {
        "name": local_env_name,
        "channels": [
            f"file://{(root / 'local_main').absolute()}",
            f"file://{(root / 'local_conda-forge').absolute()}",
            "nodefaults",
        ],
        "dependencies": ["python=3.9.5", "conda-mirror=0.8.2"],
    }
    result = get_local_environment_yaml(
        conda_channel_fixture, local_environment_name=local_env_name
    )

    TestCase().assertDictEqual(result, expected)


def test_create_local_environment_yamll(conda_channel_fixture):
    root = conda_channel_fixture.channel_root
    local_env_name = "TROPICAL_ENVIRONMENT_NAME"
    expected_name = "TROPICAL.yaml"
    expected = {
        "name": local_env_name,
        "channels": [
            f"file://{(root / 'local_main').absolute()}",
            f"file://{(root / 'local_conda-forge').absolute()}",
            "nodefaults",
        ],
        "dependencies": ["python=3.9.5", "conda-mirror=0.8.2"],
    }

    expected_file = root / expected_name
    create_local_environment_yaml(
        conda_channel_fixture,
        local_environment_name=local_env_name,
        local_environment_filename=expected_name,
    )

    with expected_file.open("r") as f:
        result = yaml.load(f, Loader=SafeLoader)

    TestCase().assertDictEqual(result, expected)


def test_LockWrapper_init():
    lw = LockWrapper()
    assert isinstance(lw, LockWrapper)


@patch("conda_vendor.core.LockWrapper.parse")
def test_LockWrapper_parse(mock):
    test_args = ["dummy_path.yaml", "dummy-64"]
    LockWrapper.parse(*test_args)
    print(mock.call_args)
    mock.assert_called_once_with("dummy_path.yaml", "dummy-64")


@patch("conda_vendor.core.LockWrapper.solve")
def test_LockWrapper_solve(mock):

    test_args = ["conda", ["dummy_channel"]]
    test_kwargs = {"specs": ["dummy_spec"], "platform": "dummy_platform"}
    LockWrapper.solve(*test_args, **test_kwargs)
    mock.assert_called_once_with(*test_args, **test_kwargs)


@patch("yaml.load")
def test_load_manifest(mock, conda_channel_fixture, tmp_path):
    test_manifest_path = tmp_path / "test_manifest.yml"
    with open(test_manifest_path, "w") as y:
        y.write("test")
    conda_channel_fixture.load_manifest(test_manifest_path)
    mock.assert_called_once_with = [test_manifest_path, yaml.SafeLoader]


def test_instantiate_conda_lock_fetch_from_manifest_file(conda_channel_fixture):
    test_manifest = {}
    test_manifest_data = [
        {
            "url": "https://conda.anaconda.org/wonderland/osx-64/wrong_rabbit.tar.bz2",
            "filename": "wrong_rabbit.tar.bz2",
            "validation": {"type": "sha256", "value": "POOOBEAR"},
        }
    ]
    test_manifest["resources"] = test_manifest_data
    expected_fetch = {
        "actions": {
            "FETCH": [
                {
                    "url": "https://conda.anaconda.org/wonderland/osx-64/wrong_rabbit.tar.bz2",
                    "channel": "https://conda.anaconda.org/wonderland/osx-64",
                    "fn": "wrong_rabbit.tar.bz2",
                    "sha256": "POOOBEAR",
                }
            ]
        }
    }

    conda_channel_fixture.manifest = test_manifest
    conda_channel_fixture.instantiate_conda_lock_fetch_from_manifest_file()
    result_fetch = conda_channel_fixture.env_deps["solution"]
    TestCase().assertDictEqual(result_fetch, expected_fetch)


def test_CondaChannel_get_package_entry(conda_channel_fixture):
    test_filename1 = "mydummypkg1-1.1.94-pydwefwef.tar.bz"
    test_filename2 = "mydummypkg2-1-pydwefwef.tar.bz"

    result1 = conda_channel_fixture.get_package_entry(test_filename1)
    result2 = conda_channel_fixture.get_package_entry(test_filename2)

    expected1 = "mydummypkg1=1.1.94"
    expected2 = "mydummypkg2=1"

    assert result1 == expected1
    assert result2 == expected2


def test_CondaChannel_get_yaml_from_manifest(conda_channel_fixture, tmp_path):
    dummy_manifest = {}
    dummy_manifest_data = [
        {
            "url": "https://conda.anaconda.org/wonderland/osx-64/wrong_rabbit-1.0-pyhfhfhfhf.tar.bz2",
            "filename": "wrong_rabbit.tar.bz2",
            "validation": {"type": "sha256", " value": "POOOBEAR"},
        }
    ]
    dummy_manifest["resources"] = dummy_manifest_data

    expected_env_yaml = {
        "name": "conda_vendor_env",
        "channels": ["wonderland"],
        "dependencies": ["wrong_rabbit=1.0"],
    }

    dummy_manifest_path = tmp_path / "dummy_manifest.yml"
    with open(dummy_manifest_path, "w") as f:
        yaml.dump(dummy_manifest, f, sort_keys=False)

    result = conda_channel_fixture.get_yaml_from_manifest(dummy_manifest)
    TestCase().assertDictEqual(result, expected_env_yaml)


def test_get_yaml_channel_basepath(conda_channel_fixture):
    test_destination_channel_root = "mcdonalds"
    expected_return_alternate_root = "mcdonalds"

    test_conda_channel = conda_channel_fixture
    expected_return_default_root = test_conda_channel.channel_root

    actual_return_alternate_root = test_conda_channel.get_yaml_channel_basepath(
        test_destination_channel_root
    )
    assert expected_return_alternate_root == actual_return_alternate_root

    actual_return_default_root = test_conda_channel.get_yaml_channel_basepath()
    assert expected_return_default_root == actual_return_default_root


# def test_get_yaml_channel_basepath(conda_channel_fixture, minimal_conda_forge_environment):
#     with open(minimal_conda_forge_environment, "r") as f:
#         test_yaml = yaml.load(f, Loader=SafeLoader)

#     expected_yaml = test_yaml.copy()
#     destination_path = 'mcdonalds'
#     expected_yaml['channels'] = [f'{destination_path}/main', f'{destination_path}/conda-forge']

#     expected_dict = {
#         "name": "minimal_conda_forge_env"
#         "channels": [f'{destination_path}/main', f'{destination_path}/conda-forge']
#         "dependencies": ["python=3.9.5", "conda-mirror=0.8.2"]
#     }


# content = """name: minimal_conda_forge_env
# channels:
# - main
# - conda-forge
# dependencies:
# - python=3.9.5
# - conda-mirror=0.8.2
# """
#     fn = tmpdir_factory.mktemp("minimal_env").join("env.yml")
#     fn.write(content)
#     return fn
#     return 0
