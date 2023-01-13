# Project Description

Conda Vendor is a tool to create local conda channels and manifests based on
an input conda environment yaml file. This tool is particularly useful when
trying to use conda packages inside an air-gapped network.

The tool works by intaking a [conda environment yaml file](https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#create-env-file-manually) and performing a conda solve to determine what packages are needed.  Conda vendor will download those packages and provide `repodata.json`
files for the relevant directories, so that the downloaded files are a
valid conda channel.

## Usage

#### Creating a Local Channel
The most basic way to use `conda-vendor` is to just pass an `environment.yaml`
file to the `vendor` subcommand
```bash
$ conda-vendor vendor --file my_environment.yaml
```

This will solve the environment specified in `my_environment.yaml` using the
host platform.  Sometimes it is necessary or desirable to solve for another
platform.  The `vendor` command allows this with the `--platform` flag.  The
usage looks like
```bash
$ conda-vendor vendor --file my_environment.yaml  --platform linux-64
```

By default `conda-vendor` will use a set of *virtual packages* for the
specified platform. Under the hood `conda-vendor` uses the package
`conda-lock`, with the default virtual packages from `conda-lock`, to solve
the environment.[^1]  Virtual packages are the mechanism conda uses to encode
system specific configuration.  For more information about *virtual packages*
see the conda documentation
[Managing virtual packages](https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-virtual.html).

[^1]:The `conda-lock` documentation is located here:
    [conda-lock](https://github.com/conda-incubator/conda-lock).  The set of
default packages must be read from the `conda-lock` source code specifically
in the `conda_lock.virtual_package` module.


**note: If no platform option is supplied to `conda-vendor`, it will use the
host platform as if it were supplied explicitly.  This means that
`conda-vendor` will use the default set of *virutal packages* specified by
`conda-lock`, and so the *virtual packages* might not be correct for the host.
To ensure a correct solution supply the virtual packages explictly as
explaineed below.**

These packages can be overwritten by providing a yaml file
specifying the desired *virtual packages* using the `--virtual-package-spec`
option:
```bash
$ conda-vendor vendor --file my_environment.yaml  \
                      --platform linux-64 \
                      --virtual-package-spec my_virtual_packages.yaml
```

The `conda-vendor vendor` command also has an option `--dry-run` to allow
solving the environment without downloading files.  It outputs a json
formatted block of text describing all the files that would be downloaded in
the local channel.

#### Using the Local channel

There are several ways to use the local channel. If python was in the input
`environment.yaml` file for example, the following could be used:

	conda create -n test_env python -c <path_to_local_channel> --offline

The `--offline` flag will prevent conda from reaching out to the internet for
packages. To verify that the environment created only contains packages
contained in the local channel, run the following:

	conda activate test_env
	conda list --explicit

This should show a list of all the packages in the environment and the local
paths to their source code (typically tar.bz2 files).


## Creating a Custom Manifest for Package Security Validation

The following functionality is only applicable if there is an organization
that requires a list of packages for security validation. Currently the Iron
Bank format is supported, but support for other formats can potentially be
added in the future.

To generate an iron bank manifest from the `environment.yaml`, use the
`ironbank-gen` subcommand:

```bash
$ conda-vendor ironbank_gen --file my_environment.yaml ....
```
This will output a manifest file in the Iron Bank required format.  This can
also be accomplished as part of the local channel creation by passing
the flag `--ironbank-gen` to the `vendor` subcommand:
```bash
$ conda-vendor ...vendor arguments... --ironbank_gen
```

