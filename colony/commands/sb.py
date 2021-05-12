import datetime
import time

import tabulate
from docopt import DocoptExit
from yaspin import yaspin

from colony.branch.branch_context import ContextBranch
from colony.branch.branch_utils import (
    can_temp_branch_be_deleted,
    get_and_check_folder_based_repo,
    is_k8s_blueprint,
    logger,
    sandbox_start_wait_output,
)
from colony.commands.base import BaseCommand
from colony.constants import FINAL_SB_STATUSES, TIMEOUT
from colony.sandboxes import SandboxesManager
from colony.utils import BlueprintRepo, parse_comma_separated_string


class SandboxesCommand(BaseCommand):
    """
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
                                        By default Colony CLI will try to take artifacts from blueprint definition yaml
                                        file.

       -b, --branch <branch>            Run the Blueprint version from a remote Git branch. If not provided,
                                        the CLI will attempt to automatically detect the current working branch.
                                        The CLI will automatically run any local uncommitted or untracked changes in a
                                        temporary branch created for the validation or for the development Sandbox.

       -c, --commit <commitId>          Specify a specific Commit ID. This is used in order to run a Sandbox from a
                                        specific Blueprint historic version. If this parameter is used, the
                                        Branch parameter must also be specified.

       -t, --timeout <timeout>          Set the timeout in minutes to wait for the sandbox to become active. If not set,
                                        the CLI will wait for a default timeout of 30 minutes until the sandbox is
                                        ready.

       -w, --wait                       Wait for sandbox to finish launching process.


    """

    RESOURCE_MANAGER = SandboxesManager

    def get_actions_table(self) -> dict:
        return {"status": self.do_status, "start": self.do_start, "end": self.do_end, "list": self.do_list}

    def do_list(self):
        list_filter = self.args["--filter"] or "my"
        if list_filter not in ["my", "all", "auto"]:
            raise DocoptExit("--filter value must be in [my, all, auto]")

        show_ended = self.args["--show-ended"]
        count = self.args.get("--count", 25)

        try:
            sandbox_list = self.manager.list(filter_opt=list_filter, count=count)
        except Exception as e:
            logger.exception(e, exc_info=False)
            return self.die()

        result_table = []
        for sb in sandbox_list:

            if sb.sandbox_status == "Ended" and not show_ended:
                continue

            result_table.append(
                {
                    "Sandbox ID": sb.sandbox_id,
                    "Sandbox Name": sb.name,
                    "Blueprint Name": sb.blueprint_name,
                    "Status": sb.sandbox_status,
                }
            )

        self.message(tabulate.tabulate(result_table, headers="keys"))

    def do_status(self):
        sandbox_id = self.args["<sandbox_id>"]
        try:
            sandbox = self.manager.get(sandbox_id)
        except Exception as e:
            logger.exception(e, exc_info=False)
            return self.die()

        status = getattr(sandbox, "sandbox_status")
        return self.success(status)

    def do_end(self):
        sandbox_id = self.args["<sandbox_id>"]
        try:
            self.manager.end(sandbox_id)
        except Exception as e:
            logger.exception(e, exc_info=False)
            return self.die()

        return self.success("End request has been sent")

    def do_start(self):
        branch_input = self.args.get("--branch")
        commit_input = self.args.get("--commit")
        if commit_input and branch_input is None:
            raise DocoptExit("Since commit is specified, branch is required")

        blueprint_name_input = self.args["<blueprint_name>"]
        sandbox_name_input = self.args["--name"]
        wait_input = self.args["--wait"]

        timeout_input = self.timeout_flag_validate(self.args["--timeout"])
        duration_input = self.duration_flag_validate(self.args["--duration"])

        inputs = parse_comma_separated_string(self.args["--inputs"])
        artifacts = parse_comma_separated_string(self.args["--artifacts"])

        repo = get_and_check_folder_based_repo(blueprint_name_input)

        self._update_missing_artifacts_and_inputs_with_default_values(artifacts, blueprint_name_input, inputs, repo)

        with ContextBranch(repo, branch_input) as context_branch:
            # TODO move error handling to exception catch
            if not context_branch:
                return self.error("Unable to start Sandbox")

            if sandbox_name_input is None:
                sandbox_name_input = self.generate_sandbox_name(
                    blueprint_name_input,
                    context_branch.temp_working_branch,
                    context_branch.working_branch,
                )

            try:
                sandbox_id = self.manager.start(
                    sandbox_name_input,
                    blueprint_name_input,
                    duration_input,
                    context_branch.validation_branch,
                    commit_input,
                    artifacts,
                    inputs,
                )
                BaseCommand.action_announcement("Starting sandbox")
                BaseCommand.important_value("Id: ", sandbox_id)
                BaseCommand.url(prefix_message="URL: ", message=self.manager.get_sandbox_ui_link(sandbox_id))

            except Exception as e:
                logger.exception(e, exc_info=False)
                return self.die()

            wait_timeout_reached = wait_for_sandbox_to_launch(
                self.manager,
                sandbox_id,
                repo,
                blueprint_name_input,
                timeout_input,
                context_branch,
                wait_input,
            )

            if wait_timeout_reached:
                return self.die()
            else:
                return self.success(sandbox_id)

    def _update_missing_artifacts_and_inputs_with_default_values(self, artifacts, blueprint_name, inputs, repo):
        # TODO(ddovbii): This obtaining default values magic must be refactored
        logger.debug("Trying to obtain default values for artifacts and inputs from local git blueprint repo")
        try:
            if not repo.is_current_branch_synced():
                logger.debug("Skipping obtaining values since local branch is not synced with remote")
            else:
                for art_name, art_path in repo.get_blueprint_artifacts(blueprint_name).items():
                    if art_name not in artifacts and art_path is not None:
                        logger.debug(f"Artifact `{art_name}` has been set with default path `{art_path}`")
                        artifacts[art_name] = art_path

                for input_name, input_value in repo.get_blueprint_default_inputs(blueprint_name).items():
                    if input_name not in inputs and input_value is not None:
                        logger.debug(f"Parameter `{input_name}` has been set with default value `{input_value}`")
                        inputs[input_name] = input_value

        except Exception as e:
            logger.debug(f"Unable to obtain default values. Details: {e}")
        return repo

    def generate_sandbox_name(self, blueprint_name: str, temp_working_branch: str, working_branch: str) -> str:
        suffix = datetime.datetime.now().strftime("%b%d-%H:%M:%S")
        branch_name_or_type = ""
        if working_branch:
            branch_name_or_type = working_branch + "-"
        if temp_working_branch:
            branch_name_or_type = "localchanges-"
        return f"{blueprint_name}-{branch_name_or_type}{suffix}"

    def duration_flag_validate(self, duration: str) -> int:
        try:
            duration = int(duration or 120)
            if duration <= 0:
                raise DocoptExit("Duration must be positive")

        except ValueError:
            raise DocoptExit("Duration must be a number")
        return duration

    def timeout_flag_validate(self, timeout: str) -> int:
        if timeout is not None:
            try:
                timeout = int(timeout)
            except ValueError:
                raise DocoptExit("Timeout must be a number")

            if timeout < 0:
                raise DocoptExit("Timeout must be positive")
        return timeout


