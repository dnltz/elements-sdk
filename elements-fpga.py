#!venv/bin/python3
"""Tool to handle all FPGA projects in the elements SDK."""
# pylint: disable=invalid-name

import os
import logging

from base import prepare_build, environment, open_board, get_soc_name, get_board_name, parse_args
from base import command
from base import prepare, compile_, generate, functional_simulation


_FORMAT = "%(asctime)s - %(message)s"


def parse_fpga_args(subparsers, _):
    """Parses all FPGA related arguments."""
    parser_simulate = subparsers.add_parser('simulate', help="Simulates a design")
    parser_simulate.set_defaults(func=simulate)

    parser_synthesize = subparsers.add_parser('synthesize', help="Synthesizes the design")
    parser_synthesize.set_defaults(func=synthesize)
    parser_synthesize.add_argument('--toolchain', default="xilinx", choices=['xilinx', 'symbiflow'],
                                   help="Choose between different toolchains.")

    parser_build = subparsers.add_parser('build', help="Run the complete flow to generate a "
                                                       "bitstream file.")
    parser_build.set_defaults(func=build)
    parser_build.add_argument('application', nargs='?', default="",
                              help="Name of an application")
    parser_build.add_argument('-f', action='store_true', help="Force build")
    parser_build.add_argument('--toolchain', default="xilinx", choices=['xilinx', 'symbiflow'],
                              help="Choose between different toolchains.")

    parser_test = subparsers.add_parser('test', help="Tests the kit")
    parser_test.set_defaults(func=test)
    parser_test.add_argument('case', help="Name of the test case")


def simulate(args, env, cwd):
    """Command to simulate a SOC on a virtual board."""
    functional_simulation(args, env, cwd)


def synthesize(args, env, cwd):
    """Command to synthesize a SOC for a board."""
    soc = get_soc_name(args.soc)
    board = get_board_name(args.board)
    board_data = open_board(args.board)
    env['SOC'] = soc
    env['BOARD'] = board

    if not os.path.exists(f"build/{soc}/{board}/zibal/{board}Top.v"):
        raise SystemExit("No SOC design found!\n"
                         f" Run \"./elements-fpga.py {args.soc} {args.board} generate\" before.")

    if args.toolchain == 'xilinx':
        if 'xilinx' not in board_data:
            raise SystemExit(f"No xilinx definitions in board {args.board}")
        env['PART'] = board_data['xilinx']['part']
        env['TCL_PATH'] = os.path.join(cwd, "internal/zibal/eda/Xilinx/vivado/syn")

        xilinx_cwd = os.path.join(cwd, f"build/{soc}/{board}/vivado/syn")
        command("vivado -mode batch " \
                "-source ../../../../../internal/zibal/eda/Xilinx/vivado/syn/syn.tcl " \
                "-log ./logs/vivado.log -journal ./logs/vivado.jou", env, xilinx_cwd)
    if args.toolchain == 'symbiflow':
        if not 'xilinx' in board_data:
            raise SystemExit("No xilinx definitions in board {}".format(args.board))
        env['PART'] = board_data['xilinx']['part']
        env['PART'] = board_data['xilinx']['part'].lower()
        env['DEVICE'] = "{}_test".format(board_data['xilinx']['device'])

        symbiflow_cwd = os.path.join(cwd, "internal/zibal/eda/Xilinx/symbiflow")
        command("make clean", env, symbiflow_cwd)
        command("./syn.sh", env, symbiflow_cwd)


def build(args, env, cwd):
    """Command to compile, generate and synthesize a board."""
    prepare(args, env, cwd)
    compile_(args, env, cwd)
    generate(args, env, cwd)
    synthesize(args, env, cwd)


def test(args, env, cwd):
    """Command to run tests in different projects for a kit."""
    soc = get_soc_name(args.soc)
    board = get_board_name(args.board)
    env['SOC'] = soc
    env['BOARD'] = board

    command(f"sbt \"runMain elements.soc.{soc.lower()}.{board}Simulate {args.case}\"", env, cwd)


def main():
    """Main function."""
    args = parse_args(parse_fpga_args)
    if args.v:
        logging.basicConfig(format=_FORMAT, level=logging.DEBUG)
    env = environment()
    if hasattr(args, 'soc') and hasattr(args, 'board'):
        prepare_build(args)
    cwd = os.path.dirname(os.path.realpath(__file__))
    if hasattr(args, 'func'):
        args.func(args, env, cwd)

main()
