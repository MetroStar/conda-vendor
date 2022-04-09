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
Generate a local conda channel and attestation manifest based on an input `environment.yaml`:
```bash
conda-vendor vendor --file environment.yaml --solver conda --platform linux-64
```