def wait_for_sandbox_to_launch(
    sb_manager: SandboxesManager,
    sandbox_id: str,
    repo: BlueprintRepo,
    blueprint_name: str,
    timeout: int,
    context_branch: ContextBranch,
    wait_launch_end: str,
) -> bool:
    try:
        if context_branch.temp_branch_exists:
            context_branch.revert_from_local_temp_branch()

        if not timeout:
            timeout = TIMEOUT

        start_time = datetime.datetime.now()
        sandbox = sb_manager.get(sandbox_id)
        status = getattr(sandbox, "sandbox_status")
        k8s_blueprint = is_k8s_blueprint(blueprint_name, repo)

        sandbox_start_wait_output(sandbox_id, context_branch.temp_branch_exists)

        with yaspin(text="Starting...", color="yellow") as spinner:
            while (datetime.datetime.now() - start_time).seconds < timeout * 60:
                if status in FINAL_SB_STATUSES:
                    spinner.green.ok("✔")
                    break
                if context_branch.temp_branch_exists and can_temp_branch_be_deleted(sandbox, k8s_blueprint):
                    context_branch.delete_temp_branch()
                    if not wait_launch_end:
                        spinner.green.ok("✔")
                        break

                time.sleep(10)
                spinner.text = f"[{int((datetime.datetime.now() - start_time).total_seconds())} sec]"
                sandbox = sb_manager.get(sandbox_id)
                status = getattr(sandbox, "sandbox_status")
            else:
                logger.error(f"Timeout Reached - Sandbox {sandbox_id} was not active after {timeout} minutes")
                return True
        return False

    except Exception as e:
        logger.error(f"There was an issue with waiting for sandbox deployment -> {str(e)}")
