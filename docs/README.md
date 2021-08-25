# Conda Vendor docs

## Building docs
With conda installed, run the below commands to build the docs

```
conda env create -f doc_build_env.yaml
sphinx-build . _build
```

Then open _build/index.html with web browser

## Adding new files

To add a new file to the sphinx docs, edit or add a `toctree` block to the `index.md` file:

```
```{toctree}
:maxdepth: 1
:caption: Introduction
source/example.md
```
