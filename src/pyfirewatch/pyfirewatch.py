import watchfiles
from enum import Enum
from collections.abc import Callable
import datetime
import os
import subprocess
from io import TextIOWrapper
import logging

class PyFireWatchEvent(Enum):
    CREATED = 1
    MODIFIED = 2
    DELETED = 3

    @staticmethod
    def fromString(event: str):
        NAME_MATRIX = {
            "CREATED": PyFireWatchEvent.CREATED,
            "MODIFIED": PyFireWatchEvent.MODIFIED,
            "DELETED": PyFireWatchEvent.DELETED,
        }
        event = event.upper()
        if event in NAME_MATRIX:
            return NAME_MATRIX[event]
        return None

    def __repr__(self) -> str:
        return self.name

class PyFireWatchFormatEntry:
    def __init__(self, help: str = "", callback: Callable[[datetime.datetime, str, str, PyFireWatchEvent], str] = lambda x: "") -> None:
        self.help = help
        self.callback = callback

class PyFireWatchCommand:
    def __init__(self, printf_formatted_command: str) -> None:
        self.command = printf_formatted_command

    def format(self, config: dict[str, PyFireWatchFormatEntry], realpath: str, event: PyFireWatchEvent):
        now: datetime.datetime = datetime.datetime.now()
        command: str = self.command

        for key, entry in config.items():
            command = command.replace(key, entry.callback(now, realpath, event))

        return command

def __format_realpath(now: datetime.datetime, realpath: str, event: PyFireWatchEvent):
    return realpath

def __format_directory(now: datetime.datetime, realpath: str, event: PyFireWatchEvent):
    return os.path.dirname(realpath)

def __format_filename(now: datetime.datetime, realpath: str, event: PyFireWatchEvent):
    return os.path.basename(realpath)

def __format_event(now: datetime.datetime, realpath: str, event: PyFireWatchEvent):
    return event.name.upper()

def __format_year(now: datetime.datetime, realpath: str, event: PyFireWatchEvent):
    return f"{now.year}"

def __format_month(now: datetime.datetime, realpath: str, event: PyFireWatchEvent):
    return f"{now.month}"

def __format_day(now: datetime.datetime, realpath: str, event: PyFireWatchEvent):
    return f"{now.day}"

def __format_hour(now: datetime.datetime, realpath: str, event: PyFireWatchEvent):
    return f"{now.hour}"

def __format_minute(now: datetime.datetime, realpath: str, event: PyFireWatchEvent):
    return f"{now.minute}"

def __format_seconds(now: datetime.datetime, realpath: str, event: PyFireWatchEvent):
    return f"{now.second}"

def __format_microseconds(now: datetime.datetime, realpath: str, event: PyFireWatchEvent):
    return f"{now.microsecond}"

DEFAULT_PRINTF_FORMAT_MATRIX = {
    "%r": PyFireWatchFormatEntry("Inserts the realpath of the file that triggered the event", __format_realpath),
    "%d": PyFireWatchFormatEntry("Inserts the dirname of the directory that contained the file that triggered the event", __format_directory),
    "%f": PyFireWatchFormatEntry("Inserts the filename (basename) of the file that triggered the event", __format_filename),
    "%e": PyFireWatchFormatEntry("Inserts the event (\"created\" | \"modified\" | \"deleted\")", __format_event),
    "%Y": PyFireWatchFormatEntry("Inserts the year when the event occured", __format_year),
    "%M": PyFireWatchFormatEntry("Inserts the month when the event occured", __format_month),
    "%D": PyFireWatchFormatEntry("Inserts the day when the event occured", __format_day),
    "%h": PyFireWatchFormatEntry("Inserts the hours when the event occured", __format_hour),
    "%m": PyFireWatchFormatEntry("Inserts the minutes when the event occured", __format_minute),
    "%s": PyFireWatchFormatEntry("Inserts the seconds when the event occured", __format_seconds),
    "%u": PyFireWatchFormatEntry("Inserts the microseconds when the event occured", __format_microseconds),
}

class PyFireWatchEntry:
    def __init__(self, events: list[PyFireWatchEvent], action: str) -> None:
        self.events = events
        self.action = PyFireWatchCommand(action)

    def execute(self, command: str, subcommand_dumpfile: TextIOWrapper):
        now: datetime.datetime = datetime.datetime.now()
        print(f'[{now.strftime("%Y-%m-%d %H:%M:%S")}] - `{command}`', file=subcommand_dumpfile, flush=True)
        process = subprocess.run(command, stderr=subcommand_dumpfile, stdout=subcommand_dumpfile, shell=True)
        print(f'[{now.strftime("%Y-%m-%d %H:%M:%S")}] - `{command}` finished with exit code: {process.returncode}', file=subcommand_dumpfile, flush=True)
        return process.returncode

class PyFireWatch:
    WATCHFILES_CHANGE_TO_PYFIREWATCH_EVENT = {
        watchfiles.Change.added: PyFireWatchEvent.CREATED,
        watchfiles.Change.modified: PyFireWatchEvent.MODIFIED,
        watchfiles.Change.deleted: PyFireWatchEvent.DELETED
    }
    def __init__(self, subcommand_dumpfile: str = "PyFireWatch_subcommands_dump.log", towatch: dict[str, PyFireWatchEntry] = {}) -> None:
        self.childrens_pids: list[int] = []
        self.subcommand_dumpfile = open(os.path.realpath(subcommand_dumpfile), 'a')
        self.to_watch: dict[str, PyFireWatchEntry] = {}
        for key, value in towatch.items():
            realpath: str = os.path.realpath(key)
            if not os.path.exists(realpath):
                os.makedirs(realpath)
            self.to_watch[realpath] = value
            logging.debug(f'Watching \"{realpath}\" for event{"s" if len(value.events) > 1 else ""} {value.events} with action \"{value.action.command}\"')

    def sub_process_execute(self, entry: PyFireWatchEntry, realpath: str, event: PyFireWatchEvent):
        pid = os.fork()
        command: str = entry.action.format(DEFAULT_PRINTF_FORMAT_MATRIX, realpath, event)
        logging.debug(f'Executing \"{command}\" on process {pid}')
        if pid == 0:
            exit_code = entry.execute(command, self.subcommand_dumpfile)
            exit(exit_code)
        else:
            self.childrens_pids.append(pid)
            pids: list[int] = self.childrens_pids
            for p in pids:
                try:
                    pid, status = os.waitpid(p, os.WNOHANG)
                    if pid == p:
                        self.childrens_pids.remove(p)
                        logging.debug(f'Process {pid} finished with exit code {os.WEXITSTATUS(status)}')
                except:
                    logging.error(f"Failed to waitpid, no child process {p}")
                    pass

    def run(self):
        for changes in watchfiles.watch(*self.to_watch.keys(), recursive=True, ignore_permission_denied=True):
            for event, filepath in changes:
                realpath: str = os.path.realpath(filepath)
                if realpath == self.subcommand_dumpfile.name:
                    continue
                dirname: str = os.path.dirname(filepath)
                for path, entry in self.to_watch.items():
                    if dirname.startswith(path):
                        pyfirewatch_event = self.WATCHFILES_CHANGE_TO_PYFIREWATCH_EVENT[event]
                        if pyfirewatch_event in entry.events:
                            self.sub_process_execute(entry, realpath, pyfirewatch_event)