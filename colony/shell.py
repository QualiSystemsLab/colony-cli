"""
Usage:
      colony bp validate <name> --space=<space> --token=<token> [-b --branch <branch>] [-c --commit <commitId>]

Options:
  -h --help     Show this screen.
"""

#TODO(ddovbii): refactor. split on modules, add subcommands
from docopt import docopt
from .client import ColonyClient
from pprint import pprint


def main():
    args = docopt(__doc__)
    client = None

    #auth
    token = args.get('--token', '')
    space = args.get('--space', '')

    try:
        client = ColonyClient(space=space, token=token)
    except Exception as e:
        print(f"Unable to create client. Check your token. Details {e}")

    if 'bp' in args and 'validate' in args:
        do_blueprint_validate(client, args)

def do_blueprint_validate(client, args):
    name = args.get('<name>')
    branch = args.get('<branch>')
    commit = args.get('<commitId>')

    if commit and branch is None:
        print("Since commit is specified, branch is required")
        return

    try:
        bp = client.blueprints.validate(blueprint=name, branch=branch, commit=commit)
    except Exception as e:
        print(f"Unable to run command. Details {e}")
        return

    errors = bp.errors
    if errors:
        pprint(errors)

    else:
        print("Valid!")


if __name__ == '__main__':
    main()