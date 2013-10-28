# What is mon.py?

It is a simple log monitoring tool, written by Igor Askarov (juks@juks.ru)

- ☑ Tails given log files, detects important messages by user-defined patterns
- ☑ Notifies by email
- ☑ Groups email messages, prevents flooding

# Files

      mon.py          - this one should be executed
      config.ini      - configuration file (not required, overrides default values)
      rules.txt       - message detection rules setup
      sources         - here you need to define your log files

# Usage

One of the best options is to launch mon.py under the supervisor process control system (http://supervisord.org/).

