import struct
import sys
from unittest.mock import Mock

import pytest
import yaml

from conda_vendor.conda_channel import CondaChannel
from conda_vendor.manifest import MetaManifest


def get_conda_platform(platform=sys.platform):
    _platform_map = {
        "linux2": "linux",
        "linux": "linux",
        "darwin": "osx",
        "win32": "win",
        "zos": "zos",
    }

    bits = struct.calcsize("P") * 8
    return f"{_platform_map[platform]}-{bits}"


@pytest.fixture(scope="function")
def get_path_location_for_manifest_fixture(tmpdir_factory):
    platform = get_conda_platform()
    fixture_manifest = {
        "main": {
            "noarch": {"repodata_url": None, "entries": []},
            f"{platform}": {
                "repodata_url": f"https://conda.anaconda.org/main/{platform}/repodata.json",
                "entries": [
                    {
                        "url": f"https://conda.anaconda.org/main/{platform}/brotlipy-0.7.0-py39h27cfd23_1003.tar.bz2",
                        "name": "brotlipy",
                        "version": "0.7.0",
                        "channel": f"https://conda.anaconda.org/main/{platform}",
                        "purl": f"pkg:conda/brotlipy@0.7.0?url=https://conda.anaconda.org/main/{platform}/brotlipy-0.7.0-py39h27cfd23_1003.tar.bz2",
                    }
                ],
            },
        },
        "conda-forge": {
            "noarch": {
                "repodata_url": "https://conda.anaconda.org/conda-forge/noarch/repodata.json",
                "entries": [
                    {
                        "url": "https://conda.anaconda.org/conda-forge/noarch/ensureconda-1.4.1-pyhd8ed1ab_0.tar.bz2",
                        "name": "ensureconda",
                        "version": "1.4.1",
                        "channel": "https://conda.anaconda.org/conda-forge/noarch",
                        "purl": "pkg:conda/ensureconda@1.4.1?url=https://conda.anaconda.org/conda-forge/noarch/ensureconda-1.4.1-pyhd8ed1ab_0.tar.bz2",
                    }
                ],
            },
            f"{platform}": {"repodata_url": None, "entries": []},
        },
    }

    fn = tmpdir_factory.mktemp("minimal_env").join("env.yml")
    with open(fn, "w") as f:
        yaml.dump(fixture_manifest, f, sort_keys=False)

    return fn


@pytest.fixture(scope="function")
def minimal_environment(tmpdir_factory):
    content = """name: minimal_env
channels:
- main
dependencies:
- python=3.9.5"""
    fn = tmpdir_factory.mktemp("minimal_env").join("env.yml")
    fn.write(content)
    return fn


@pytest.fixture(scope="function")
def minimal_environment_defaults(tmpdir_factory):
    content = """name: minimal_env
channels:
- main
- defaults
dependencies:
- python=3.9.5"""
    fn = tmpdir_factory.mktemp("minimal_env").join("env.yml")
    fn.write(content)
    return fn


@pytest.fixture(scope="function")
def minimal_conda_forge_environment(tmpdir_factory):
    content = """name: minimal_conda_forge_env
channels:
- main
- conda-forge
dependencies:
- python=3.9.5
- conda-mirror=0.8.2
"""
    fn = tmpdir_factory.mktemp("minimal_env").join("env.yml")
    fn.write(content)
    return fn


