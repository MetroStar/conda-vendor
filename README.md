# Conda-Vendor
Conda Vendor is a tool to create local conda channels and manifests for vendor deployments

## Installation

To install with pip, run:

	pip install conda-vendor
	
## Usage
Conda-vendor has two main steps to create a local channel. First, a meta-manifest file is created as an intermediate artifact. With an existing meta-manifest file, a local conda channel can then be craeted

The reason for the intermediate file is to allow for custom software manifests. These manifests can them be used obtain approve packages by an organizations cybersecurity team.

### Creating a Metamanifest
Conda-vendor solves an environment with conda from an `environment.yaml` and determines all the packages that are required. The metadata about these required packages is output in a file called `meta_manifest.yaml`. To create this file run:

	conda vendor create-meta-manifest --environment-yaml environment.yaml
		
	
The above command will output a `meta_manifest.yaml` file in the current directory. 

### Creating a Local Channel

With a meta-manifest file created, conda-vendor can then create local channels. 
	
	conda vendor create-channels --meta-manifest-path ./meta_manifest.yaml

This will create a directory called `local_channel` that will contain the same nummber of channels as were listed in the original `environment.yaml` file. These local channels will only contain the packages that are needed to satisfy the solved environment from the `create-meta-manifest` step.

### Using the Local channel

There are several ways to use the local channel. If python was in the input `environment.yaml` file for example, the following could be used:

	conda create -n test_env python -c <path_to_local_channel> --offline
	
The `--offline` flag will prevent conda from reaching out to the internet for packages. To verify that the environment created only contains packages that were in the local channel, run the following:

	conda activate test_env
	conda list --explicit
	
This should show a list of all the packages in the environment, and show the local path to their source code (typically tar.bz2 files).

### Creating Environment with all Packages from Input Environment.yaml

Another wTo generate an conda environment yaml that will contain all the packages from the input `environment.yaml`, run this:

	conda vendor create-local-yaml --meta-manifest-path ./meta_manifest.yaml --channel-root <absolute_path_to_local_channel_dir>
	
This will create a environment file inside the `local_channel` directory called `local_conda-vendor-env.yaml`. An environment can be created with:

	conda env create -f local_channel/local_conda-vendor-env.yaml
	
The environment will be created with the packages that are contained in the local channel.

### Creating a Custom Manifest for Package Security Validation

The following functionality is only applicable if there is an organization that requires a list of packages for security validation. Currently the Iron Bank format is supported, but other classes could be added to the source code in `custom_manifest.py`.

To generate an iron bank manifest from the meta-manifest, run:

	conda vendor create-custom-manifest --meta-manifest-path ./meta-manifest.yaml --output-manifest-path ./custom_manifest.yaml
	
This will output a manifest file in the Iron Bank format.