import pytest
from unittest.mock import Mock
import requests
from requests import Response
import json
from conda_vendor.core import  CondaChannel
from tests.repodata_fixtures import (
    vendor_manifest_dict,
    dot_conda_and_tar_list,
    python_395_pkg_list,
    repodata_output,
)


@pytest.fixture
def conda_channel_fixture(tmp_path,minimal_conda_forge_env, scope="module"):
    return CondaChannel(minimal_conda_forge_env, channel_root=tmp_path )


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


@pytest.fixture(scope="function")
def minimal_conda_forge_env(tmpdir_factory):
    content = """name: minimal_env
channels:
- main
- conda-forge
- nodefaults
dependencies:
- python=>3.6.1
- conda-mirror"""
    
    fn = tmpdir_factory.mktemp("minimal_env").join("env.yml")
    print(fn)
    fn.write(content)
    return fn


@pytest.fixture
def mock_requests_repodata(unfiltered_repo_data_response):
    requests_mock = Mock(spec=requests)
    actual_result_mock = Mock(Response)
    requests_mock.get.return_value = actual_result_mock
    actual_result_mock.json.return_value = unfiltered_repo_data_response
    return requests_mock

@pytest.fixture(scope="module")
def fixture_conda_lock_small_response():
    return [{"arch": "x86_64", "build": "h27cfd23_0", "build_number": 0, "channel": "https://conda.anaconda.org/main/linux-64", "constrains": [], "depends": ["libgcc-ng >=7.3.0", "ncurses >=6.2,<7.0a0"], "fn": "readline-8.1-h27cfd23_0.tar.bz2", "license": "GPL-3.0", "md5": "b3a5e0e61af068595cfd411db9960e1f", "name": "readline", "platform": "linux", "sha256": "fa1a041badf4beeba06f51b17a3214a5509015eef4daf1925d01c207f6b00ca7", "size": 475570, "subdir": "linux-64", "timestamp": 1611868595060, "url": "https://conda.anaconda.org/main/linux-64/readline-8.1-h27cfd23_0.tar.bz2", "version": "8.1"}]




