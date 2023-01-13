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

#### Specifying Virtual Packages
Conda uses *virtual packages* as a way to track system dependencies.
For more information about *virtual packages* see the conda documentation
[Managing virtual packages](https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-virtual.html).
Since these are not real packages they might not exist on the host system, or
they might need to be manually specified. `conda-vendor` allows you to pass in
a yaml file describing the *virtual packages* that are needed and their version.

By default `conda-vendor` uses a set of packages tied to the `--platform`
options.  To override this selection use the `--virtual-package-spec` options
with the path to a spec yaml.  The yaml should look something like
```yaml
subdirs:
  linux-64:
    packages:
      __glibc: 2.17
      __cuda: 11.4
```
For more information see the documentation for
[`conda-lock`](https://github.com/conda-incubator/conda-lock).

In order to assist with a correct choice of *virtual packages*, `conda-vendor` now
includes a convenience command `virtual-packages` that will create an
appropriately formatted virtual package spec for the system
that conda vendor is running on.
```bash
$ conda-vendor virtual-packages
```
Which might output something like:
```yaml
subdirs:
    osx-64:
        packages:
            __archspec: '1'
            __osx: 10.15.7
            __unix: '0'
````
