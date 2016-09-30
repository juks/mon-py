# What is mon.py?

Sometimes you have lots of applications, each writing into it's own log file, and you do not want to waste your time browsing through each of them to see if some critical problems occur. But you want to know it there are any and you want to know the same moment they hit. Mon.py is the kind of tool for dealing with these sort of cases.

- Tails given log files, detects important messages by user-defined patterns
- Notifies by email
- Groups email messages, prevents flooding

## Files

      mon.py          - this one should be executed
      config.ini      - configuration file (not required, overrides default values)
      rules.txt       - message detection rules setup
      sources         - here you need to define your log files

## Usage

One of the best options is to launch mon.py under the supervisor process control system (http://supervisord.org/).