@pytest.fixture(scope="module")
def fixture_conda_lock_solve_response():
    return [{"arch": "x86_64", "build": "h27cfd23_0", "build_number": 0, "channel": "https://conda.anaconda.org/main/linux-64", "constrains": [], "depends": ["libgcc-ng >=7.3.0", "ncurses >=6.2,<7.0a0"], "fn": "readline-8.1-h27cfd23_0.tar.bz2", "license": "GPL-3.0", "md5": "b3a5e0e61af068595cfd411db9960e1f", "name": "readline", "platform": "linux", "sha256": "fa1a041badf4beeba06f51b17a3214a5509015eef4daf1925d01c207f6b00ca7", "size": 475570, "subdir": "linux-64", "timestamp": 1611868595060, "url": "https://conda.anaconda.org/main/linux-64/readline-8.1-h27cfd23_0.tar.bz2", "version": "8.1"}, {"arch": None, "build": "h52ac0ba_0", "build_number": 0, "channel": "https://conda.anaconda.org/main/noarch", "constrains": [], "depends": [], "fn": "tzdata-2021a-h52ac0ba_0.tar.bz2", "license": "LicenseRef-Public-Domain AND BSD-3-clause", "md5": "50004d19422d1020b935226a5a8240b2", "name": "tzdata", "noarch": "generic", "package_type": "noarch_generic", "platform": None, "sha256": "bf168d15cd7f1e366d00d449992c008e59260789e313ba1525e69a24234bb5c5", "size": 121398, "subdir": "noarch", "timestamp": 1623996945083, "url": "https://conda.anaconda.org/main/noarch/tzdata-2021a-h52ac0ba_0.tar.bz2", "version": "2021a"}, {"arch": "x86_64", "build": "py39h06a4308_0", "build_number": 0, "channel": "https://conda.anaconda.org/main/linux-64", "constrains": [], "depends": ["python >=3.9,<3.10.0a0"], "fn": "certifi-2021.5.30-py39h06a4308_0.tar.bz2", "license": "MPL-2.0", "md5": "cbca47c19fccdfd89cd2908733224750", "name": "certifi", "platform": "linux", "sha256": "4c5b7f885b01f19943423303e51cfabd852e76ffe957a3bad0a5c0af559816d2", "size": 144707, "subdir": "linux-64", "timestamp": 1622562526194, "url": "https://conda.anaconda.org/main/linux-64/certifi-2021.5.30-py39h06a4308_0.tar.bz2", "version": "2021.5.30"}, {"arch": "x86_64", "build": "h06a4308_1", "build_number": 1, "channel": "https://conda.anaconda.org/main/linux-64", "constrains": [], "depends": [], "fn": "ca-certificates-2021.5.25-h06a4308_1.tar.bz2", "license": "MPL 2.0", "md5": "068ad52c49286e986574ba544d9f4c50", "name": "ca-certificates", "platform": "linux", "sha256": "0350a857d969478805dc68f12af2094bba3e527c1b00e5ab17e36615242fdc13", "size": 120366, "subdir": "linux-64", "timestamp": 1621995548182, "url": "https://conda.anaconda.org/main/linux-64/ca-certificates-2021.5.25-h06a4308_1.tar.bz2", "version": "2021.5.25"}, {"arch": "x86_64", "build": "py39h06a4308_1003", "build_number": 1003, "channel": "https://conda.anaconda.org/main/linux-64", "constrains": [], "depends": ["python >=3.9,<3.10.0a0"], "fn": "chardet-4.0.0-py39h06a4308_1003.tar.bz2", "license": "LGPL2", "license_family": "GPL", "md5": "bf619ce778d01adaef0aef6b7e99972a", "name": "chardet", "platform": "linux", "sha256": "d8f7c5997134528dfdf57095abd046116ce2bb1264082b1959a5da6731ed7f4d", "size": 203040, "subdir": "linux-64", "timestamp": 1607706813216, "url": "https://conda.anaconda.org/main/linux-64/chardet-4.0.0-py39h06a4308_1003.tar.bz2", "version": "4.0.0"}, {"arch": "x86_64", "build": "he6710b0_2", "build_number": 2, "channel": "https://conda.anaconda.org/main/linux-64", "constrains": [], "depends": ["libgcc-ng >=7.3.0", "libstdcxx-ng >=7.3.0"], "fn": "libffi-3.3-he6710b0_2.tar.bz2", "license": "Custom", "md5": "822b5201dde61bc838072dc5b670c88c", "name": "libffi", "platform": "linux", "sha256": "3b4afe7665dcdb99bd4586a888b85b2e0325f8faecdd31c7780792080ee97872", "size": 55183, "subdir": "linux-64", "timestamp": 1594054267890, "url": "https://conda.anaconda.org/main/linux-64/libffi-3.3-he6710b0_2.tar.bz2", "version": "3.3"}, {"arch": "x86_64", "build": "h12debd9_4", "build_number": 4, "channel": "https://conda.anaconda.org/main/linux-64", "constrains": [], "depends": ["ld_impl_linux-64", "libffi >=3.3,<3.4.0a0", "libgcc-ng >=7.5.0", "libstdcxx-ng >=7.5.0", "ncurses >=6.2,<7.0a0", "openssl >=1.1.1k,<1.1.2a", "readline >=8.0,<9.0a0", "sqlite >=3.35.4,<4.0a0", "tk >=8.6.10,<8.7.0a0", "tzdata", "xz >=5.2.5,<6.0a0", "zlib >=1.2.11,<1.3.0a0"], "fn": "python-3.9.5-h12debd9_4.tar.bz2", "license": "Python-2.0", "md5": "eb1bc6ccb2cbb43adb5a09e5802efef8", "name": "python", "platform": "linux", "sha256": "7fc98fe684cb716a8d19cf20a77ccce3cda3f6da968abaade63edbe006d8f3ba", "size": 23740654, "subdir": "linux-64", "timestamp": 1622828217909, "url": "https://conda.anaconda.org/main/linux-64/python-3.9.5-h12debd9_4.tar.bz2", "version": "3.9.5"}, {"arch": "x86_64", "build": "h7b6447c_0", "build_number": 0, "channel": "https://conda.anaconda.org/main/linux-64", "constrains": [], "depends": ["libgcc-ng >=7.3.0"], "fn": "xz-5.2.5-h7b6447c_0.tar.bz2", "license": "LGPL-2.1 and GPL-2.0", "md5": "e17620ef8fc8654e77f53b4f2995b288", "name": "xz", "platform": "linux", "sha256": "85f331e34675d2ecfc096398ec8ba34c58f23f374e882c354e2245d895d96e67", "size": 448605, "subdir": "linux-64", "timestamp": 1587011767250, "url": "https://conda.anaconda.org/main/linux-64/xz-5.2.5-h7b6447c_0.tar.bz2", "version": "5.2.5"}, {"arch": "x86_64", "build": "main", "build_number": 0, "channel": "https://conda.anaconda.org/main/linux-64", "constrains": [], "depends": [], "fn": "_libgcc_mutex-0.1-main.tar.bz2", "md5": "013d3f22cd3b87f71224bd936765bcad", "name": "_libgcc_mutex", "platform": "linux", "sha256": "bd36a740479053a94d9c2a92bc55333a7a1a3e63ec0341d4cde6b7825bae0ee3", "size": 3121, "subdir": "linux-64", "timestamp": 1562011674792, "url": "https://conda.anaconda.org/main/linux-64/_libgcc_mutex-0.1-main.tar.bz2", "version": "0.1"}, {"arch": "x86_64", "build": "he6710b0_1", "build_number": 1, "channel": "https://conda.anaconda.org/main/linux-64", "constrains": [], "depends": ["libgcc-ng >=7.3.0", "libstdcxx-ng >=7.3.0"], "fn": "ncurses-6.2-he6710b0_1.tar.bz2", "license": "Free software (MIT-like)", "md5": "e8ca84eda38cda3b462addd143a2e7b7", "name": "ncurses", "platform": "linux", "sha256": "1ed6f2c2e5c4fffb883bcb7e84b69605a91e6f20e0142313fdf722d85e001959", "size": 1116403, "subdir": "linux-64", "timestamp": 1588170439381, "url": "https://conda.anaconda.org/main/linux-64/ncurses-6.2-he6710b0_1.tar.bz2", "version": "6.2"}, {"arch": "x86_64", "build": "hbc83047_0", "build_number": 0, "channel": "https://conda.anaconda.org/main/linux-64", "constrains": [], "depends": ["libgcc-ng >=7.3.0", "zlib >=1.2.11,<1.3.0a0"], "fn": "tk-8.6.10-hbc83047_0.tar.bz2", "license": "Tcl/Tk", "license_family": "BSD", "md5": "76350e04c66dde3f9d94884866ed70c3", "name": "tk", "platform": "linux", "sha256": "51dacd65bba96d74f135cf531c832ebb04f3250df72eaf6d5f0840e5cbcb3d6d", "size": 3406660, "subdir": "linux-64", "timestamp": 1592503345885, "url": "https://conda.anaconda.org/main/linux-64/tk-8.6.10-hbc83047_0.tar.bz2", "version": "8.6.10"}, {"arch": "x86_64", "build": "h7b6447c_0", "build_number": 0, "channel": "https://conda.anaconda.org/main/linux-64", "constrains": [], "depends": ["libgcc-ng >=7.3.0"], "fn": "yaml-0.2.5-h7b6447c_0.tar.bz2", "license": "MIT", "md5": "fcff4f33bb4e3fa91f8d5c3168807abb", "name": "yaml", "platform": "linux", "sha256": "21957e347f97960435b5267baefe1014fe53e4e673b478dfe46b82e371bc0e2b", "size": 88839, "subdir": "linux-64", "timestamp": 1593116114710, "url": "https://conda.anaconda.org/main/linux-64/yaml-0.2.5-h7b6447c_0.tar.bz2", "version": "0.2.5"}, {"arch": None, "build": "pyhd3eb1b0_1", "build_number": 1, "channel": "https://conda.anaconda.org/main/noarch", "constrains": [], "depends": ["cryptography >=2.8", "python", "six >=1.5.2"], "fn": "pyopenssl-20.0.1-pyhd3eb1b0_1.tar.bz2", "license": "Apache 2.0", "license_family": "Apache", "md5": "525075d4b015206933ba28ceb5163d63", "name": "pyopenssl", "noarch": "python", "package_type": "noarch_python", "platform": None, "sha256": "23777ed5961a0474951fccde25e5e74d644db40a59fa8d5df2e263eeb2f0aebd", "size": 49074, "subdir": "noarch", "timestamp": 1608057995890, "url": "https://conda.anaconda.org/main/noarch/pyopenssl-20.0.1-pyhd3eb1b0_1.tar.bz2", "version": "20.0.1"}, {"arch": "x86_64", "build": "h7b6447c_3", "build_number": 3, "channel": "https://conda.anaconda.org/main/linux-64", "constrains": [], "depends": ["libgcc-ng >=7.3.0"], "fn": "zlib-1.2.11-h7b6447c_3.tar.bz2", "license": "zlib", "license_family": "Other", "md5": "e76217678961a4836e1067a2d11603e2", "name": "zlib", "platform": "linux", "sha256": "d5653139d823ef26148ea5fe781e48e62a1d95b487a80e9aa3507dfd9efd5971", "size": 122469, "subdir": "linux-64", "timestamp": 1542814864621, "url": "https://conda.anaconda.org/main/linux-64/zlib-1.2.11-h7b6447c_3.tar.bz2", "version": "1.2.11"}, {"arch": "x86_64", "build": "py39h261ae71_0", "build_number": 0, "channel": "https://conda.anaconda.org/main/linux-64", "constrains": [], "depends": ["libffi >=3.3,<3.4.0a0", "libgcc-ng >=7.3.0", "pycparser", "python >=3.9,<3.10.0a0"], "fn": "cffi-1.14.5-py39h261ae71_0.tar.bz2", "license": "MIT", "md5": "227c9160144b3c934d796eb4047be270", "name": "cffi", "platform": "linux", "sha256": "f51dfaaaf27796530ed0cb5066be12b43d24e38a0552b3f005cd6c271a7fce75", "size": 232177, "subdir": "linux-64", "timestamp": 1613246999673, "url": "https://conda.anaconda.org/main/linux-64/cffi-1.14.5-py39h261ae71_0.tar.bz2", "version": "1.14.5"}, {"arch": "x86_64", "build": "py39h06a4308_0", "build_number": 0, "channel": "https://conda.anaconda.org/main/linux-64", "constrains": [], "depends": ["python >=3.9,<3.10.0a0"], "fn": "pysocks-1.7.1-py39h06a4308_0.tar.bz2", "license": "BSD 3-Clause", "license_family": "BSD", "md5": "c5f3f7f10ad30f0945e75252615ab6e5", "name": "pysocks", "platform": "linux", "sha256": "5eb7130d2f345d4a4fd7ccfc10bc9ba5f1235eaabc22536b9a20736087be106e", "size": 31331, "subdir": "linux-64", "timestamp": 1605305847037, "url": "https://conda.anaconda.org/main/linux-64/pysocks-1.7.1-py39h06a4308_0.tar.bz2", "version": "1.7.1"}, {"arch": None, "build": "py_1", "build_number": 1, "channel": "https://conda.anaconda.org/conda-forge/noarch", "constrains": [], "depends": ["python >=3", "pyyaml", "requests"], "fn": "conda-mirror-0.8.2-py_1.tar.bz2", "license": "BSD-3-Clause", "license_family": "BSD", "md5": "fca6767eff1b77c4f90238eb0c58d529", "name": "conda-mirror", "noarch": "python", "package_type": "noarch_python", "platform": None, "sha256": "ce932d3a30d08ff38c1ee07c1ed0139c9a0b4b422afda3736a2b006752ac079a", "size": 19015, "subdir": "noarch", "timestamp": 1585061111054, "url": "https://conda.anaconda.org/conda-forge/noarch/conda-mirror-0.8.2-py_1.tar.bz2", "version": "0.8.2"}, {"arch": None, "build": "pyhd3eb1b0_0", "build_number": 0, "channel": "https://conda.anaconda.org/main/noarch", "constrains": [], "depends": ["certifi >=2017.4.17", "chardet >=3.0.2,<5", "idna >=2.5,<3", "python", "urllib3 >=1.21.1,<1.27"], "fn": "requests-2.25.1-pyhd3eb1b0_0.tar.bz2", "license": "Apache-2.0", "md5": "b403001a8842763085ec42a635ab8a64", "name": "requests", "noarch": "python", "package_type": "noarch_python", "platform": None, "sha256": "d7a0a3df15a22ab9d0d4c498aeb927c132589a382a87d1f4dcd8efa72aebc9e2", "size": 52418, "subdir": "noarch", "timestamp": 1608241453837, "url": "https://conda.anaconda.org/main/noarch/requests-2.25.1-pyhd3eb1b0_0.tar.bz2", "version": "2.25.1"}, {"arch": "x86_64", "build": "hdf63c60_0", "build_number": 0, "channel": "https://conda.anaconda.org/main/linux-64", "constrains": [], "depends": [], "fn": "libstdcxx-ng-9.1.0-hdf63c60_0.tar.bz2", "license": "GPL3 with runtime exception", "md5": "53fa39fdae936e9d07c4b2f5ef361993", "name": "libstdcxx-ng", "platform": "linux", "sha256": "43b0bd205f539583c088feb5b8d77b60c83d1df80c2a93dac9f2a1127001b2cf", "size": 4246257, "subdir": "linux-64", "timestamp": 1560112223556, "url": "https://conda.anaconda.org/main/linux-64/libstdcxx-ng-9.1.0-hdf63c60_0.tar.bz2", "version": "9.1.0"}, {"arch": "x86_64", "build": "py39hd23ed53_0", "build_number": 0, "channel": "https://conda.anaconda.org/main/linux-64", "constrains": [], "depends": ["cffi >=1.12", "libgcc-ng", "openssl >=1.1.1k,<1.1.2a", "python >=3.9,<3.10.0a0"], "fn": "cryptography-3.4.7-py39hd23ed53_0.tar.bz2", "license": "Apache-2.0 AND BSD-3-Clause AND PSF-2.0 AND MIT", "license_family": "BSD", "md5": "04c8a1b34174f41818af0185a77cf1e6", "name": "cryptography", "platform": "linux", "sha256": "204063190dffe13c06dbcac394c75b7b778c5a54dfca5f152ce6cacc6d17fdee", "size": 1064005, "subdir": "linux-64", "timestamp": 1616767201071, "url": "https://conda.anaconda.org/main/linux-64/cryptography-3.4.7-py39hd23ed53_0.tar.bz2", "version": "3.4.7"}, {"arch": None, "build": "py_2", "build_number": 2, "channel": "https://conda.anaconda.org/main/noarch", "constrains": [], "depends": ["python"], "fn": "pycparser-2.20-py_2.tar.bz2", "license": "BSD-3-Clause", "md5": "bc20c885814700fdc0187918f9aff9ac", "name": "pycparser", "noarch": "python", "package_type": "noarch_python", "platform": None, "sha256": "c4bb620fcf867208e59165ef21e6525958633c4b863f34efb4884a5febcb7179", "size": 95951, "subdir": "noarch", "timestamp": 1594388539730, "url": "https://conda.anaconda.org/main/noarch/pycparser-2.20-py_2.tar.bz2", "version": "2.20"}, {"arch": None, "build": "pyhd3eb1b0_0", "build_number": 0, "channel": "https://conda.anaconda.org/main/noarch", "constrains": [], "depends": ["python"], "fn": "idna-2.10-pyhd3eb1b0_0.tar.bz2", "license": "BSD Like", "md5": "153ff132f593ea80aae2eea61a629c92", "name": "idna", "noarch": "python", "package_type": "noarch_python", "platform": None, "sha256": "2f4e481054f660769fd766a506f4774a91afa95903cbcfe1ba9da724ca348dc4", "size": 53346, "subdir": "noarch", "timestamp": 1610986112547, "url": "https://conda.anaconda.org/main/noarch/idna-2.10-pyhd3eb1b0_0.tar.bz2", "version": "2.10"}, {"arch": "x86_64", "build": "py39h27cfd23_1", "build_number": 1, "channel": "https://conda.anaconda.org/main/linux-64", "constrains": [], "depends": ["libgcc-ng >=7.3.0", "python >=3.9,<3.10.0a0", "yaml >=0.2.5,<0.3.0a0"], "fn": "pyyaml-5.4.1-py39h27cfd23_1.tar.bz2", "license": "MIT", "license_family": "MIT", "md5": "aab0fc073e49da57e556df3019e514d5", "name": "pyyaml", "platform": "linux", "sha256": "4d89212418ecb3cb74ca4453dafe7a40f3be5a551da7b9ed5af303a9edb3e6d5", "size": 184830, "subdir": "linux-64", "timestamp": 1611258452686, "url": "https://conda.anaconda.org/main/linux-64/pyyaml-5.4.1-py39h27cfd23_1.tar.bz2", "version": "5.4.1"}, {"arch": "x86_64", "build": "hc218d9a_0", "build_number": 0, "channel": "https://conda.anaconda.org/main/linux-64", "constrains": [], "depends": ["libgcc-ng >=7.5.0", "readline >=8.0,<9.0a0", "zlib >=1.2.11,<1.3.0a0"], "fn": "sqlite-3.36.0-hc218d9a_0.tar.bz2", "license": "Public-Domain (http://www.sqlite.org/copyright.html)", "md5": "7147fbe9c210388a7603df8168184535", "name": "sqlite", "platform": "linux", "sha256": "5b8e64bcf8486bbd3a05798c572e897023d882fa3dde3fd50cb44009eeddb5f4", "size": 1510907, "subdir": "linux-64", "timestamp": 1624470591767, "url": "https://conda.anaconda.org/main/linux-64/sqlite-3.36.0-hc218d9a_0.tar.bz2", "version": "3.36.0"}, {"arch": "x86_64", "build": "h7274673_9", "build_number": 9, "channel": "https://conda.anaconda.org/main/linux-64", "constrains": ["binutils_impl_linux-64 2.35.1"], "depends": [], "fn": "ld_impl_linux-64-2.35.1-h7274673_9.tar.bz2", "license": "GPL-3.0-only", "md5": "74753bc14c44f52ce318f4385c746eb8", "name": "ld_impl_linux-64", "platform": "linux", "sha256": "90fcb03d8f04099b57f0f1ea7e29ebeaba9515ac3917a586a4f4b5af55b7523c", "size": 652172, "subdir": "linux-64", "timestamp": 1622698544714, "url": "https://conda.anaconda.org/main/linux-64/ld_impl_linux-64-2.35.1-h7274673_9.tar.bz2", "version": "2.35.1"}, {"arch": "x86_64", "build": "hdf63c60_0", "build_number": 0, "channel": "https://conda.anaconda.org/main/linux-64", "constrains": [], "depends": ["_libgcc_mutex * main"], "fn": "libgcc-ng-9.1.0-hdf63c60_0.tar.bz2", "license": "GPL", "md5": "238f19c803a6ba7bd6dbd6989e03cbf1", "name": "libgcc-ng", "platform": "linux", "sha256": "c6fafbe73d2f93b91b6f4b65829f925f52a8f84746a57abd216b39da9ce8c494", "size": 8496776, "subdir": "linux-64", "timestamp": 1560112207081, "url": "https://conda.anaconda.org/main/linux-64/libgcc-ng-9.1.0-hdf63c60_0.tar.bz2", "version": "9.1.0"}, {"arch": None, "build": "pyhd3eb1b0_0", "build_number": 0, "channel": "https://conda.anaconda.org/main/noarch", "constrains": [], "depends": ["python"], "fn": "six-1.16.0-pyhd3eb1b0_0.tar.bz2", "license": "MIT", "license_family": "MIT", "md5": "4b46cefc41f565ce5a7a5d572d851c49", "name": "six", "noarch": "python", "package_type": "noarch_python", "platform": None, "sha256": "142b5c736cfec8981e631d63f2b0860ce31775cf24d1b5b504dbafbec6561c88", "size": 18781, "subdir": "noarch", "timestamp": 1623709705233, "url": "https://conda.anaconda.org/main/noarch/six-1.16.0-pyhd3eb1b0_0.tar.bz2", "version": "1.16.0"}, {"arch": "x86_64", "build": "h27cfd23_0", "build_number": 0, "channel": "https://conda.anaconda.org/main/linux-64", "constrains": [], "depends": ["ca-certificates", "libgcc-ng >=7.3.0"], "fn": "openssl-1.1.1k-h27cfd23_0.tar.bz2", "license": "OpenSSL", "license_family": "Apache", "md5": "ce1162e605898e7d6a69e025a26f7706", "name": "openssl", "platform": "linux", "sha256": "e52e5211a21d2728b55a8883f6725fafb5e331aaf4953b276e795461aeb2853b", "size": 3981587, "subdir": "linux-64", "timestamp": 1616684152302, "url": "https://conda.anaconda.org/main/linux-64/openssl-1.1.1k-h27cfd23_0.tar.bz2", "version": "1.1.1k"}, {"arch": None, "build": "pyhd3eb1b0_1", "build_number": 1, "channel": "https://conda.anaconda.org/main/noarch", "constrains": [], "depends": ["brotlipy >=0.6.0", "certifi", "cryptography >=1.3.4", "idna >=2.0.0", "pyopenssl >=0.14", "pysocks >=1.5.6,<2.0,!=1.5.7", "python >=3.6,<4.0"], "fn": "urllib3-1.26.6-pyhd3eb1b0_1.tar.bz2", "license": "MIT", "license_family": "MIT", "md5": "7e333a7799eb59068e29ad9dc18997b2", "name": "urllib3", "noarch": "python", "package_type": "noarch_python", "platform": None, "sha256": "19e7d8c924f252c3672047b713300519592fbd090f1e7c44a59e99c2e7dac8b0", "size": 108963, "subdir": "noarch", "timestamp": 1625084309336, "url": "https://conda.anaconda.org/main/noarch/urllib3-1.26.6-pyhd3eb1b0_1.tar.bz2", "version": "1.26.6"}, {"arch": "x86_64", "build": "py39h27cfd23_1003", "build_number": 1003, "channel": "https://conda.anaconda.org/main/linux-64", "constrains": [], "depends": ["cffi >=1.0.0", "libgcc-ng >=7.3.0", "python >=3.9,<3.10.0a0"], "fn": "brotlipy-0.7.0-py39h27cfd23_1003.tar.bz2", "license": "MIT", "license_family": "MIT", "md5": "c203ffc7bbba991c7089d4b383cfd92c", "name": "brotlipy", "platform": "linux", "sha256": "8c2071f706c2b445dabb781f7f8f008b23a29957468ec6894f050bfb3a2d5bf4", "size": 357797, "subdir": "linux-64", "timestamp": 1605539534667, "url": "https://conda.anaconda.org/main/linux-64/brotlipy-0.7.0-py39h27cfd23_1003.tar.bz2", "version": "0.7.0"}]

@pytest.fixture
def mock_requests_content(unfiltered_repo_data_response):
    requests_mock = Mock(spec=requests)
    actual_result_mock = Mock(Response)
    requests_mock.get.return_value = actual_result_mock
    actual_result_mock.content.return_value = bytearray([9, 9, 9])
    return requests_mock




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
            "dist_name": "python-3.9.5-h12debd9_4",
            "name": "python",
            "platform": "linux-64",
            "version": "0.1",
        },
        {
            "base_url": "https://conda.anaconda.org/main",
            "build_number": 1,
            "build_string": "h06a4308_1",
            "channel": "main",
            "dist_name": "tk-8.6.10-hbc83047_0",
            "name": "ca-certificates",
            "platform": "linux-64",
            "version": "2021.5.25",
        }
       
    ]
