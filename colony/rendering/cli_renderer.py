import re
import shutil
import sys
from abc import ABCMeta, abstractmethod
from os import system, name


class BaseRenderer(metaclass=ABCMeta):

    @abstractmethod
    def clear(self):
        pass

    @abstractmethod
    def get_terminal_size(self):
        pass

    @abstractmethod
    def render_new_line(self, text):
        pass

    @abstractmethod
    def render_to_current_line(self, text):
        pass

    @abstractmethod
    def get_stripped_string(self, text):
        pass

    @abstractmethod
    def restore_from_buffer(self):
        pass

    @abstractmethod
    def clear_current_line(self):
        pass


class CliRenderer(BaseRenderer):

    def __init__(self):
        self.remove_ansi_regex = re.compile(r'\x1b[^m]*m')
        self.buffer = []

    def get_stripped_string(self, text: str):
        return self.remove_ansi_regex.sub('', text)

    def clear(self):
        # for windows
        if name == 'nt':
            _ = system('cls')

            # for mac and linux(here, os.name is 'posix')
        else:
            _ = system('clear')

    def restore_from_buffer(self):
        for line in self.buffer:
            self.render_new_line(line)

    def get_terminal_size(self):
        return shutil.get_terminal_size((80, 24))

    def render_new_line(self, text: str, new_line: bool = True):
        if new_line:
            text = text + '\n'
        sys.stdout.write(text)
        self.buffer.append(text)

    def clear_current_line(self):
        if self.buffer:
            last_line = self.buffer[-1]
            self.render_to_current_line(f"{len(self.get_stripped_string(last_line)) * ' '}")
            self.buffer.pop()

    def render_to_current_line(self, text: str):
        sys.stdout.write(f"\r {text}")
        sys.stdout.flush()

        if self.buffer:
            self.buffer[-1] = text
        else:
            self.buffer.append(text)
