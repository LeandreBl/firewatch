from pyfirewatch import PyFireWatch, PyFireWatchEntry, PyFireWatchEvent
import os
import logging
import sys
import argparse
import re

def invalid_config_syntax(config: str) -> None:
    print(f"Invalid syntax for config argument \"{config}\": config pattern should look like \"<dirpath>,[<event1>, ...], <command>\", where the possible events are \"CREATED\", \"MODIFIED\", \"DELETED\", example: \"/tmp,[CREATED,MODIFIED],echo newfile at %r\"", file=sys.stderr)
    exit(1)    

CONFIG_REGEX = r'^(.+)\s*,\s*\[([A-Za-z, ]+)\]\s*,\s*(.+)$'

def unpack_watcher_config(config: str) -> (str, list[PyFireWatchEvent], str):
    stripped_config: str = config.strip()
    parsed_config = re.search(CONFIG_REGEX, stripped_config)
    if parsed_config == None:
        invalid_config_syntax(config)
    matches: list[str] = parsed_config.groups()
    directory: str = matches[0]
    command: str = matches[2]
    splited_events: list[str] = matches[1].split(',')
    events: list[PyFireWatchEvent] = []
    for event in splited_events:
        pyevent = PyFireWatchEvent.fromString(event)
        if pyevent == None:
            print(f"Error: {event} in config \"{config}\" is not a valid event", file=sys.stderr)
            invalid_config_syntax(config)
        if pyevent not in events:
            events.append(pyevent)
    return directory, events, command

def main(argv: list[str]):
    LOG_FORMAT: str = '[%(levelname)-8s] [%(asctime)s] [%(filename)s:%(lineno)d] -- %(message)s'

    parser = argparse.ArgumentParser(prog='PyFireWatch', description='A Python inotify daemon to run commands based on filesystem events')

    parser.add_argument('-l', '--logfile', type=str, default="logs/PyFireWatch.log", required=False, help="The filepath that the daemon will use to log it's activity")
    parser.add_argument('-d', '--dumpfile', type=str, default="logs/PyFireWatch_subcommands_dump.log", required=False, help="The filepath that the commands executed by the daemon will log into")
    parser.add_argument('watches', type=str, help="Watch patterns such as \"<dirpath>,[<event1>, ...], <command>\", where the possible events are \"CREATED\", \"MODIFIED\", \"DELETED\", example: \"/tmp,[CREATED,MODIFIED],echo newfile at %r\"", nargs='+')
    parser.add_argument('-v', '--verbose', action='store_true', help="Turn on the debug logs of the prorgam", default=False)

    args = parser.parse_args(argv[1:])

    logfile: str = os.path.realpath(args.logfile)
    logdir: str = os.path.dirname(logfile)
    if not os.path.exists(logdir):
        os.makedirs(logdir)

    logging.basicConfig(
        format=LOG_FORMAT,
        level=logging.DEBUG if args.verbose else logging.INFO,
        handlers=[
            logging.FileHandler(logfile, 'a'),
            logging.StreamHandler()
        ],
    )

    watches: dict[str, PyFireWatchEntry] = {}

    for watch in args.watches:
        directory, events, command = unpack_watcher_config(watch)
        watches[directory] = PyFireWatchEntry(events, command)

    watcher = PyFireWatch(towatch=watches, subcommand_dumpfile=args.dumpfile)

    watcher.run()
    pass

if __name__ == '__main__':
    exit(main(sys.argv))
