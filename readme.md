# What is mon.py?

Sometimes you have lots of applications, each writing into it's own log file, and you do not want to waste your time browsing through each of them to see if some critical problems occur. But you want to know it there are any and you want to know the same moment they hit. You might be unable to implement email sending logic into existing applications.

Mon.py is the kind of tool for dealing with these sort of cases.

- Monitors given log files, detects important messages by user-defined patterns
- Notifies by email
- Groups email messages, prevents flooding
- Supports multi-line messages
- Lets you keep an eye on critical errors and exceptions that happen in your applications

## Files

      mon.py          - this one should be executed
      config.ini      - configuration file (not required, overrides default values)
      rules.txt       - message detection rules setup
      sources         - here you need to define your log files
      
## Exampes
### Tracking the production errors of an YII2 application (PHP)

rules.txt:

    {
        'basic': {
                    # Equal messages that appear within this time interval will be grouped (in seconds)
                    'min_group_time': 300,
                    
                    # Grouped message will be sent if there is no other messages within this time interval (in seconds)
                    'silent_interval': 30,

                    # Whom to notify
                    'notify': ['developer@mail.domain'],

                    # Delimiter means regex that detects the end of multi line log entry (default is newline, when dealing with single line entries only)
                    'delimiter': "   \t",

                    # Events that trigger this rule
                    'events': [
                        {
                            # The regexp to match the message
                            'pattern': '\[error\]',
                            
                            # Don't need to know of all there requests that trigger 404 Not Found exceptions
                            'exclude_pattern': 'HttpException',

                            # Date pattern helps us group the same messages that only differ by date string that is coming together with them
                            'date_pattern': '^\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2} '
                        }
                    ]
                }
    }
    
sources.txt:

    [
        {
            # The file name to tail
            'filename': '/opt/sites/my.site.com/www/runtime/logs/app.log',

            # This overrides the rules settings
            'silent_interval': 30,

            # This adds notice to the email title
            'notice': 'My App Error',

            # Rules to apply to this source
            'common_rules': ['basic']
        }
    ]

## Usage

One of the best options is to launch mon.py under the supervisor process control system (http://supervisord.org/).

