import json
import subprocess
import pathlib
import requests
import yaml
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
        self._repodata = None

    def fetch(self, requests=requests):
        repodata = {}
        for platform in self.platforms:
            repodata_url = self.base_url + platform + "/repodata.json"
            repodata[platform] = requests.get(repodata_url).json()

        self._repodata = repodata

    def _add_repodata_info(self, contents, platform="linux-64"):
        contents["info"] = self._repodata[platform]["info"]
        return contents

    def filter_repodata(self, package_list, platform="linux-64"):
        filtered_content = {}
        packages = self._repodata[platform]["packages"]
        conda_packages = self._repodata[platform]["packages.conda"]

        for pkg_name in package_list:
            if pkg_name in packages.keys():
                if "packages" not in filtered_content.keys():
                    filtered_content["packages"] = {}
                filtered_content["packages"][pkg_name] = packages[pkg_name]

            if pkg_name in conda_packages.keys():
                if "packages.conda" not in filtered_content.keys():
                    filtered_content["packages.conda"] = {}
                filtered_content["packages.conda"][pkg_name] = conda_packages[pkg_name]

        filtered_content = self._add_repodata_info(filtered_content)
        return filtered_content

    def create_dot_conda_and_tar_pkg_list(self, match_list, platform="linux-64"):
        dot_conda_channel_pkgs = [
            pkg.split(".conda")[0]
            for pkg in self._repodata[platform]["packages.conda"].keys()
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
                        "value": self._repodata[platform][pkg_type][pkg]["sha256"],
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


def conda_vendor(environment_yml):
    specs = parse_environment(environment_yml)
    manifest = conda_vendor_artifacts_from_specs(specs)
    return yaml.dump(manifest)


def parse_environment(environment_yml):
    parser = CondaLockWrapper()
    specs = parser.parse(environment_yml)

    return specs


def conda_vendor_artifacts_from_specs(specs):
    link_actions = CondaLockWrapper().solve(specs)
    base_url = "https://repo.anaconda.com/pkgs/main"  # link_actions[0]['base_url]
    platform = "linux-64"

    conda_channel = CondaChannel()
    conda_channel.fetch()
    repodata = conda_channel._repodata["linux-64"]

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
    # import ipdp; ipdb.set_trace()

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


def download_and_validate(manifest_dict, local_channel_obj, requests=requests):

    resources_list = manifest_dict["resources"]
    linux_dir = local_channel_obj / "linux-64"
    noarch_channel = local_channel_obj / "noarch"

    for resource in resources_list:
        url_data = requests.get(resource["url"])
        print(url_data)
        if "noarch" in resource['url']:
            with open(noarch_channel / resource["name"], "wb") as f:
                f.write(url_data)
        else:
            with open(linux_dir / resource["name"], "wb") as f:
                f.write(url_data)
