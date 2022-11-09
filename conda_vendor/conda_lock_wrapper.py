from conda_lock.src_parser.environment_yaml import parse_environment_file
from conda_lock.conda_solver import solve_specs_for_arch, _reconstruct_fetch_actions, solve_conda
from conda_lock.virtual_package import default_virtual_package_repodata

# Wrapper class around certain conda-lock functions
class CondaLockWrapper:
    # create a static method from conda_lock.src_parser.parse_environment()
    # returns a LockSpecification
    @staticmethod
    def parse_environment_file(*args):
        return parse_environment_file(*args)

    # create a static method from conda_lock
    @staticmethod
    def solve_specs_for_arch(*args):
        return solve_specs_for_arch(*args)

    # patch our repodata.json with LINK actions
    @staticmethod
    def reconstruct_fetch_actions(*args):
        return _reconstruct_fetch_actions(*args)

    # create a repository with faked virtual package repodata
    @staticmethod
    def default_virtual_package_repodata():
        return default_virtual_package_repodata()

    @staticmethod
    def solve_conda(*args):
        return solve_conda(*args)

