from colony.branch.branch_utils import (
    count_stashed_items,
    create_temp_branch_and_stash_if_needed,
    delete_temp_local_branch,
    delete_temp_remote_branch,
    get_blueprint_working_branch,
    revert_from_local_temp_branch,
)
from colony.utils import BlueprintRepo


class ContextBranch(object):
    def __init__(self, repo: BlueprintRepo, branch: str):
        self.working_branch = None
        self.temp_working_branch = None
        self.repo = repo
        self.branch = branch
        self.temp_branch_exists = False
        self.temp_branch_reverted = False

    def __enter__(self):

        items_in_stack_before_temp_branch_check = count_stashed_items(self.repo)

        if self.branch:
            self.working_branch = self.branch
        else:
            self.working_branch = get_blueprint_working_branch(self.repo)
            self.temp_working_branch = create_temp_branch_and_stash_if_needed(self.repo, self.working_branch)
            if self.temp_working_branch is None:
                return None
            else:
                self.temp_branch_exists = True

        self.stashed_flag = items_in_stack_before_temp_branch_check < count_stashed_items(self.repo)
        self.temp_branch_exists = bool(self.temp_working_branch)
        self.validation_branch = self.temp_working_branch or self.working_branch

        return self

    def __exit__(self, type, value, traceback):
        if self.temp_branch_exists:
            self.delete_temp_branch()

    def delete_temp_branch(self) -> None:
        if not self.temp_branch_reverted:
            self.revert_from_local_temp_branch()

        if self.temp_branch_exists:
            delete_temp_local_branch(self.repo, self.temp_working_branch)
            delete_temp_remote_branch(self.repo, self.temp_working_branch)
            self.temp_branch_exists = False

    def revert_from_local_temp_branch(self) -> None:
        if not self.temp_branch_reverted:
            revert_from_local_temp_branch(self.repo, self.working_branch, self.stashed_flag)
        self.temp_branch_reverted = True
