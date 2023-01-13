import json
import pytest
import subprocess

from click.testing import CliRunner
from packaging import version
from pathlib import Path

from conda_vendor.conda_vendor import (
    _generate_lock_spec,
    _get_conda_platform,
    create_repodata_json,
    download_packages,
    solve_environment,
    vendor,
)


environments = {
    "minimal": """
name: minimal_env
channels:
- main
dependencies:
- python==3.9.5
""",
    "conda_mirror": """name: conda_mirror
channels:
- main
- conda-forge
dependencies:
- python==3.9.5
- conda-mirror==0.8.2
""",
    "notsolvable": """name: not_solvable
channels:
- main
dependencies:
- fjdlkfjdsalfkjdsalkfjadflkdajs==100.0.0
""",
    "pytorch": """name: torch
channels:
- conda-forge
dependencies:
- python=3.9.*
- pytorch
- torchvision
""",
}


@pytest.fixture(scope="function")
def make_env(tmp_path_factory):
    def _make_env(body, *, name: str = "test", filename: str = None):
        if filename is None:
            filename = f"{name}.yml"
        f = tmp_path_factory.mktemp(name) / filename
        f.write_text(body)
        return f

    return _make_env


def _has_mamba():
    try:
        subprocess.call(["mamba", "--version"])
        return True
    except:
        return False


# dry-run install using vendored channel.
@pytest.mark.integration
def test_vendor_dry_run(make_env):
    runner = CliRunner()

    env = make_env(environments["minimal"])
    result = runner.invoke(
        vendor,
        [
            "--file",
            str(env),
            "--solver",
            "conda",
            "--platform",
            "linux-64",
            "--dry-run",
        ],
    )
    assert result.exit_code == 0
    _json = result.output.split("Dry Run Complete!", 1)[1]
    package_list = json.loads(_json)

    for pkg in package_list:
        if pkg["name"] != "python":
            continue

        if version.parse(pkg["version"]) == version.parse("3.9.5"):
            return

    pytest.fail("python package not found in solution")


# full conda vendor call. will use mamba to solve if that's available, otherwise
# uses conda
@pytest.mark.integration
def test_vendor_complete(make_env):
    solver = "mamba" if _has_mamba() else "conda"
    env = make_env(environments["minimal"])
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(vendor, ["--file", env, "--solver", solver])
    assert result.exit_code == 0


# tests the LockSpecification object returned from conda-lock actually has
# the package we specified
@pytest.mark.integration
def test_get_lock_spec(make_env):
    env = make_env(environments["minimal"])
    lock_spec = _generate_lock_spec(env, _get_conda_platform())
    for dep in lock_spec.dependencies:
        if dep.name != "python":
            continue

        if version.parse(dep.version) == version.parse("3.9.5"):
            return

    pytest.fail("python package not found in lock_spec")


# tests that the solve_environment call doesn't fail.  If this doesn't solve
# a python Exception is raised
@pytest.mark.integration
def test_solvable_environment(make_env):
    env = make_env(environments["conda_mirror"])
    solution = solve_environment(env, "conda", "linux-64")


# tests that if the sovle_environment call does fail, an Exception is raised
@pytest.mark.integration
def test_notsolvable_environment(make_env):
    env = make_env(environments["notsolvable"])
    with pytest.raises(Exception):
        solution = solve_environment(env, "conda", "linux-64")


# tests that the LINK actions are convert to FETCH actions (happens inside
# solve environment)
@pytest.mark.integration
def test_solve_environment_link2fetch(make_env):
    expected_packages = {
        "python": {"version": "3.9.5", "found": False},
        "conda-mirror": {"version": "0.8.2", "found": False},
    }

    env = make_env(environments["conda_mirror"])
    package_list = solve_environment(env, "conda", "linux-64")

    for p in package_list:
        expected = expected_packages.get(p["name"])
        if expected is None:
            continue

        if version.parse(expected["version"]) == version.parse(p["version"]):
            expected["found"] = True

    for name, val in expected_packages.items():
        if not val["found"]:
            pytest.fail("failed to find all the required packages")


def _make_directories(tmp_path_factory, environment_name):
    root = tmp_path_factory.mktemp("temp") / environment_name
    Path.mkdir(root)
    Path.mkdir(root / "linux-64")
    Path.mkdir(root / "noarch")
    return root


# tests that a repodata.json file is generated in the correct locations
@pytest.mark.integration
def test_creates_repodata_json(make_env, tmp_path_factory):
    env = make_env(environments["conda_mirror"])

    root = _make_directories(tmp_path_factory, "conda_mirror")
    package_list = solve_environment(env, "conda", "linux-64")
    create_repodata_json(package_list, root)

    assert ((root / "linux-64") / "repodata.json").exists()
    assert ((root / "noarch") / "repodata.json").exists()


# tests that the files we expect to be downloader are downloaded
@pytest.mark.integration
def test_download_packages(make_env, tmp_path_factory):
    env = make_env(environments["conda_mirror"])

    root = _make_directories(tmp_path_factory, "conda_mirror")
    package_list = solve_environment(env, "conda", "linux-64")
    download_packages(package_list, root, "linux-64")

    for pkg in package_list:
        assert ((root / pkg["subdir"]) / pkg["fn"]).exists()


# tests that the default virtual packages work (and condtain the
# __cuda virtual package)
@pytest.mark.integration
def test_solve_with_cuda_implicit(make_env):
    env = make_env(environments["pytorch"])
    package_list = solve_environment(env, "conda", "linux-64")

    for pkg in package_list:
        if pkg["name"] == "pytorch":
            assert "cuda" in pkg["fn"]
            return

    pytest.fail("pytorch package not found in solution")


# tests that we can override the virtual packages explicitly
@pytest.mark.integration
def test_solve_with_cuda_explicit(make_env):
    virtual_packages = """subdirs:
    linux-64:
        packages:
            __glibc: 2.28
            __unix: 0
            __linux: 5.15
            __cuda: 11.2
"""
    env = make_env(environments["pytorch"])
    virtual_packages_yaml = make_env(virtual_packages, name="vpckg_spec")

    package_list = solve_environment(
        env, "conda", "linux-64", virtual_packages_yaml
    )

    for pkg in package_list:
        if pkg["name"] == "pytorch":
            assert "cuda" in pkg["fn"]
            return

    pytest.fail("pytorch package not found in solution")


# tests that we can override the virtual packages explicitly
@pytest.mark.integration
def test_solve_without_cuda_explicit(make_env):
    virtual_packages = """subdirs:
    linux-64:
        packages:
            __glibc: 2.28
            __unix: 0
            __linux: 5.15
"""
    env = make_env(environments["pytorch"])
    virtual_packages_yaml = make_env(virtual_packages, name="vpckg_spec")

    package_list = solve_environment(
        env, "conda", "linux-64", virtual_packages_yaml
    )

    for pkg in package_list:
        if pkg["name"] == "pytorch":
            assert "cuda" not in pkg["fn"]
            assert "cpu" in pkg["fn"]
            return

    pytest.fail("pytorch package not found in solution")
