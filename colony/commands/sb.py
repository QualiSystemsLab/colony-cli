import datetime
import logging
import os
import time

from docopt import DocoptExit

from colony.commands.base import BaseCommand
from colony.sandboxes import SandboxesManager
from colony.utils import BlueprintRepo, get_working_branch, parse_comma_separated_string

logger = logging.getLogger(__name__)


class SandboxesCommand(BaseCommand):
    """
    usage:
        colony (sb | sandbox) start <blueprint_name> [options]
        colony (sb | sandbox) status <sandbox_id>
        colony (sb | sandbox) end <sandbox_id>
        colony (sb | sandbox) [--help]

    options:
       -h --help                        Show this message
       -d, --duration <minutes>         Sandbox will automatically deprovision at the end of the provided duration
       -n, --name <sandbox_name>        Provide name of Sandbox. If not set, the name will be generated using timestamp

       -i, --inputs <input_params>      Comma separated list of input parameters. Example: key1=value1, key2=value2.
                                        By default Colony CLI will try to take default values for inputs from blueprint
                                        definition yaml file (if you are inside a git-enabled folder of blueprint repo).
                                        Use this option to override them.

       -a, --artifacts <artifacts>      Comma separated list of artifacts with paths where artifacts are defined per
                                        application. The artifact name is the name of the application.
                                        Example: appName1=path1, appName2=path2.
                                        By default Colony CLI will try to take artifacts from blueprint definition yaml
                                        file (if you are inside a git-enabled folder of blueprint repo).
                                        Use this option to override them.

       -b, --branch <branch>            Specify the name of remote git branch. If not provided, we will try to
                                        automatically detect the current working branch if the command is used in a
                                        git enabled folder.

       -c, --commit <commitId>          Specify commit ID. It's required to run sandbox from a blueprint from an
                                        historic commit. Must be used together with the branch option.
                                        If not specified then the latest commit will be used

       -w, --wait <timeout>             Set the timeout in minutes for the sandbox to become active. If not set, command
                                        will not block terminal and just return the ID of started sandbox
    """

    RESOURCE_MANAGER = SandboxesManager

    def get_actions_table(self) -> dict:
        return {"status": self.do_status, "start": self.do_start, "end": self.do_end}

    def do_status(self):
        sandbox_id = self.args["<sandbox_id>"]
        try:
            sandbox = self.manager.get(sandbox_id)
        except Exception as e:
            logger.exception(e, exc_info=False)
            sandbox = None
            self.die()

        status = getattr(sandbox, "sandbox_status")
        self.success(status)

    def do_end(self):
        sandbox_id = self.args["<sandbox_id>"]
        try:
            self.manager.end(sandbox_id)
        except Exception as e:
            logger.exception(e, exc_info=False)
            self.die()

        self.success("End request has been sent")

    def do_start(self):
        bp_name = self.args["<blueprint_name>"]
        branch = self.args.get("--branch")
        commit = self.args.get("--commit")
        name = self.args["--name"]
        timeout = self.args["--wait"]

        if timeout is not None:
            try:
                timeout = int(timeout)
            except ValueError:
                raise DocoptExit("Timeout must be a number")

            if timeout < 0:
                raise DocoptExit("Timeout must be positive")

        if name is None:
            suffix = datetime.datetime.now().strftime("%b%d%Y-%H:%M:%S")
            name = f"{bp_name}-{suffix}"

        try:
            duration = int(self.args["--duration"] or 120)
            if duration <= 0:
                raise DocoptExit("Duration must be positive")

        except ValueError:
            raise DocoptExit("Duration must be a number")

        if commit and branch is None:
            raise DocoptExit("Since commit is specified, branch is required")

        inputs = parse_comma_separated_string(self.args["--inputs"])
        artifacts = parse_comma_separated_string(self.args["--artifacts"])

        logger.debug("Trying to obtain default values for artifacts and inputs from local git blueprint repo")
        try:
            repo = BlueprintRepo(os.getcwd())
            if not repo.is_current_branch_synced():
                logger.debug("Skipping obtaining values since local branch is not synced with remote")
            else:
                for art_name, art_path in repo.get_blueprint_artifacts(bp_name).items():
                    if art_name not in artifacts and art_path is not None:
                        logger.debug(f"Artifact `{art_name}` has been set with default path `{art_path}`")
                        artifacts[art_name] = art_path

                for input_name, input_value in repo.get_blueprint_default_inputs(bp_name).items():
                    if input_name not in inputs and input_value is not None:
                        logger.debug(f"Parameter `{input_name}` has been set with default value `{input_value}`")
                        inputs[input_name] = input_value

        except Exception as e:
            logger.debug(f"Unable to recognize current directory as a blueprint repo. Details: {e}")

        if branch:
            working_branch = branch
        else:
            working_branch = get_working_branch()
            if working_branch:
                self.message(f"Automatically detected current working branch: {working_branch}")

        try:
            sandbox_id = self.manager.start(name, bp_name, duration, working_branch, commit, artifacts, inputs)

        except Exception as e:
            logger.exception(e, exc_info=False)
            sandbox_id = None
            self.die()

        if timeout is None:
            self.success(sandbox_id)

        else:
            start_time = datetime.datetime.now()

            logger.debug(f"Waiting for sandbox {sandbox_id}...")
            # Waiting loop
            while (datetime.datetime.now() - start_time).seconds < timeout * 60:
                sandbox = self.manager.get(sandbox_id)
                status = getattr(sandbox, "sandbox_status")
                if status == "Active":
                    self.success(sandbox_id)

                elif status == "Launching":
                    progress = getattr(sandbox, "launching_progress")
                    for check_points, properties in progress.items():
                        logger.debug(f"{check_points}: {properties['status']}")
                    time.sleep(30)

                else:
                    self.die(f"Sandbox {sandbox_id} started with {status} state")

            # timeout exceeded
            logger.error(f"Sandbox {sandbox_id} is not active after {timeout} minutes")
            self.die()
