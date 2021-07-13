from setuptools import find_packages , setup 

#https://stackoverflow.com/questions/57821903/setup-py-with-dependecies-installed-by-conda-not-pip
#we need a meta.yaml and to remove conda lock from here, if we want the conda package
#yaml is a conda package 
##durrr
setup (name='conda_vendor',
       version='0.1',
       package_dir={"": "."},
       packages=find_packages(exclude=('tests', ), where="."),
       entry_points = {
           'console_scripts': [
               'conda-vendor = conda_vendor.__main__:main'
           ]
       },
       install_requires = ["pyyaml"],
       setup_requires = ['wheel'],
       python_requires=">=3.8"
       )