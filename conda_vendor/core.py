import json
import subprocess
import pathlib
import requests
import yaml
import hashlib
import sys
from conda_lock.conda_lock import solve_specs_for_arch
from conda_lock.src_parser.environment_yaml import parse_environment_file


class CondaLockWrapper:
    def __init__(self, platform="linux-64"):
        self.platform = platform

    def parse(self, environment_yml):
        lock_specs = parse_environment_file(environment_yml, self.platform)
        return lock_specs.specs

    def solve(self, specs):
        solved_env = solve_specs_for_arch(
            "conda", ["main"], specs=specs, platform="linux-64"
        )

        link_actions = solved_env["actions"]["LINK"]
        return link_actions


class CondaChannel:
    def __init__(self, platforms=["linux-64", "noarch"]):
        self.base_url = "https://repo.anaconda.com/pkgs/main/"
        self.platforms = platforms
        self._repodata_dict = None

    # needs test
    def fetch(self, requests=requests):
        repodata = {}
        for platform in self.platforms:
            repodata_url = self.base_url + platform + "/repodata.json"
            repodata[platform] = requests.get(repodata_url).json()
        self._repodata_dict = repodata

    def filter_repodata(self, package_list, platform="linux-64"):
        filtered_content = {
            "packages": {},
            "packages.conda": {},
            "info": self._repodata_dict[platform]["info"],
        }
        packages = self._repodata_dict[platform]["packages"]
        conda_packages = self._repodata_dict[platform]["packages.conda"]

        for pkg_name in package_list:
            if pkg_name in packages.keys():
                filtered_content["packages"][pkg_name] = packages[pkg_name]

            if pkg_name in conda_packages.keys():
                filtered_content["packages.conda"][pkg_name] = conda_packages[pkg_name]

        return filtered_content

    # has test
    def create_dot_conda_and_tar_pkg_list(self, match_list, platform="linux-64"):
        dot_conda_channel_pkgs = [
            pkg.split(".conda")[0]
            for pkg in self._repodata_dict[platform]["packages.conda"].keys()
        ]

        desired_pkg_extension_list = []

        for pkg in match_list:
            if pkg in dot_conda_channel_pkgs:
                desired_pkg_extension_list.append(f"{pkg}.conda")
            else:
                desired_pkg_extension_list.append(f"{pkg}.tar.bz2")

        return desired_pkg_extension_list

   
    def format_manifest(self, pkg_extension_list, base_url, platform):
        manifest_list = []

        for pkg in pkg_extension_list:
            if pkg.endswith(".conda"):
                pkg_type = "packages.conda"
            else:
                pkg_type = "packages"

            manifest_list.append(
                {
                    "url": f"{base_url}/{platform}/{pkg}",
                    "name": f"{pkg}",
                    "validation": {
                        "type": "sha256",
                        "value": self._repodata_dict[platform][pkg_type][pkg]["sha256"],
                    },
                }
            )

        return manifest_list


def fetch_repodata(package_file_names_list, requests=requests, platform="linux-64"):
    conda_channel = CondaChannel()
    conda_channel.fetch()
    filtered_content = conda_channel.filter_repodata(
        package_file_names_list, platform=platform
    )

    return filtered_content

#TODO: need a function to write yaml dump probably just add out to this 
def conda_vendor(environment_yml):
    specs = parse_environment(environment_yml)
    manifest = conda_vendor_artifacts_from_specs(specs)
    return yaml.dump(manifest)


def parse_environment(environment_yml):
    parser = CondaLockWrapper()
    specs = parser.parse(environment_yml)

    return specs

#needs mock on test
def conda_vendor_artifacts_from_specs(specs):
    link_actions = CondaLockWrapper().solve(specs)
    base_url = "https://repo.anaconda.com/pkgs/main"  # link_actions[0]['base_url]
    platform = "linux-64"

    conda_channel = CondaChannel()
    conda_channel.fetch()
    repodata = conda_channel._repodata_dict["linux-64"]

    linux_64_pkg_names = [
        link["dist_name"] for link in link_actions if link["platform"] == "linux-64"
    ]

    linux_64_pkg_correct_extensions = conda_channel.create_dot_conda_and_tar_pkg_list(
        linux_64_pkg_names, platform="linux-64"
    )

    noarch_packages = [
        link["dist_name"] for link in link_actions if link["platform"] == "noarch"
    ]

    noarch_packages_correct_extensions = (
        conda_channel.create_dot_conda_and_tar_pkg_list(
            noarch_packages, platform="noarch"
        )
    )

    linux_64_manifest_list = conda_channel.format_manifest(
        linux_64_pkg_correct_extensions, base_url=base_url, platform="linux-64"
    )
    noarch_manifest_list = conda_channel.format_manifest(
        noarch_packages_correct_extensions, base_url=base_url, platform="noarch"
    )
    complete_manifest_list = linux_64_manifest_list + noarch_manifest_list

    manifest_dict = {"resources": complete_manifest_list}

    return manifest_dict


def create_channel_directories(channel_path="./"):
    channel_root = pathlib.Path(channel_path)
    local_channel = channel_root / "local_channel"
    local_channel.mkdir()

    linux_dir = local_channel / "linux-64"
    linux_dir.mkdir()

    noarch_channel = local_channel / "noarch"
    noarch_channel.mkdir()

    return local_channel

def download_and_validate(out, url, sha256, requests=requests):
    url_data = requests.get(url)
    print("yo", url_data )
    with open(out, "wb") as f:
        f.write(url_data)
        calculated_sha = calc_sha256(url_data)
        if sha256 != calculated_sha:
            raise RuntimeError(f'SHA256 does not match for {out} calculated SHA: {calculated_sha}, '
                'manifest SHA: {sha256}')


def calc_sha256(byte_array):                                                            
    return hashlib.sha256(byte_array).hexdigest()

def download_binaries(manifest_dict : dict, local_channel_obj, requests=requests) -> None:
    # TODO: validate the sha 256 in seperate function, Not currently validating files ONLY download.
    resources_list = manifest_dict["resources"]
    linux_dir = local_channel_obj / "linux-64"
    noarch_dir = local_channel_obj / "noarch"

    for resource in resources_list:        
        output_path = noarch_dir if "noarch" in resource["url"] else linux_dir
        if resource["validation"]["type"] != "sha256":
            raise RuntimeError('invalid checksum type: {resource["validation"]["type"]}')
        download_and_validate(output_path / resource["name"], 
            resource["url"], resource["validation"]["value"], requests=requests)
