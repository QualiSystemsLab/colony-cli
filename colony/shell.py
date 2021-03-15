"""
Usage: colony [--space=<space>] [--token=<token>] [--profile=<profile>] [--help] [--debug]
              <command> [<args>...]

Options:
  -h --help             Show this screen.
  --version             Show current version
  --space=<space>       Use a specific Colony Space, this will override any default set in the Colony config file
  --token=<token>       Use a specific token for authentication, this will override any default set in the
                        .colony\\config file
  --profile=<profile>   Use a specific Profile section in .colony\\config file

Commands:
    bp, blueprint       validate colony blueprints
    sb, sandbox         start sandbox, end sandbox and get its status
"""
import logging
import os

import pkg_resources
from docopt import DocoptExit, docopt

from colony.commands import bp, sb
from colony.config import ColonyConfigProvider, ColonyConnection
from colony.exceptions import ConfigError

logger = logging.getLogger(__name__)

commands_table = {
    "bp": bp.BlueprintsCommand,
    "blueprint": bp.BlueprintsCommand,
    "sb": sb.SandboxesCommand,
    "sandbox": sb.SandboxesCommand,
}


def is_help_needed(args):
    subcommand_args = args["<args>"]
    if not subcommand_args:
        return True

    return "--help" in subcommand_args or "-h" in subcommand_args


# NOTE: added to simplify command syntax
def validate_connection_params(args):
    if args["--profile"] and any([args.get("--token", None), args.get("--space", None)]):
        raise DocoptExit("If --profile is set, neither --space or --token must be provided!")


def get_connection_params(args) -> ColonyConnection:
    # first try to get them as options or from env variable
    token = args.pop("--token", None) or os.environ.get("COLONY_TOKEN", None)
    space = args.pop("--space", None) or os.environ.get("COLONY_SPACE", None)

    # then try to load them from file
    if not all([token, space]):
        logger.debug("Couldn't fetch token/space neither from command line nor environment variables")
        profile = args.pop("--profile", None)
        config_file = os.environ.get("COLONY_CONFIG_PATH", None)
        try:
            colony_conn = ColonyConfigProvider(config_file).load_connection(profile)
            token = token or colony_conn["token"]
            space = space or colony_conn["space"]
        except ConfigError as e:
            raise DocoptExit(f"Unable to read the Colony credentials. Reason: {e}")

    return ColonyConnection(token=token, space=space)


def main():
    version = pkg_resources.get_distribution("colony-cli").version
    args = docopt(__doc__, options_first=True, version=version)
    validate_connection_params(args)
    debug = args.pop("--debug", None)

    level = logging.DEBUG if debug else logging.WARNING
    logging.basicConfig(format="%(levelname)s - %(name)s - %(message)s", level=level)

    # Take command
    command_name = args["<command>"]
    if command_name not in commands_table:
        raise DocoptExit("Invalid or unknown command. See usage instruction by running 'colony -h'")

    # Take auth parameters
    if not is_help_needed(args):
        conn = get_connection_params(args)
    else:
        conn = None

    argv = [args["<command>"]] + args["<args>"]

    command_class = commands_table[command_name]
    command = command_class(argv, conn)
    command.execute()


if __name__ == "__main__":
    main()
