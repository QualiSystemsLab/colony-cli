# Colony CLI

[![Coverage Status](https://coveralls.io/repos/github/QualiSystemsLab/colony-cli/badge.svg?branch=master)](https://coveralls.io/github/QualiSystemsLab/colony-cli?branch=master)
[![CI](https://github.com/QualiSystemsLab/colony-cli/workflows/CI/badge.svg)](https://github.com/QualiSystemsLab/colony-cli/actions?query=workflow%3ACI)
[![Python 3.8](https://img.shields.io/badge/python-3.8-blue.svg)](https://www.python.org/downloads/release/python-380/)
[![PyPI version](https://badge.fury.io/py/colony-cli.svg)](https://badge.fury.io/py/colony-cli)
[![Maintainability](https://api.codeclimate.com/v1/badges/5a9f730163de9b6231e6/maintainability)](https://codeclimate.com/github/QualiSystemsLab/colony-cli/maintainability)


---

![quali](quali.png)

## Cloudshell Colony CLI

Colony CLI is a Command Line interface tool for CloudShell Colony.

The main functionality this tool currently provides is validation of Colony Blueprints and launching of Sandbox environments from any branch in addition to testing local changes before committing them.

## Why use Colony CLI

When developing Blueprints for Colony, it can be very helpful to immediately check your work for errors.

Let's assume you are currently working in *development* branch, and you also have a main branch which is connected
to a Colony space. You would like to be sure that your latest local changes haven't broken anything before commiting to current branch and pushing to remote or before merging changes to main branch.

This is where this tool might be handy for you. Instead of reconnecting Colony to your development branch in the UI or going with "merge and pray" you can
use Colony CLI to validate your current Blueprints state and even launch Sandboxes.

## Installing

You can install Colony CLI with [pip](https://pip.pypa.io/en/stable/):

`$ python -m pip install colony-cli`

Or if you want to install it for your user:

`$ python -m pip install --user colony-cli`

### Configuration

In order to allow the CLI tool to authenticate with Colony you must provide several parameters:
* *Token* The easiest way to generate a token is via the Colony UI. Navigate to *Settings (in your space) -> Integrations ->
click “Connect” under any of the CI tools -> click “New Token”* to get an API token.
* *Space* The space in the Colony to use which is mapped to the Git repo you are using
* *Account* (optional) providing the account name (appearing as the subdomain in your Colony URL,
e.g <https://YOURACCOUNT.cloudshellcolony.com>). This is not a mandatory value but will help generate easy links.

The *Token*, *Space* and *Account* parameters can be provided via special command line flags (*--token*, *--space*,  
and *--account* respectively) but can be conveniently placed in a config file relative to your user folder,
so they don't need to be provided each time.

Use credentials file, with profiles. Create an INI formatted file like this:

```bash
[default]
token = xxxyyyzzz
space = DemoSpace
# This is optional
account = MYACCOUNT

[user]
token = aaabbbccc
space = TestSpace
# This is optional
account = MYACCOUNT
```

Save the file relative to your home user directory ('~/.colony/config' on Mac and Linux or in '%UserProfile%\\.colony\\config' on Windows).
If you wish to place credentials file in a different location, you can specify that location via an environment
variable:

`$ export COLONY_CONFIG_PATH=/path/to/file`

The different parameters may also be provided as environment variables:

```bash
export COLONY_TOKEN = xxxzzzyyy
export COLONY_SPACE = demo_space
# Optional
export COLONY_ACCOUNT = MYACCOUNT
```


## Basic Usage

Colony CLI currently allows you to make two actions:

- Validate a Blueprint (using the `colony bp validate` command)
- Start a Sandbox (via `colony sb start`)

In order to get help run:

`$ colony --help`

It will give you detailed output with usage:

```bash
$ colony --help
Usage: colony [--space=<space>] [--token=<token>] [--account=<account>] [--profile=<profile>] [--help] [--debug]
              <command> [<args>...]

Options:
  -h --help             Show this screen.
  --version             Show current version
  --space=<space>       Use a specific Colony Space, this will override any default set in the config file
  --token=<token>       Use a specific token for authentication, this will override any default set in the
                        config file
  --account=<account>   [Optional] Your Colony account name. The account name is equal to your subdomain in
                        the Colony URL. e.g. <https://YOURACCOUNT.cloudshellcolony.com//>
  --profile=<profile>   Use a specific Profile section in the config file
                        You still can override config with --token/--space options.

Commands:
    bp, blueprint       validate colony Blueprints
    sb, sandbox         start a Sandbox, end a Sandbox, get a Sandbox status or list all Sandboxes
```

You can get additional help information for a particular command by specifying *--help* flag after command name, like:

```colony sb --help
    usage:
        colony (sb | sandbox) start <blueprint_name> [options]
        colony (sb | sandbox) status <sandbox_id>
        colony (sb | sandbox) end <sandbox_id>
        colony (sb | sandbox) list [--filter={all|my|auto}] [--show-ended] [--count=<N>]
        colony (sb | sandbox) [--help]

    options:
       -h --help                        Show this message
       -d, --duration <minutes>         The Sandbox will automatically de-provision at the end of the provided duration
       -n, --name <sandbox_name>        Provide a name for the Sandbox. If not set, the name will be generated
                                        automatically using the source branch (or local changes) and current time.

       -i, --inputs <input_params>      The Blueprints inputs can be provided as a comma-separated list of key=value
                                        pairs. For example: key1=value1, key2=value2.
                                        By default Colony CLI will try to take the default values for these inputs
                                        from the Blueprint definition yaml file.

       -a, --artifacts <artifacts>      A comma-separated list of artifacts per application. These are relative to the
                                        artifact repository root defined in Colony.
                                        Example: appName1=path1, appName2=path2.
                                        By default Colony CLI will try to take artifacts from Blueprint definition yaml
                                        file.

       -b, --branch <branch>            Run the Blueprint version from a remote Git branch. If not provided,
                                        the CLI will attempt to automatically detect the current working branch.
                                        The CLI will automatically run any local uncommitted or untracked changes in a
                                        temporary branch created for the validation or for the development Sandbox.

       -c, --commit <commitId>          Specify a specific Commit ID. This is used in order to run a Sandbox from a
                                        specific Blueprint historic version. If this parameter is used, the
                                        Branch parameter must also be specified.

       -w, --wait <timeout>             Set the timeout in minutes to wait for the sandbox to become active. If not set,
                                        the CLI will wait for a default timeout of 30 minutes until the sandbox is
                                        ready.
```

### Blueprint validation

* If you are currently inside a git-enabled folder containing your Blueprint, commit and push your latest changes and run (Colony CLI will automatically detect the current working branch):

    `$ colony bp validate MyBlueprint`


* If you want to validate a Blueprint from another branch you can specify _--branch_ argument or even check validation in a
specific point in time by setting _--commit_:

    `$ colony bp validate MyBlueprint --branch dev --commit fb88a5e3275q5d54697cff82a160a29885dfed24`

### Testing Local Changes

The Colony CLI can validate your Blueprints and test your Sandboxes even before you commit and push your code to a
remote branch. It does so by creating a temporary branch on the remote repository with your local staged and even
untracked changes which gets deleted automatically after the Sandbox is created or the Blueprint validation is
complete. The CLI will automatically detect if you have some local changes and use them unless you explicitly
set the --branch flag.

Please notice that in order to create a Sandbox from your local changes, the CLI must make sure they are
picked up by the Sandbox setup process before completing the action and deleting the temporary branch. This means
that when you launch a local Sandbox the CLI command will not return immediately. You'll also receive a warning
not to abort the wait as that might not give Colony enough time to pull your changes and the Sandbox may fail.
Feel free to launch the CLI command asynchronously or continue working in a new tab.

---
**NOTE**

If you are not it git-enabled folder of your Blueprint repo and haven't set --branch/--commit arguments tool will
validate Blueprint with name "MyBlueprint" from branch currently attached to your Colony space.

---

The result will indicate whether the Blueprint is valid. If there are ny issues, you will see them printed out as
a table describing each issue found.

**Example:**

```bash
$colony blueprint validate Jenkins -b master

ERROR - colony.commands - Validation failed
message                                                                      name
---------------------------------------------------------------------------  -------------------------------
Cloud account: AWS is not recognized as a valid cloud account in this space  Blueprint unknown cloud account
```

### Launching a Sandbox

* Similar to the previous command you can omit *--branch/--commit* arguments if you are in a git-enabled folder of your
  Blueprint repo:

    `$ colony sb start MyBlueprint`

* This will create a Sandbox from the specified Blueprint

* If you want to start a Sandbox from a Blueprint in a specific state, specify _--branch_ and _--commit_ arguments:

    `$ colony sb start MyBlueprint --branch dev --commit fb88a5e3275q5d54697cff82a160a29885dfed24`

* Additional optional options that you can provide here are:
  * `-d, --duration <minutes>` - you can specify duration for the Sandbox environment in minutes. Default is 120 minutes
  * `-n, --name <sandbox_name>` - the name of the Sandbox you want to create. By default the cli will generate a name using the Blueprint name, branch or local changes, and the current timestamp
  * `-i, --inputs <input_params>` - comma-separated list of input parameters for the Sandbox, For example:_"param1=val1, param2=val2_"
  * `-a, --artifacts <artifacts>` - comma-separated list of Sandbox artifacts, like: "_app1=path1, app2=path2_"
  * `-w, --wait <timeout>` - <timeout> is a number of minutes. If set, you Colony CLI will wait for the Sandbox to become active and lock your terminal.
---
**NOTE**

1. If you are not it git-enabled folder of your Blueprint repo and haven't set --branch/--commit arguments tool will
start a Sandbox using the Blueprint "MyBlueprint" from the branch currently attached to your Colony space.

2. If you omit artifacts and inputs options, you are inside a git enabled folder and the local is in sync with remote,
then Colony Cli will try to get default values for artifacts and inputs from the Blueprint YAML file.
---

Result of the command is a Sandbox ID.

**Example**:

```bash
colony sb start MyBlueprint --inputs "CS_COLONY_TOKEN=ABCD, IAM_ROLE=s3access-profile, BUCKET_NAME=abc"

ybufpamyok03c11
```

### Other functionality

You can also end a Colony Sandbox by using the "end" command and specifying its Id:

`$ colony sb end <sandbox> id`

To get the current status of a Sandbox status run:

`$ colony sb status <sandbox> id`

In order to list all Sandboxes in your space use the following command:

`$ colony sb list`

- By default this command will show only Sandboxes launched by the CLI user which are not in an ended status.
- You can include historic completed Sandboxes by setting `--show-ended` flag
- Default output length is 25. You can override with option `--count=N` where N < 1000
- You can also list Sandboxes created by other users or filter only automation Sandboxes by setting option
`--filter={all|my|auto}`. Default is `my`.

## Troubleshooting and Help

To troubleshoot what Colony CLI is doing you can add _--debug_ to get additional information.

For questions, bug reports or feature requests, please refer to the [Issue Tracker](https://github.com/QualiSystemsLab/colony-cli/issues).


## Contributing


All your contributions are welcomed and encouraged. We've compiled detailed information about:

* [Contributing](.github/contributing.md)


## License
[Apache License 2.0](https://github.com/QualiSystems/shellfoundry/blob/master/LICENSE)
