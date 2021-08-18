import datetime
import logging
import os
import time

import tabulate

from colony.branch_utils import (
    delete_temp_branch,
    figure_out_branches,
    revert_and_delete_temp_branch,
    revert_from_temp_branch,
    revert_wait_and_delete_temp_branch,
)
from colony.commands.base import BaseCommand
from colony.constants import UNCOMMITTED_BRANCH_NAME
from colony.parsers.command_input_validators import CommandInputValidator
from colony.sandboxes import SandboxesManager
from colony.utils import BlueprintRepo

logger = logging.getLogger(__name__)


class SandboxesCommand(BaseCommand):
    """
    usage:
        {command_name} (sb | sandbox) start <blueprint_name> [options]
        {command_name} (sb | sandbox) status <sandbox_id>
        {command_name} (sb | sandbox) end <sandbox_id>
        {command_name} (sb | sandbox) list [--filter={{all|my|auto}}] [--show-ended] [--count=<N>]
        {command_name} (sb | sandbox) [--help]

    options:
       -h --help                        Show this message
       -d, --duration <minutes>         The Sandbox will automatically de-provision at the end of the provided duration
       -n, --name <sandbox_name>        Provide a name for the Sandbox. If not set, the name will be generated
                                        automatically using the source branch (or local changes) and current time.

       -i, --inputs <input_params>      The Blueprints inputs can be provided as a comma-separated list of key=value
                                        pairs. For example: key1=value1, key2=value2.
                                        By default {product_name} CLI will try to take the default values for these inputs
                                        from the Blueprint definition yaml file.

       -a, --artifacts <artifacts>      A comma-separated list of artifacts per application. These are relative to the
                                        artifact repository root defined in {product_name}.
                                        Example: appName1=path1, appName2=path2.
                                        By default {product_name} CLI will try to take artifacts from blueprint definition yaml
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

    """

    RESOURCE_MANAGER = SandboxesManager

    def get_actions_table(self) -> dict:
        return {"status": self.do_status, "start": self.do_start, "end": self.do_end, "list": self.do_list}

    def do_list(self):
        list_filter = self.input_parser.sandbox_list.filter
        show_ended = self.input_parser.sandbox_list.show_ended
        count = self.input_parser.sandbox_list.count

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
        try:
            sandbox = self.manager.get(self.input_parser.sandbox_status.sandbox_id)
        except Exception as e:
            logger.exception(e, exc_info=False)
            return self.die()

        status = getattr(sandbox, "sandbox_status")
        return self.success(status)

    def do_end(self):
        try:
            self.manager.end(self.input_parser.sandbox_status.sandbox_id)
        except Exception as e:
            logger.exception(e, exc_info=False)
            return self.die()

        return self.success("End request has been sent")

    def do_start(self):
        # get commands inputs
        blueprint_name = self.input_parser.sandbox_start.blueprint_name
        branch = self.input_parser.sandbox_start.branch
        commit = self.input_parser.sandbox_start.commit
        name = self.input_parser.sandbox_start.sandbox_name
        timeout = self.input_parser.sandbox_start.timeout
        duration = self.input_parser.sandbox_start.duration
        inputs = self.input_parser.sandbox_start.inputs
        artifacts = self.input_parser.sandbox_start.artifacts

        CommandInputValidator.validate_commit_and_branch_specified(branch, commit)

        repo, working_branch, temp_working_branch, stashed_flag, success = figure_out_branches(branch, blueprint_name)

        if not success:
            return self.error("Unable to start Sandbox")

        # TODO(ddovbii): This obtaining default values magic must be refactored
        logger.debug("Trying to obtain default values for artifacts and inputs from local git blueprint repo")
        try:
            repo = BlueprintRepo(os.getcwd())
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

        branch_to_be_used = temp_working_branch or working_branch

        if name is None:
            suffix = datetime.datetime.now().strftime("%b%d-%H:%M:%S")
            branch_name_or_type = ""
            if working_branch:
                branch_name_or_type = working_branch + "-"
            if temp_working_branch:
                branch_name_or_type = "localchanges-"
            name = f"{blueprint_name}-{branch_name_or_type}{suffix}"

        try:
            sandbox_id = self.manager.start(
                name, blueprint_name, duration, branch_to_be_used, commit, artifacts, inputs
            )
            BaseCommand.action_announcement("Starting sandbox")
            BaseCommand.important_value("Id: ", sandbox_id)
            BaseCommand.url(prefix_message="URL: ", message=self.manager.get_sandbox_ui_link(sandbox_id))

        except Exception as e:
            logger.exception(e, exc_info=False)
            if temp_working_branch.startswith(UNCOMMITTED_BRANCH_NAME):
                revert_from_temp_branch(repo, working_branch, stashed_flag)
                delete_temp_branch(repo, temp_working_branch)
            return self.die()

        # todo: I think the below can be simplified and refactored
        if timeout is None:
            revert_wait_and_delete_temp_branch(
                self.manager, blueprint_name, repo, sandbox_id, stashed_flag, temp_working_branch, working_branch
            )
            return self.success("The Sandbox was created")

        else:
            start_time = datetime.datetime.now()

            logger.debug(f"Waiting for the Sandbox {sandbox_id} to start...")
            # Waiting loop
            while (datetime.datetime.now() - start_time).seconds < timeout * 60:
                sandbox = self.manager.get(sandbox_id)
                status = getattr(sandbox, "sandbox_status")
                if status == "Active":
                    revert_and_delete_temp_branch(repo, working_branch, temp_working_branch, stashed_flag)
                    return self.success(sandbox_id)

                elif status == "Launching":
                    progress = getattr(sandbox, "launching_progress")
                    for check_points, properties in progress.items():
                        logger.debug(f"{check_points}: {properties['status']}")
                    time.sleep(30)

                else:
                    revert_and_delete_temp_branch(repo, working_branch, temp_working_branch, stashed_flag)
                    return self.die(f"The Sandbox {sandbox_id} has started. Current state is: {status}")

            # timeout exceeded
            logger.error(f"Sandbox {sandbox_id} was not active after the provided timeout of {timeout} minutes")
            revert_and_delete_temp_branch(repo, working_branch, temp_working_branch, stashed_flag)
            return self.die()
