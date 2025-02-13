#!venv/bin/python3
"""Tool to handle common commands in the elements SDK."""
# pylint: disable=invalid-name

import argparse
import os
import logging
import shutil

from base import environment, get_socs, get_boards_for_soc, get_soc_name, get_board_name, _RELEASE
from base import command


_FORMAT = "%(asctime)s - %(message)s"


def parse_args():
    """Parses all common related arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', action='store_true', help="Enables debug output")

    subparsers = parser.add_subparsers(help="Elements commands", dest='command')
    subparsers.required = True

    parser_checkout = subparsers.add_parser('checkout', help="Checks out all repositories")
    parser_checkout.set_defaults(func=checkout)
    parser_checkout.add_argument('--manifest', help="Repo manifest")
    parser_checkout.add_argument('-f', action='store_true', help="Force checkout")

    parser_init = subparsers.add_parser('init', help="Initialise the SDK")
    parser_init.set_defaults(func=init)
    parser_init.add_argument('--manifest', help="Repo manifest")
    parser_init.add_argument('-f', action='store_true', help="Force init")

    parser_clean = subparsers.add_parser('clean', help="Cleans all builds")
    parser_clean.set_defaults(func=clean)
    parser_clean.add_argument('soc', help="Name of a SOC", nargs="?")
    parser_clean.add_argument('board', help="Name of a board", nargs="?")

    parser_socs = subparsers.add_parser('socs', help="Lists all available SOCs.")
    parser_socs.set_defaults(func=socs)

    parser_boards = subparsers.add_parser('boards', help="Lists all available boards for a SOC.")
    parser_boards.set_defaults(func=boards)
    parser_boards.add_argument('soc', help="Name of a SOC")

    return parser.parse_args()


def checkout(args, env, cwd):
    """Checks out all repositories."""
    cwd_internal = os.path.join(cwd, "internal")

    if args.f:
        command("rm -rf internal/.repo", env, cwd)
    if os.path.exists("internal/.repo"):
        raise SystemExit("Repo exists! Either the SDK is already initialized or force init.")

    if not os.path.exists("internal/repo"):
        with open("internal/repo", "w", encoding='UTF-8') as text_file:
            command("curl https://storage.googleapis.com/git-repo-downloads/repo-1", env, cwd,
                    stdout=text_file)

            command("chmod a+x repo", env, cwd_internal)

    cmd = "python3 repo init -u https://github.com/aesc-silicon/elements-manifest.git" \
          " -m {}".format(args.manifest if args.manifest else _RELEASE + ".xml")
    command(cmd, env, cwd_internal)

    command("python3 repo sync", env, cwd_internal)

    print("Checkout done")


def init(args, env, cwd):
    """Clones all repositories, installs and/or build all packages."""
    checkout(args, env, cwd)

    command("./.init.sh {}".format(env['ZEPHYR_SDK_VERSION']), env, cwd)

    print("Initialization finished")


def clean(args, env, cwd):  # pylint: disable=unused-argument
    """Cleans all build by remove the build directory."""
    path = "build/"
    if args.soc:
        path = os.path.join(path, get_soc_name(args.soc))
    if args.board:
        path = os.path.join(path, get_board_name(args.board))
    if os.path.exists(path):
        logging.debug("Remove path %s", path)
        shutil.rmtree(path)
    else:
        print(f"Path {path} does not exist!")


def socs(args, env, cwd):  # pylint: disable=unused-argument
    """Lists all available SOCs by existing SOC files."""
    for soc in get_socs():
        print(f"{soc}")


def boards(args, env, cwd):  # pylint: disable=unused-argument
    """Lists all available boards for a SOC."""
    for board in get_boards_for_soc(args.soc):
        print(f"{board}")


def main():
    """Main function."""
    args = parse_args()
    if args.v:
        logging.basicConfig(format=_FORMAT, level=logging.DEBUG)
    env = environment()
    cwd = os.path.dirname(os.path.realpath(__file__))
    if hasattr(args, 'func'):
        args.func(args, env, cwd)

main()
