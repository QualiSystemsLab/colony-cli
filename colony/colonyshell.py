"""

Usage:
  colony bp validate
    --name=<blueprint_name>
    --space=<space_name>
    --token=<colony_token>

Options:
  -h --help     Show this screen.


"""
from docopt import docopt
from requests import Session

def main():
    args = docopt(__doc__)

    token = args.get('--token', '')

    if 'bp' in args and 'validate' in args:
        bp_name = args.get('--name')
        space = args.get('--space')
        do_blueprint_validate(token, bp_name, space)

def do_blueprint_validate(token, name, space):
    session = Session()
    session.headers.update({'Authorization': 'Bearer {}'.format(token)})

    url = f"https://cloudshellcolony.com/api/spaces/{space}/validations/blueprints"
    payload = {
        'blueprint_name': name,
        'type': 'sandbox'
    }
    res = session.post(url=url, json=payload)
    if res.status_code == 200:
        errors =  res.json().get('errors', None)
        if not errors:
            print('Valid')
        else:
            print(errors)

if __name__ == '__main__':
    main()