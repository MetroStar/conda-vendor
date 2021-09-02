from setuptools import find_packages, setup

# TODO: we can make this a conda package and have but that will be on the next iteration.
# TODO: Some more work can be done on the setup requires but for now use the conda_vendor_test.yml
# if you want to build the wheel.

setup(
    name="conda_vendor",
    version="0.1",
    package_dir={"": "."},
    packages=find_packages(exclude=("tests",), where="."),
    entry_points={"console_scripts": ["conda-vendor = conda_vendor.__main__:cli"]},
    install_requires=["pyyaml"],
    setup_requires=["wheel"],
    python_requires=">=3.8",
)
