# Conda-Vendor

Conda Vendor is a tool to create local conda channels and attestetation manifests based on an input conda environment yaml file. This tool is particularly useful when trying to use conda packages inside an air-gapped network.


## Installation

To install with `pip`, run:
```bash
pip install conda-vendor
```

To install with `conda`, run:
```bash
conda install -c conda-forge conda-vendor
```

## Usage

#### Supported Solvers
* Conda
* Mamba
* Micromamba

Vendor dependencies from an  `environment.yaml` into a local channel:
```bash
# Use conda as the solver for linux-64
conda-vendor vendor --file environment.yaml --solver conda --platform linux-64

# use mamba as the solver for osx-64
conda-vendor vendor --file environment.yaml --solver mamba --platform osx-64

# use micromamba as the solver for the host platform
conda-vendor vendor --file environment.yaml --solver micromamba
```

