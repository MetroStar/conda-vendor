## `conda-vendor`
Tool to create local conda channels and manifests for vendor deployments

## General Workflow
1. Generate a conda solved environment file from an environment.yml
2. Figure out all the packages that need to be downloaded
3. Download repodata.json and repodata.json.bz2 from the channel  https://repo.anaconda.com/pkgs/main/linux-64/repodata.json
4. Filter out repodata.json and repodata.json.bz2
5. Generate a vendor manifest with download urls and sha256  (https://repo.anaconda.com/pkgs/main/linux-64/)
6. Download all packages and copy repodata.json and repodata.json.bz2 based on the hardening manifest
Repodata.json, repodata.json.ls bz2, vendor_manifest.yaml,
7. generate a local conda channel
8. Validate that you can solve the environment with the above environment.yml file and local channel

## TODO
- Parse environment.yml to get teh specs
- use the specs to solve the conda environment  (```conda create -p /fake-pre python=3.9.5 other-package --dry-run --json```)

## Inputs
- `environment.yml`cd 
## Outputs
- `repodata.json`
- `vendor_manifest.yaml`
```
resources:
  - url: "https://s3.amazonaws.com/path/to/your/package-1.0.0.tar.gz"
    filename: "package-1.0.0.tar.gz"
    validation:
      type: "sha256"
      value: "3d6b4cfca92067edd5c860c212ff5153d1e162b8791408bc671900309eb555ec" # must be lowercase

```
`vendor_manigest.yaml`

## P1's Hardening Manifest:
- https://repo1.dso.mil/dsop/dccscr/-/tree/master/hardening%20manifest