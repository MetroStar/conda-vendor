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

### Development Installation
Create a conda environment with conda-vendor development dependencies:
```bash
mamba env create --file environment.yaml
```

Install conda-vendor as an editable pip package:
```bash
pip install -e .
```

Running Tests:
```bash
pytest tests/ -vvv -s
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

Use Dry-Run install to verify that conda can solve using only the vendored channel:
```bash
# NOTE: ensure to use the same solver used to create the vendored channel
# example channel vendored with mamba: that includes micromamba python and pip
mamba create -n some-new-env --offline --channel ./my-vendored-channel --override-channels --dry-run micromamba python pip 
```

