# Project Description
Conda Vendor is a tool to create local conda channels based on a [conda environment yaml file](https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#create-env-file-manually). The created local channel will only contain the packages that are required when the yaml file installs. This is the same concept as [mirroring a channel](https://docs.anaconda.com/anaconda-repository/admin-guide/install/config/mirrors/mirror-anaconda-repository/) except only the required packages will be downloaded locally. This vastly descreases the size of the resulting mirrored channel.

Conda Vendor also creates software version manifests based on a conda environment configuration file. These files contain the package name, download URL, and sha256 hash of all packages and dependencies from the input conda environment file.

# Setup
All below steps should be run from within `conda-vendor` directory. This guide assumes that conda is pre-installed and configured.

To create a conda environment with the dependencies for conda vendor:

	conda env create -f conda_vendor_test.yaml

Activate the environment 

	conda activate conda_vendor_test_env

### Tests 
Make sure everything is good to go with

	pytest -vvv

# Usage
`conda-vendor` solves an environment from an environment.yaml and currently has two main functions:

* create a `meta_manifest.yaml` a yaml for CICD
* Create local channels to resolve an environment offline. 

### Manifest
To create a manifest run:
```bash
	conda-vendor manifest -f your_env.yaml --manifest-filename your_manifest_out.yaml
```

if no manifest filename is supplied it will default to `meta_manifest.yaml`.

It will looks something like this:
```
resources:
  - url: "https://s3.amazonaws.com/path/to/your/package-1.0.0.tar.gz"
    filename: "package-1.0.0.tar.gz"
    validation:
      type: "sha256"
      value: "3d6b4cfca92067edd5c860c212ff5153d1e162b8791408bc671900309eb555ec" # must be lowercase

```
where each entry contains information about a package in your environment.

### Local channels
running `conda-vendor local_channels -f your_env_yaml.yaml` will do the following:
* solve the environment
* create a `meta_manifest.yaml`
* create local channels for the channels supplied in `your_env_yaml.yaml`
* Create a `local_yaml.yaml` with the local channels and packages needed for your env with an environment name that has a `local_` prefixed to the original environment name

local_channels also has options for custom paths and names. 
```
optional arguments:
  -h, --help            show this help message and exit
  --dry-run             local environment filename
  -f FILE, --file FILE  environment.yaml file
  --channel-root CHANNEL_ROOT
                        create local directories here
  -m MANIFEST_FILENAME, --manifest-filename MANIFEST_FILENAME
                        write manifest to this file
  -n NAME, --name NAME  local environment name
  -e ENVIRONMENT_FILE, --environment-file ENVIRONMENT_FILE
                        local environment filename
```

### Create an offline conda environment 

	conda env create -f local_yaml.yaml --offline
>if you used a custom name for your local yaml use the name of that file.

### Notes:
* If you do not have pip as a required package in your yaml you will need to export the flag
`export CONDA_ADD_PIP_AS_PYTHON_DEPENDENCY=False` 
* If you have channels `defaults` in your `env.yaml` conda-vendor will throw a runtime error. Please explicitly state the needed channels.
* Logging is always on :( sorry
* cli needs tests and has some extra features

# Building a python wheel
Build your conda-vendor wheel 

	python setup.py bdist_wheel

Install the package 

	pip install dist/conda_vendor-0.1-py3-none-any.whl

Make sure it looks good 

	conda-vendor -h

You should see something like 
```
conda-vendor creates a local conda environment

positional arguments:
  {manifest,local_yaml,local_channels}
                        command options
    manifest            mainifest commands
    local_yaml          local yaml commands
    local_channels      local channel commands
```
