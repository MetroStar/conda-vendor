from pathlib import Path

from setuptools import find_packages, setup

# TODO: we can make this a conda package and have but that will be on the next iteration.
# TODO: Some more work can be done on the setup requires but for now use the conda_vendor_test.yml
# if you want to build the wheel.
root_dir = Path(__file__).absolute().parent

__version__ = None
exec(open(root_dir / "conda_vendor/version.py").read())  # Load __version__

from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="conda_vendor",
    version=__version__,
    package_dir={"": "."},
    packages=find_packages(exclude=("tests",), where="."),
    url="https://github.com/MetroStar/conda-vendor",
    entry_points={"console_scripts": ["conda-vendor = conda_vendor.__main__:cli"]},
    install_requires=["pyyaml", "conda-lock"],
    setup_requires=["wheel"],
    python_requires=">=3.6",
    long_description=long_description,
    long_description_content_type="text/markdown",
)
