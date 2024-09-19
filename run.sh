conda deactivate conda-vendor-dependencies
conda env remove -n conda-vendor-dependencies

conda env create --file environment.yaml
conda activate conda-vendor-dependencies
pip install -e .

pytest tests/ -vvv -s