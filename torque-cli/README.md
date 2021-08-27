# Torque CLI

---

![quali](../quali.png)

## Quali Torque CLI

Torque CLI is a Command Line interface tool for Quali Torque.

The main functionality this tool currently provides is validation of Torque Blueprints and launching of Sandbox environments from any branch in addition to testing local changes before committing them.

## Why use Torque CLI

When developing Blueprints for Torque, it can be very helpful to immediately check your work for errors.

Let's assume you are currently working in *development* branch, and you also have a main branch which is connected
to a Torque space. You would like to be sure that your latest local changes haven't broken anything before commiting to current branch and pushing to remote or before merging changes to main branch.

This is where this tool might be handy for you. Instead of reconnecting Torque to your development branch in the UI or going with "merge and pray" you can
use Torque CLI to validate your current Blueprints state and even launch Sandboxes.

## Installing

You can install Torque CLI with [pip](https://pip.pypa.io/en/stable/):

`$ python -m pip install torque-cli`

Or if you want to install it for your user:

`$ python -m pip install --user torque-cli`

### Configuration

In order to allow the CLI tool to authenticate with Torque you must provide several parameters:
* *Token* The easiest way to generate a token is via the Torque UI. Navigate to *Settings (in your space) -> Integrations ->
click “Connect” under any of the CI tools -> click “New Token”* to get an API token.
* *Space* The space in the Torque to use which is mapped to the Git repo you are using
* *Account* (optional) providing the account name (appearing as the subdomain in your Torque URL,
e.g <https://YOURACCOUNT.qtorque.io>). This is not a mandatory value but will help generate easy links.

The *Token*, *Space* and *Account* parameters can be provided via special command line flags (*--token*, *--space*,  
and *--account* respectively) but can be conveniently placed in a config file relative to your user folder,
so they don't need to be provided each time.

The config file can be easily created and managed using the interactive `torque configure` command.
The CLI supports multiple profiles and we recommend setting up a default profile for ease of use. To use a non-default profile the _--profile_ command line flag needs to be used to specify the profile name.

To add a new profile or update an existing one run ```torque configure set``` and follow the on-screen directions. First you will be able to choose the profile name. Hit enter to add/update the default profile or enter a custom profile name. If the profile exists it will be update and if it doesn't exist then a new profile will be configured.

To see all profiles run ```torque configure list``` and the command will output a table of all the profiles that are currently configured. Example output:
```bash
Profile Name    Torque Account    Space Name           Token
--------------  ----------------  -------------------  -------------
default         torque-demo       promotions-manager   *********jhtU
custom-profile  my-torque         my-space             *********igEw
```

If a profile is no longer needed it can be easily removed by running ```torque configure remove [profile-name]```

The `torque configure` command will save the config file relative to your home user directory ('~/.torque/config' on Mac and Linux or in '%UserProfile%\\.torque\\config' on Windows).
If you wish to place the config file in a different location, you can specify that location via an environment variable:

`$ export COLONY_CONFIG_PATH=/path/to/file`

The different parameters may also be provided as environment variables instead of using the config file:

```bash
export COLONY_TOKEN = xxxzzzyyy
export COLONY_SPACE = demo_space
# Optional
export COLONY_ACCOUNT = MYACCOUNT
```


## Basic Usage

Torque CLI currently allows you to make two actions:

- Validate a Blueprint (using the `torque bp validate` command)
- Start a Sandbox (via `torque sb start`)

In order to get help run:

`$ torque --help`

It will give you detailed output with usage:

```bash
$ torque --help
Usage: torque [--space=<space>] [--token=<token>] [--account=<account>] [--profile=<profile>] [--help] [--debug]
              <command> [<args>...]

Options:
  -h --help             Show this screen.
  --version             Show current version
  --space=<space>       Use a specific Torque Space, this will override any default set in the config file
  --token=<token>       Use a specific token for authentication, this will override any default set in the
                        config file
  --account=<account>   [Optional] Your Torque account name. The account name is equal to your subdomain in
                        the Torque URL. e.g. <https://YOURACCOUNT.qtorque.io//>
  --profile=<profile>   Use a specific Profile section in the config file
                        You still can override config with --token/--space options.

Commands:
    bp, blueprint       validate Torque Blueprints
    sb, sandbox         start a Sandbox, end a Sandbox, get a Sandbox status or list all Sandboxes
```

You can get additional help information for a particular command by specifying *--help* flag after command name, like:

```torque sb --help
    usage:
        torque (sb | sandbox) start <blueprint_name> [options]
        torque (sb | sandbox) status <sandbox_id>
        torque (sb | sandbox) end <sandbox_id>
        torque (sb | sandbox) list [--filter={all|my|auto}] [--show-ended] [--count=<N>]
        torque (sb | sandbox) [--help]

    options:
       -h --help                        Show this message
       -d, --duration <minutes>         The Sandbox will automatically de-provision at the end of the provided duration
       -n, --name <sandbox_name>        Provide a name for the Sandbox. If not set, the name will be generated
                                        automatically using the source branch (or local changes) and current time.

       -i, --inputs <input_params>      The Blueprints inputs can be provided as a comma-separated list of key=value
                                        pairs. For example: key1=value1, key2=value2.
                                        By default Torque CLI will try to take the default values for these inputs
                                        from the Blueprint definition yaml file.

       -a, --artifacts <artifacts>      A comma-separated list of artifacts per application. These are relative to the
                                        artifact repository root defined in Torque.
                                        Example: appName1=path1, appName2=path2.
                                        By default Torque CLI will try to take artifacts from Blueprint definition yaml
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

* If you are currently inside a git-enabled folder containing your Blueprint, commit and push your latest changes and run (Torque CLI will automatically detect the current working branch):

    `$ torque bp validate MyBlueprint`


* If you want to validate a Blueprint from another branch you can specify _--branch_ argument or even check validation in a
specific point in time by setting _--commit_:

    `$ torque bp validate MyBlueprint --branch dev --commit fb88a5e3275q5d54697cff82a160a29885dfed24`

### Testing Local Changes

The Torque CLI can validate your Blueprints and test your Sandboxes even before you commit and push your code to a
remote branch. It does so by creating a temporary branch on the remote repository with your local staged and even
untracked changes which gets deleted automatically after the Sandbox is created or the Blueprint validation is
complete. The CLI will automatically detect if you have some local changes and use them unless you explicitly
set the --branch flag.

Please notice that in order to create a Sandbox from your local changes, the CLI must make sure they are
picked up by the Sandbox setup process before completing the action and deleting the temporary branch. This means
that when you launch a local Sandbox the CLI command will not return immediately. You'll also receive a warning
not to abort the wait as that might not give Torque enough time to pull your changes and the Sandbox may fail.
Feel free to launch the CLI command asynchronously or continue working in a new tab.

---
**NOTE**

If you are not it git-enabled folder of your Blueprint repo and haven't set --branch/--commit arguments tool will
validate Blueprint with name "MyBlueprint" from branch currently attached to your Torque space.

---

The result will indicate whether the Blueprint is valid. If there are ny issues, you will see them printed out as
a table describing each issue found.

**Example:**

```bash
$torque blueprint validate Jenkins -b master

ERROR - torque.commands - Validation failed
message                                                                      name
---------------------------------------------------------------------------  -------------------------------
Cloud account: AWS is not recognized as a valid cloud account in this space  Blueprint unknown cloud account
```

### Launching a Sandbox

* Similar to the previous command you can omit *--branch/--commit* arguments if you are in a git-enabled folder of your
  Blueprint repo:

    `$ torque sb start MyBlueprint`

* This will create a Sandbox from the specified Blueprint

* If you want to start a Sandbox from a Blueprint in a specific state, specify _--branch_ and _--commit_ arguments:

    `$ torque sb start MyBlueprint --branch dev --commit fb88a5e3275q5d54697cff82a160a29885dfed24`

* Additional optional options that you can provide here are:
  * `-d, --duration <minutes>` - you can specify duration for the Sandbox environment in minutes. Default is 120 minutes
  * `-n, --name <sandbox_name>` - the name of the Sandbox you want to create. By default the cli will generate a name using the Blueprint name, branch or local changes, and the current timestamp
  * `-i, --inputs <input_params>` - comma-separated list of input parameters for the Sandbox, For example:_"param1=val1, param2=val2_"
  * `-a, --artifacts <artifacts>` - comma-separated list of Sandbox artifacts, like: "_app1=path1, app2=path2_"
  * `-w, --wait <timeout>` - <timeout> is a number of minutes. If set, you Torque CLI will wait for the Sandbox to become active and lock your terminal.
---
**NOTE**

1. If you are not it git-enabled folder of your Blueprint repo and haven't set --branch/--commit arguments tool will
start a Sandbox using the Blueprint "MyBlueprint" from the branch currently attached to your Torque space.

2. If you omit artifacts and inputs options, you are inside a git enabled folder and the local is in sync with remote,
then Torque Cli will try to get default values for artifacts and inputs from the Blueprint YAML file.
---

Result of the command is a Sandbox ID.

**Example**:

```bash
torque sb start MyBlueprint --inputs "CS_COLONY_TOKEN=ABCD, IAM_ROLE=s3access-profile, BUCKET_NAME=abc"

ybufpamyok03c11
```

### Other functionality

You can also end a Torque Sandbox by using the "end" command and specifying its Id:

`$ torque sb end <sandbox> id`

To get the current status of a Sandbox status run:

`$ torque sb status <sandbox> id`

In order to list all Sandboxes in your space use the following command:

`$ torque sb list`

- By default this command will show only Sandboxes launched by the CLI user which are not in an ended status.
- You can include historic completed Sandboxes by setting `--show-ended` flag
- Default output length is 25. You can override with option `--count=N` where N < 1000
- You can also list Sandboxes created by other users or filter only automation Sandboxes by setting option
`--filter={all|my|auto}`. Default is `my`.

## Troubleshooting and Help

To troubleshoot what Torque CLI is doing you can add _--debug_ to get additional information.

For questions, bug reports or feature requests, please refer to the [Issue Tracker](https://github.com/QualiNext/client-cli/issues).


## Contributing


All your contributions are welcomed and encouraged. We've compiled detailed information about:

* [Contributing](../.github/contributing.md)


## License
[Apache License 2.0](https://github.com/QualiSystems/shellfoundry/blob/master/LICENSE)