@pytest.fixture
def minimal_manifest():
    platform = get_conda_platform()
    if platform == "linux-64":
        return {
            "resources": [
                {
                    "url": "https://conda.anaconda.org/main/noarch/six-1.16.0-pyhd3eb1b0_0.tar.bz2",
                    "filename": "six-1.16.0-pyhd3eb1b0_0.tar.bz2",
                    "validation": {
                        "type": "sha256",
                        "value": "142b5c736cfec8981e631d63f2b0860ce31775cf24d1b5b504dbafbec6561c88",
                    },
                },
                {
                    "url": "https://conda.anaconda.org/main/linux-64/ncurses-6.2-he6710b0_1.tar.bz2",
                    "filename": "ncurses-6.2-he6710b0_1.tar.bz2",
                    "validation": {
                        "type": "sha256",
                        "value": "1ed6f2c2e5c4fffb883bcb7e84b69605a91e6f20e0142313fdf722d85e001959",
                    },
                },
                {
                    "url": "https://conda.anaconda.org/main/noarch/urllib3-1.26.6-pyhd3eb1b0_1.tar.bz2",
                    "filename": "urllib3-1.26.6-pyhd3eb1b0_1.tar.bz2",
                    "validation": {
                        "type": "sha256",
                        "value": "19e7d8c924f252c3672047b713300519592fbd090f1e7c44a59e99c2e7dac8b0",
                    },
                },
                {
                    "url": "https://conda.anaconda.org/main/noarch/pyopenssl-20.0.1-pyhd3eb1b0_1.tar.bz2",
                    "filename": "pyopenssl-20.0.1-pyhd3eb1b0_1.tar.bz2",
                    "validation": {
                        "type": "sha256",
                        "value": "23777ed5961a0474951fccde25e5e74d644db40a59fa8d5df2e263eeb2f0aebd",
                    },
                },
                {
                    "url": "https://conda.anaconda.org/main/linux-64/libgomp-9.3.0-h5101ec6_17.tar.bz2",
                    "filename": "libgomp-9.3.0-h5101ec6_17.tar.bz2",
                    "validation": {
                        "type": "sha256",
                        "value": "fd8540c16e79afdead8c6dcfb4e7401294f4185522f41deb4dc12f27fb58b3a8",
                    },
                },
                {
                    "url": "https://conda.anaconda.org/main/linux-64/certifi-2021.5.30-py39h06a4308_0.tar.bz2",
                    "filename": "certifi-2021.5.30-py39h06a4308_0.tar.bz2",
                    "validation": {
                        "type": "sha256",
                        "value": "4c5b7f885b01f19943423303e51cfabd852e76ffe957a3bad0a5c0af559816d2",
                    },
                },
                {
                    "url": "https://conda.anaconda.org/main/linux-64/libstdcxx-ng-9.3.0-hd4cf53a_17.tar.bz2",
                    "filename": "libstdcxx-ng-9.3.0-hd4cf53a_17.tar.bz2",
                    "validation": {
                        "type": "sha256",
                        "value": "564810f222aaac1d23bf5265f9a63f62e18f504a38aa33d418e628c1b6ea9fb5",
                    },
                },
                {
                    "url": "https://conda.anaconda.org/main/linux-64/cffi-1.14.6-py39h400218f_0.tar.bz2",
                    "filename": "cffi-1.14.6-py39h400218f_0.tar.bz2",
                    "validation": {
                        "type": "sha256",
                        "value": "ada49b19cea09beec5d5eba25ea3169bdeed5c5a120746ee3ad04e1ddd7b0ddb",
                    },
                },
                {
                    "url": "https://conda.anaconda.org/main/noarch/tzdata-2021a-h5d7bf9c_0.tar.bz2",
                    "filename": "tzdata-2021a-h5d7bf9c_0.tar.bz2",
                    "validation": {
                        "type": "sha256",
                        "value": "76cc5c5c7030424c5331ee71e2338758b662f6696dfc5f787c35508e467efc76",
                    },
                },
                {
                    "url": "https://conda.anaconda.org/main/linux-64/xz-5.2.5-h7b6447c_0.tar.bz2",
                    "filename": "xz-5.2.5-h7b6447c_0.tar.bz2",
                    "validation": {
                        "type": "sha256",
                        "value": "85f331e34675d2ecfc096398ec8ba34c58f23f374e882c354e2245d895d96e67",
                    },
                },
                {
                    "url": "https://conda.anaconda.org/main/linux-64/python-3.9.5-h12debd9_4.tar.bz2",
                    "filename": "python-3.9.5-h12debd9_4.tar.bz2",
                    "validation": {
                        "type": "sha256",
                        "value": "7fc98fe684cb716a8d19cf20a77ccce3cda3f6da968abaade63edbe006d8f3ba",
                    },
                },
                {
                    "url": "https://conda.anaconda.org/main/linux-64/libffi-3.3-he6710b0_2.tar.bz2",
                    "filename": "libffi-3.3-he6710b0_2.tar.bz2",
                    "validation": {
                        "type": "sha256",
                        "value": "3b4afe7665dcdb99bd4586a888b85b2e0325f8faecdd31c7780792080ee97872",
                    },
                },
                {
                    "url": "https://conda.anaconda.org/main/noarch/requests-2.25.1-pyhd3eb1b0_0.tar.bz2",
                    "filename": "requests-2.25.1-pyhd3eb1b0_0.tar.bz2",
                    "validation": {
                        "type": "sha256",
                        "value": "d7a0a3df15a22ab9d0d4c498aeb927c132589a382a87d1f4dcd8efa72aebc9e2",
                    },
                },
                {
                    "url": "https://conda.anaconda.org/main/linux-64/ld_impl_linux-64-2.35.1-h7274673_9.tar.bz2",
                    "filename": "ld_impl_linux-64-2.35.1-h7274673_9.tar.bz2",
                    "validation": {
                        "type": "sha256",
                        "value": "90fcb03d8f04099b57f0f1ea7e29ebeaba9515ac3917a586a4f4b5af55b7523c",
                    },
                },
                {
                    "url": "https://conda.anaconda.org/main/linux-64/chardet-4.0.0-py39h06a4308_1003.tar.bz2",
                    "filename": "chardet-4.0.0-py39h06a4308_1003.tar.bz2",
                    "validation": {
                        "type": "sha256",
                        "value": "d8f7c5997134528dfdf57095abd046116ce2bb1264082b1959a5da6731ed7f4d",
                    },
                },
                {
                    "url": "https://conda.anaconda.org/main/noarch/idna-2.10-pyhd3eb1b0_0.tar.bz2",
                    "filename": "idna-2.10-pyhd3eb1b0_0.tar.bz2",
                    "validation": {
                        "type": "sha256",
                        "value": "2f4e481054f660769fd766a506f4774a91afa95903cbcfe1ba9da724ca348dc4",
                    },
                },
                {
                    "url": "https://conda.anaconda.org/main/linux-64/brotlipy-0.7.0-py39h27cfd23_1003.tar.bz2",
                    "filename": "brotlipy-0.7.0-py39h27cfd23_1003.tar.bz2",
                    "validation": {
                        "type": "sha256",
                        "value": "8c2071f706c2b445dabb781f7f8f008b23a29957468ec6894f050bfb3a2d5bf4",
                    },
                },
                {
                    "url": "https://conda.anaconda.org/main/linux-64/pyyaml-5.4.1-py39h27cfd23_1.tar.bz2",
                    "filename": "pyyaml-5.4.1-py39h27cfd23_1.tar.bz2",
                    "validation": {
                        "type": "sha256",
                        "value": "4d89212418ecb3cb74ca4453dafe7a40f3be5a551da7b9ed5af303a9edb3e6d5",
                    },
                },
                {
                    "url": "https://conda.anaconda.org/main/linux-64/_openmp_mutex-4.5-1_gnu.tar.bz2",
                    "filename": "openmp_mutex-4.5-1_gnu.tar.bz2",
                    "validation": {
                        "type": "sha256",
                        "value": "2c269ff2e33d3c158b4744485b7fe11ee132814c55a70b33b3e68d588375d465",
                    },
                },
                {
                    "url": "https://conda.anaconda.org/main/linux-64/yaml-0.2.5-h7b6447c_0.tar.bz2",
                    "filename": "yaml-0.2.5-h7b6447c_0.tar.bz2",
                    "validation": {
                        "type": "sha256",
                        "value": "21957e347f97960435b5267baefe1014fe53e4e673b478dfe46b82e371bc0e2b",
                    },
                },
                {
                    "url": "https://conda.anaconda.org/main/linux-64/tk-8.6.10-hbc83047_0.tar.bz2",
                    "filename": "tk-8.6.10-hbc83047_0.tar.bz2",
                    "validation": {
                        "type": "sha256",
                        "value": "51dacd65bba96d74f135cf531c832ebb04f3250df72eaf6d5f0840e5cbcb3d6d",
                    },
                },
                {
                    "url": "https://conda.anaconda.org/main/linux-64/libgcc-ng-9.3.0-h5101ec6_17.tar.bz2",
                    "filename": "libgcc-ng-9.3.0-h5101ec6_17.tar.bz2",
                    "validation": {
                        "type": "sha256",
                        "value": "bdb43a7a4483ab03f4d5dba6212d5d9462764980c01cdea524eebc156765f540",
                    },
                },
                {
                    "url": "https://conda.anaconda.org/main/linux-64/ca-certificates-2021.7.5-h06a4308_1.tar.bz2",
                    "filename": "ca-certificates-2021.7.5-h06a4308_1.tar.bz2",
                    "validation": {
                        "type": "sha256",
                        "value": "74ebcc5864f7e83ec533b35361d54ee3b1480043b9a80a746b51963ca12c2266",
                    },
                },
                {
                    "url": "https://conda.anaconda.org/main/linux-64/openssl-1.1.1k-h27cfd23_0.tar.bz2",
                    "filename": "openssl-1.1.1k-h27cfd23_0.tar.bz2",
                    "validation": {
                        "type": "sha256",
                        "value": "e52e5211a21d2728b55a8883f6725fafb5e331aaf4953b276e795461aeb2853b",
                    },
                },
                {
                    "url": "https://conda.anaconda.org/main/linux-64/pysocks-1.7.1-py39h06a4308_0.tar.bz2",
                    "filename": "pysocks-1.7.1-py39h06a4308_0.tar.bz2",
                    "validation": {
                        "type": "sha256",
                        "value": "5eb7130d2f345d4a4fd7ccfc10bc9ba5f1235eaabc22536b9a20736087be106e",
                    },
                },
                {
                    "url": "https://conda.anaconda.org/main/linux-64/zlib-1.2.11-h7b6447c_3.tar.bz2",
                    "filename": "zlib-1.2.11-h7b6447c_3.tar.bz2",
                    "validation": {
                        "type": "sha256",
                        "value": "d5653139d823ef26148ea5fe781e48e62a1d95b487a80e9aa3507dfd9efd5971",
                    },
                },
                {
                    "url": "https://conda.anaconda.org/main/linux-64/_libgcc_mutex-0.1-main.tar.bz2",
                    "filename": "libgcc_mutex-0.1-main.tar.bz2",
                    "validation": {
                        "type": "sha256",
                        "value": "bd36a740479053a94d9c2a92bc55333a7a1a3e63ec0341d4cde6b7825bae0ee3",
                    },
                },
                {
                    "url": "https://conda.anaconda.org/main/linux-64/readline-8.1-h27cfd23_0.tar.bz2",
                    "filename": "readline-8.1-h27cfd23_0.tar.bz2",
                    "validation": {
                        "type": "sha256",
                        "value": "fa1a041badf4beeba06f51b17a3214a5509015eef4daf1925d01c207f6b00ca7",
                    },
                },
                {
                    "url": "https://conda.anaconda.org/main/linux-64/sqlite-3.36.0-hc218d9a_0.tar.bz2",
                    "filename": "sqlite-3.36.0-hc218d9a_0.tar.bz2",
                    "validation": {
                        "type": "sha256",
                        "value": "5b8e64bcf8486bbd3a05798c572e897023d882fa3dde3fd50cb44009eeddb5f4",
                    },
                },
                {
                    "url": "https://conda.anaconda.org/main/noarch/pycparser-2.20-py_2.tar.bz2",
                    "filename": "pycparser-2.20-py_2.tar.bz2",
                    "validation": {
                        "type": "sha256",
                        "value": "c4bb620fcf867208e59165ef21e6525958633c4b863f34efb4884a5febcb7179",
                    },
                },
                {
                    "url": "https://conda.anaconda.org/conda-forge/noarch/conda-mirror-0.8.2-py_1.tar.bz2",
                    "filename": "conda-mirror-0.8.2-py_1.tar.bz2",
                    "validation": {
                        "type": "sha256",
                        "value": "ce932d3a30d08ff38c1ee07c1ed0139c9a0b4b422afda3736a2b006752ac079a",
                    },
                },
                {
                    "url": "https://conda.anaconda.org/main/linux-64/cryptography-3.4.7-py39hd23ed53_0.tar.bz2",
                    "filename": "cryptography-3.4.7-py39hd23ed53_0.tar.bz2",
                    "validation": {
                        "type": "sha256",
                        "value": "204063190dffe13c06dbcac394c75b7b778c5a54dfca5f152ce6cacc6d17fdee",
                    },
                },
            ]
        }
    elif platform == "osx-64":
        return {
            "resources": [
                {
                    "url": "https://conda.anaconda.org/main/osx-64/tk-8.6.10-hb0a8c7a_0.tar.bz2",
                    "filename": "tk-8.6.10-hb0a8c7a_0.tar.bz2",
                    "validation": {
                        "type": "sha256",
                        "value": "992b4cdf6963faf1e86471b68af3a99a2fc6912ce19064b5126eb46158943439",
                    },
                },
                {
                    "url": "https://conda.anaconda.org/main/osx-64/readline-8.1-h9ed2024_0.tar.bz2",
                    "filename": "readline-8.1-h9ed2024_0.tar.bz2",
                    "validation": {
                        "type": "sha256",
                        "value": "0e32a0c5a2de4bfac9e979d89d4bbec53de44f4c62ffdc0614224158dcc1df58",
                    },
                },
                {
                    "url": "https://conda.anaconda.org/main/noarch/idna-2.10-pyhd3eb1b0_0.tar.bz2",
                    "filename": "idna-2.10-pyhd3eb1b0_0.tar.bz2",
                    "validation": {
                        "type": "sha256",
                        "value": "2f4e481054f660769fd766a506f4774a91afa95903cbcfe1ba9da724ca348dc4",
                    },
                },
                {
                    "url": "https://conda.anaconda.org/main/noarch/tzdata-2021a-h5d7bf9c_0.tar.bz2",
                    "filename": "tzdata-2021a-h5d7bf9c_0.tar.bz2",
                    "validation": {
                        "type": "sha256",
                        "value": "76cc5c5c7030424c5331ee71e2338758b662f6696dfc5f787c35508e467efc76",
                    },
                },
                {
                    "url": "https://conda.anaconda.org/main/osx-64/pyyaml-5.4.1-py39h9ed2024_1.tar.bz2",
                    "filename": "pyyaml-5.4.1-py39h9ed2024_1.tar.bz2",
                    "validation": {
                        "type": "sha256",
                        "value": "3931a47f240104adf274df57618e61edd76cc8dd3317702f9263c80a07cb00f6",
                    },
                },
                {
                    "url": "https://conda.anaconda.org/main/noarch/pycparser-2.20-py_2.tar.bz2",
                    "filename": "pycparser-2.20-py_2.tar.bz2",
                    "validation": {
                        "type": "sha256",
                        "value": "c4bb620fcf867208e59165ef21e6525958633c4b863f34efb4884a5febcb7179",
                    },
                },
                {
                    "url": "https://conda.anaconda.org/main/osx-64/cffi-1.14.6-py39h2125817_0.tar.bz2",
                    "filename": "cffi-1.14.6-py39h2125817_0.tar.bz2",
                    "validation": {
                        "type": "sha256",
                        "value": "6f73f704f71fb52908d3e562bb3223ea339a2dbc6f08fc60da45beb9dee428d5",
                    },
                },
                {
                    "url": "https://conda.anaconda.org/main/osx-64/zlib-1.2.11-h1de35cc_3.tar.bz2",
                    "filename": "zlib-1.2.11-h1de35cc_3.tar.bz2",
                    "validation": {
                        "type": "sha256",
                        "value": "ef7d3f4658d135c24e14a7c26bd095e500eeeea760c0241f60f0188e0d6208d9",
                    },
                },
                {
                    "url": "https://conda.anaconda.org/main/osx-64/libcxx-10.0.0-1.tar.bz2",
                    "filename": "libcxx-10.0.0-1.tar.bz2",
                    "validation": {
                        "type": "sha256",
                        "value": "4229aacd7b3253967c5ca5bdf2292704ae4984cace6b0cef1b1ad4d97c3978f5",
                    },
                },
                {
                    "url": "https://conda.anaconda.org/main/osx-64/libffi-3.3-hb1e8313_2.tar.bz2",
                    "filename": "libffi-3.3-hb1e8313_2.tar.bz2",
                    "validation": {
                        "type": "sha256",
                        "value": "5799880c725c43a5adb36c3fcce24c1926246688ac102bf510d732b38ce648ca",
                    },
                },
                {
                    "url": "https://conda.anaconda.org/main/osx-64/ncurses-6.2-h0a44026_1.tar.bz2",
                    "filename": "ncurses-6.2-h0a44026_1.tar.bz2",
                    "validation": {
                        "type": "sha256",
                        "value": "e710623aa1ce240519bef7ad8a1d747799cd766bbc1d3c0b8bd46f5229c76c56",
                    },
                },
                {
                    "url": "https://conda.anaconda.org/main/osx-64/python-3.9.5-h88f2d9e_3.tar.bz2",
                    "filename": "python-3.9.5-h88f2d9e_3.tar.bz2",
                    "validation": {
                        "type": "sha256",
                        "value": "50589810048f3faa6409b66c4f92251dd29911f7b3e82bb4d1b1741ca2b45d00",
                    },
                },
                {
                    "url": "https://conda.anaconda.org/main/osx-64/sqlite-3.36.0-hce871da_0.tar.bz2",
                    "filename": "sqlite-3.36.0-hce871da_0.tar.bz2",
                    "validation": {
                        "type": "sha256",
                        "value": "ec09a7c4630f69e9daa18da315d4d425f4bb6b302c48f1e9ec215b8da00f3777",
                    },
                },
                {
                    "url": "https://conda.anaconda.org/main/osx-64/openssl-1.1.1k-h9ed2024_0.tar.bz2",
                    "filename": "openssl-1.1.1k-h9ed2024_0.tar.bz2",
                    "validation": {
                        "type": "sha256",
                        "value": "a10339e8b6c2c92abb67f01792c5b30ca2e02e346a97d05c64eace7bb0b9575a",
                    },
                },
                {
                    "url": "https://conda.anaconda.org/main/osx-64/certifi-2021.5.30-py39hecd8cb5_0.tar.bz2",
                    "filename": "certifi-2021.5.30-py39hecd8cb5_0.tar.bz2",
                    "validation": {
                        "type": "sha256",
                        "value": "83f196f95e67f4936b4e10f6044cb666bee97aea00ca806674f43f6ce5640095",
                    },
                },
                {
                    "url": "https://conda.anaconda.org/main/osx-64/chardet-4.0.0-py39hecd8cb5_1003.tar.bz2",
                    "filename": "chardet-4.0.0-py39hecd8cb5_1003.tar.bz2",
                    "validation": {
                        "type": "sha256",
                        "value": "6403e823caff9aed1e8f9f891f34f4bc5896b25f7a6031878b81c2d59eecc5f7",
                    },
                },
                {
                    "url": "https://conda.anaconda.org/main/noarch/requests-2.25.1-pyhd3eb1b0_0.tar.bz2",
                    "filename": "requests-2.25.1-pyhd3eb1b0_0.tar.bz2",
                    "validation": {
                        "type": "sha256",
                        "value": "d7a0a3df15a22ab9d0d4c498aeb927c132589a382a87d1f4dcd8efa72aebc9e2",
                    },
                },
                {
                    "url": "https://conda.anaconda.org/conda-forge/noarch/conda-mirror-0.8.2-py_1.tar.bz2",
                    "filename": "conda-mirror-0.8.2-py_1.tar.bz2",
                    "validation": {
                        "type": "sha256",
                        "value": "ce932d3a30d08ff38c1ee07c1ed0139c9a0b4b422afda3736a2b006752ac079a",
                    },
                },
                {
                    "url": "https://conda.anaconda.org/main/osx-64/pysocks-1.7.1-py39hecd8cb5_0.tar.bz2",
                    "filename": "pysocks-1.7.1-py39hecd8cb5_0.tar.bz2",
                    "validation": {
                        "type": "sha256",
                        "value": "fe7df2db41ba51c33c10a58038dd945adcab91edf897728a0918df9e1fb1ed9f",
                    },
                },
                {
                    "url": "https://conda.anaconda.org/main/noarch/six-1.16.0-pyhd3eb1b0_0.tar.bz2",
                    "filename": "six-1.16.0-pyhd3eb1b0_0.tar.bz2",
                    "validation": {
                        "type": "sha256",
                        "value": "142b5c736cfec8981e631d63f2b0860ce31775cf24d1b5b504dbafbec6561c88",
                    },
                },
                {
                    "url": "https://conda.anaconda.org/main/noarch/pyopenssl-20.0.1-pyhd3eb1b0_1.tar.bz2",
                    "filename": "pyopenssl-20.0.1-pyhd3eb1b0_1.tar.bz2",
                    "validation": {
                        "type": "sha256",
                        "value": "23777ed5961a0474951fccde25e5e74d644db40a59fa8d5df2e263eeb2f0aebd",
                    },
                },
                {
                    "url": "https://conda.anaconda.org/main/osx-64/xz-5.2.5-h1de35cc_0.tar.bz2",
                    "filename": "xz-5.2.5-h1de35cc_0.tar.bz2",
                    "validation": {
                        "type": "sha256",
                        "value": "e488e86adc3924e2d208a983515af3f53f940b792cf5ca753eb7df57e8e644ce",
                    },
                },
                {
                    "url": "https://conda.anaconda.org/main/noarch/urllib3-1.26.6-pyhd3eb1b0_1.tar.bz2",
                    "filename": "urllib3-1.26.6-pyhd3eb1b0_1.tar.bz2",
                    "validation": {
                        "type": "sha256",
                        "value": "19e7d8c924f252c3672047b713300519592fbd090f1e7c44a59e99c2e7dac8b0",
                    },
                },
                {
                    "url": "https://conda.anaconda.org/main/osx-64/brotlipy-0.7.0-py39h9ed2024_1003.tar.bz2",
                    "filename": "brotlipy-0.7.0-py39h9ed2024_1003.tar.bz2",
                    "validation": {
                        "type": "sha256",
                        "value": "3b69b6b9795b7947a7b5c2d36da3f02deed30be44a4f5a2d098839217a895d5b",
                    },
                },
                {
                    "url": "https://conda.anaconda.org/main/osx-64/ca-certificates-2021.7.5-hecd8cb5_1.tar.bz2",
                    "filename": "ca-certificates-2021.7.5-hecd8cb5_1.tar.bz2",
                    "validation": {
                        "type": "sha256",
                        "value": "634cc64bb0eb39e30e74580ad811aec07b44f5f48c951e482954fee085aa37fb",
                    },
                },
                {
                    "url": "https://conda.anaconda.org/main/osx-64/cryptography-3.4.7-py39h2fd3fbb_0.tar.bz2",
                    "filename": "cryptography-3.4.7-py39h2fd3fbb_0.tar.bz2",
                    "validation": {
                        "type": "sha256",
                        "value": "cd2dce66a02cc64212d4f0be7e1325fc741aa8cebc43390790e8049f99abf48c",
                    },
                },
                {
                    "url": "https://conda.anaconda.org/main/osx-64/yaml-0.2.5-haf1e3a3_0.tar.bz2",
                    "filename": "yaml-0.2.5-haf1e3a3_0.tar.bz2",
                    "validation": {
                        "type": "sha256",
                        "value": "c39a7da619b6fb3979784eb324e5dac686de71c6bf8c37bbd47939ecf0a468b4",
                    },
                },
            ]
        }


