# `conda-vendor`
Conda Vendor is a tool to create local conda channels and manifests for vendor deployments

## Installation

To install with pip, run:
	pip install pip install conda-vendor
	
## Usage
`conda-vendor` solves an environment with conda from an `environment.yaml` and determines all the packages that are required. The metadata about these required packages is output in a file called `meta_manifest.yaml`. To create this file run:

	conda vendor create-meta-manifest --environment-yaml environment.yaml
		
	
The above command will output a `meta_manifest.yaml` file in the current directory. Conda-Vendor can then create local channels based on the package metadata it contains. 
	
	conda vendor create-channels --meta-manifest-path ./meta_manifest.yaml


