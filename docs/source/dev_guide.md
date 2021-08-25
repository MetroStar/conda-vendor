# Packages and Repodata

There are two main main pieces that conda vendor manipulates:
packages, and `repodata.json` files. Packages are compressed files with the extensions `.tar.bz2` or `.conda`. Every conda channel with packages in it must contain these two types of files.

# Conda Channels

Below is a simplified example of a conda channel output.

``` bash
$ tree
example-channel/
├── channeldata.json
├── index.html
├── linux-64
│   ├── example_package.tar.bz2
│   ├── repodata.json
└── noarch
    ├── example_package_dependency.tar.bz2
    └── repodata.json
```

Conda channels can contain packages for many different system
architectures. These packages are stored in separate directories. For the above channel it has a directory for linux 64 bit operating system (linux-64), and packages that are architecture independant (noarch).

## Package Files and Repodata.json

A package files contains the source code for the particular package along other metadata on what that package requires to run.

The repodata.json file is created when the conda channel is indexed. This file contains a list of packages available in the channel along with a list of their dependencies. Whenever a `conda install <package_name>` is run, conda downloads the repodata.json files from the channel. The solver then checks the dependencies of all requested packages to "solve" the environment. A "solved" environmnet is one where we have a list of a packages and dependencies to download which all have compatible versions.

## Creating a conda channel

If I wanted to recreate the above channel, I would first install [conda build](https://docs.conda.io/projects/conda-build/en/latest/install-conda-build.html). I would then run:

```bash
	$ mkdir example-channel
	$ cd example-channel
	$ conda index -s linux-64 -s noarch
```

This would create an empty channel. Then to add a package to the channel, I would move the package into the proper directory and re-index the channel.

```bash
	$ mv ~/example_package.tar.bz2 ./linux-64
	$ mv ~/example_package_dependency.tar.bz2 ./noarch
	$ conda index -s linux-64 -s noarch
```

The conda index command above will read the metadata from the recently added packages. The dependencies for these packages then gets added to the repodata.json file.

# Main Channel Repodata Hotfix

Because occasionally the dependency constraints on packages can change long after a package is added to a channel. To account for this, the Anaconda main channel uses [a hotfix repo]https://github.com/AnacondaRecipes/repodata-hotfixes to edit the repodata.json when constraints change. Without this hotfix environements often will fail to solve properly. Conda-forge uses a [similar approach](https://github.com/conda-forge/conda-forge-repodata-patches-feedstock). 


# Creating Local Channels
To avoid conflicting solves due to hotfixes conda vendor doesn't update any of the package metadata in repodata.json. Conda Vendor removes all of the metadata for packages that are required to solve the input environment yaml file. It also manually creates the folder structure and downloads the package tarballs to the relevant folder.

The end result is that we have a local channel without ever having to run the `conda index` command and corrupting the local repodata. 

## Side effects of approach
Because of the issue with repodata, conda vendor doesn't support merging channels. If we have an input environment file with two source channels:

```yaml
name: test
channels:
  - main
  - conda-forge
packages:
  ...
```

The output will also include two output channels, `local_main` and `local_conda-forge`. 