@pytest.fixture
def conda_channel_fixture(
    tmp_path, get_path_location_for_manifest_fixture, scope="module"
):
    return CondaChannel(
        channel_root=tmp_path, meta_manifest_path=get_path_location_for_manifest_fixture
    )


@pytest.fixture
def meta_manifest_fixture(tmp_path, minimal_conda_forge_environment, scope="module"):
    return MetaManifest(minimal_conda_forge_environment, manifest_root=tmp_path)


def mock_response(
    status=200, content=b"CONTENT", json_data=None, raise_for_status=None
):
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
        mock_resp.json = Mock(return_value=json_data)
    return mock_resp


def fetch_data():
    [
        {
            "arch": "x86_64",
            "build": "py39h27cfd23_1003",
            "build_number": 1003,
            "channel": "https://conda.anaconda.org/main/linux-64",
            "constrains": [],
            "depends": ["cffi >=1.0.0", "libgcc-ng >=7.3.0", "python >=3.9,<3.10.0a0"],
            "fn": "brotlipy-0.7.0-py39h27cfd23_1003.tar.bz2",
            "license": "MIT",
            "license_family": "MIT",
            "md5": "c203ffc7bbba991c7089d4b383cfd92c",
            "name": "brotlipy",
            "platform": "linux",
            "sha256": "8c2071f706c2b445dabb781f7f8f008b23a29957468ec6894f050bfb3a2d5bf4",
            "size": 357797,
            "subdir": "linux-64",
            "timestamp": 1605539534667,
            "url": "https://conda.anaconda.org/main/linux-64/brotlipy-0.7.0-py39h27cfd23_1003.tar.bz2",
            "version": "0.7.0",
        },
        {
            "arch": None,
            "build": "pyhd8ed1ab_0",
            "build_number": 0,
            "channel": "https://conda.anaconda.org/conda-forge/noarch",
            "constrains": [],
            "depends": ["appdirs", "click", "filelock", "python >=3.6", "requests"],
            "fn": "ensureconda-1.4.1-pyhd8ed1ab_0.tar.bz2",
            "license": "MIT",
            "license_family": "MIT",
            "md5": "52a7f7cc9076e2c8a25e15e19ad42821",
            "name": "ensureconda",
            "noarch": "python",
            "package_type": "noarch_python",
            "platform": None,
            "sha256": "ddf53aae78fbbccd01e4bb4eb97beb0403b89b91fa75f1ffecc5b59647f07c72",
            "size": 11368,
            "subdir": "noarch",
            "timestamp": 1609981069692,
            "url": "https://conda.anaconda.org/conda-forge/noarch/ensureconda-1.4.1-pyhd8ed1ab_0.tar.bz2",
            "version": "1.4.1",
        },
    ]
