import pathlib
from conda_vendor.core import CondaChannel

def dump_extended_data(extended_data):
    for ch, plat in extended_data.items():
        print(f'{ch}')
        for subdir, rest in plat.items():
            print(f'  {subdir}')
            print(f"    repodata @ {rest['repodata_url']}")
            print('    files')
            for entry in rest['entries']:
                print(f"       {entry['fn']}")

def dump_repo_data(all_repo_data):
    for ch, plat in all_repo_data.items():
        print(f'{ch}')
        for subdir, rest in plat.items():
            print(f'  {subdir}')
            for key, val in rest.items():
                print(f'    {key}')
                if key == 'packages':
                    print(f'      {len(val)} packages')
                elif key == 'packages.conda':
                    print(f'      {len(val)} packages')


# test_yml.yaml
#
# name: minimal_env
# channels:
#   - main
#   - conda-forge
# dependencies:
#   - python=3.9.5
#   - conda-mirror

def main():
    environment_yml = pathlib.Path('test_yml.yaml')
    print(f'creating conda channel: {environment_yml}')
    ch = CondaChannel(environment_yml)
    print(f'ch: {ch}')
    print(f'channels: {ch.channels}')
    print(f'platforms: {ch.valid_platforms}')
    print()

    print('solving environment')
    sols = ch.solve_environment()
    print(f'sols: {len(sols)} entries')
    print()


    print('getting extended data')
    extended_data = ch.get_extended_data()
    dump_extended_data(extended_data)
    print()

    print('getting/filtering external repodata')
    all_repo_data = ch.get_all_repo_data()
    print('all_repo_data')
    dump_repo_data(all_repo_data)
    print()


    print('creating local repo data')
    ch.write_repo_data()
    print()

    print('downloading files')
    ch.download_binaries()
    print()


    print('making manifest')
    ch.create_manifest()
    print()

    print('making local environment yaml')
    ch.create_local_environment_yaml()
    print()

if __name__ == '__main__':
    main()
