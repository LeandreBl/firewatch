# PyFireWatch
A Python inotify daemon to run commands based on filesystem events

# Install
```sh
$ pip install .
```

## This command is supposed to be running as a daemon (Work in progress)

PyFireWatch is a simple tool, usable as an executable or a class to be notified upon creation, modification and deletion of files/directories

You can track directories/files like:
- `If anything is created (file / dir / fifo ...) inside the "ABC" directory: call "rm -rf %r", where % flags are replaced by an information based on the event context (here %r is the realpath of the file that was created)`

- `If anything is created or modified or deleted (file / dir / fifo ...) inside the "ABC" directory: call "echo $r $e >> ~/.events.log", where % flags are replaced by an information based on the event context (here %r is the realpath of the file that was created/modified or deleted and %e is the name of the event "CREATED", "MODIFIED", "DELETED")`

> Multiple watchers can be instanciated at once, see #Examples

> Multiple events can be registered on a single watcher, see #Examples

> Note that if you specify two different actions of the same directory, the next one will override the previous one

---

### Examples

```sh
$ python3 -m pyfirewatch "/tmp,[CREATED],rm -f %r"
```

Will watch the /tmp directory for any creation event, when a CREATED event is triggered, it will call the `rm -f %r` command where `%r` will be replaced by PyFireWatch by the realpath of the file that triggered the event.

---
```sh
$ python3 -m pyfirewatch "/tmp,[CREATED],rm -f %r" "/dev,[MODIFIED,DELETED],notify-send '%d' 'Device %f: %e'"
```

Will watch the /tmp directory like the upper example, but will also watch the /dev directory for MODIFIED and DELETED events, on which it will then call the `notify-send` command (desktop notification) stating the directory and the file that got modified/deleted

---

####  Here is a list of all the current `%` flags handled by PyFireWatch:
| printf like % flag | behavior |
|--------------------|----------|
|%r                  |Inserts the realpath of the file that triggered the event|
|%d                  |Inserts the dirname of the directory that contained the file that triggered the event|
|%f                  |Inserts the filename (basename) of the file that triggered the event|
|%e                  |Inserts the event (\"created\" | \"modified\" | \"deleted\")|
|%Y                  |Inserts the year when the event occured|
|%M                  |Inserts the month when the event occured|
|%D                  |Inserts the day when the event occured|
|%h                  |Inserts the hours when the event occured|
|%m                  |Inserts the minutes when the event occured|
|%s                  |Inserts the seconds when the event occured|
|%u                  |Inserts the microseconds when the event occured|
