#!/usr/bin/env python
#
# Simple log file monitoring tool. Copyright Igor Askarov (juks@juks.ru). See readme.md for more information
import time, os, re, smtplib, collections, ast
from copy import deepcopy
from email.mime.text import MIMEText

cb = collections.deque(maxlen=1000)
drop_mode_start_time = 0

d = {'run_folder': os.getcwd()}

defaults = {
    'max_messages_per_hour': 1000,                  # Drop message if it repeated for more than max_messages_per_hour times within one hour interval
    'mailer_path': '/usr/sbin/sendmail -t -i',      # Path to the mailer program with parameters
    'my_email': 'mon@localhost',                    # Email 'from' field
    'my_title': 'mon'
}

# Reading ini values
if os.path.exists(d['run_folder'] + '/setup.ini'):
    with open(d['run_folder'] + '/setup.ini') as of:
        values = of.readlines()

    for value in values:
        parts = value.rstrip().split('=', 1)
        if len(parts) == 2:
            d[parts[0]] = parts[1]

# Applying defaults
for default_index, default_name in enumerate(defaults):
    if default_name not in d:
        d[default_name] = defaults[default_name]

if os.path.exists(d['run_folder'] + '/rules.txt'):
    data = open(d['run_folder'] + '/rules.txt', 'r').read()
    common_rules = ast.literal_eval(data)
else:
    common_rules = {}

if os.path.exists(d['run_folder'] + '/sources.txt'):
    data = open(d['run_folder'] + '/sources.txt', 'r').read()
    sources = ast.literal_eval(data)
else:
    raise Exception('No sources.txt found')

# This sub sends emails
def send_mail(to, body, title):
    p = os.popen("%s -t" % d['mailer_path'], "w")
    msg = MIMEText(body.decode('utf-8'), _charset='utf-8')
    msg['To'] = to
    msg['From'] = d['my_email']
    msg['Subject'] = title
    p.write(msg.as_string())
    p.close()

# This sub decides how to send source message
def send(message, source_index=0, event_index=0):
    global sources, drop_mode_start_time, d

    cnt = sources[source_index]['events'][event_index]['appear_count']

    title = d['my_title']

    if cnt and cnt > 1:
        title = title + ' [' + str(cnt) + ']'
        message = '*' + str(cnt) + '* ' + message

    message = message + ' [' + sources[source_index]['filename'] + ']'
    sources[source_index]['last_notify_time'] = time.time()

    if 'notice' in sources[source_index]:
        title = title + ' (' + sources[source_index]['notice'] + ')'

    cb.append({'time': time.time(), 'message': message})
    count_per_hour = 0

    for stored_message in cb:
        if time.time() - stored_message['time'] <= 3600:
            count_per_hour += 1

    if count_per_hour > d['max_messages_per_hour']:
        if drop_mode_start_time:
            return
        else:
            drop_mode_start_time = time.time()
            message += "\n\n *** Maximum message flow capacity has reached. Some messages might get droppped ***"
    else:
        if drop_mode_start_time:
            message += "\n\n *** Message flow capacity is Ok. Back to normal operation ***"

        drop_mode_start_time = 0

    if sources[source_index]['notify']:
        for addr in sources[source_index]['notify']:
            send_mail(addr, message, title)
    else:
        print source_index + ' has no means of notification defined'

# This sub sends the grouped message ind resets the counter
def send_grouped(source_index, event_index):
    send(sources[source_index]['last_message'], source_index=source_index, event_index=event_index)

    sources[source_index]['events'][event_index]['appear_count'] = 0
    sources[source_index]['events'][event_index]['appear_time'] = 0

# Checks for the grouped messages to be ready for delivery
def process_grouped(force_send=False):
    global sources
    for source_index, source in enumerate(sources):
        for event_index, event in enumerate(source['events']):
            if event['appear_count']:
                if force_send or (not source['silent_interval'] or time.time() - source['last_notify_time'] >= source['silent_interval']):
                    send_grouped(source_index, event_index)

# Main thing
for source_index, source in enumerate(sources):
    if 'common_rules' in source:
        for rule in source['common_rules']:
            if rule in common_rules:
                tmp_source = deepcopy(common_rules[rule])
                sources[source_index].update(tmp_source)

    if 'events' not in sources[source_index]: sources[source_index]['events'] = []

    if 'file_handler' not in source:
        source['file_handler'] = False
        if 'silent_interval' not in source: sources[source_index]['silent_interval'] = 0
        sources[source_index]['last_notify_time'] = 0
        sources[source_index]['last_message'] = ''

        if 'min_group_time' not in source: source['min_group_time'] = 0

        for event_index, event in enumerate(sources[source_index]['events']):
            sources[source_index]['events'][event_index]['appear_time'] = 0
            sources[source_index]['events'][event_index]['appear_count'] = 0

    sources[source_index]['buffer'] = ''

tick = 0

while 1:
    for source_index, source in enumerate(sources):
        line = ''

        try:
            source['file_handler'] = open(source['filename'], 'r')
        except IOError as e:
            continue

        stat = os.stat(source['filename'])

        if 'current_pos' not in source:
            source['file_handler'].seek(stat[6])
        elif stat[6] >= source['current_pos']:
            source['file_handler'].seek(source['current_pos'])
        else:
            source['current_pos'] = 0

        while 1:
            line = source['file_handler'].readline(4096)

            if not line:
                break

            if len(source['buffer']) + len(line) <= 4096:
                source['buffer'] += line
            else:
                print 'Reached source buffer size limit'

            if 'delimiter' not in source or re.compile(source['delimiter'], re.IGNORECASE).search(line):
                if 'events' in source:
                    for event_index, event in enumerate(source['events']):
                        if 'pattern' in event and re.compile(event['pattern'], re.IGNORECASE).search(source['buffer']):
                            unique_message = source['buffer']
                                
                            if 'date_pattern' in event and event['date_pattern']:
                                unique_message = re.sub(re.compile(event['date_pattern'], re.IGNORECASE), '', unique_message)
                                
                            if 'replace_pattern' in event and event['replace_pattern']:
                                source['buffer'] = re.sub(re.compile(event['replace_pattern'][0], re.IGNORECASE|re.MULTILINE|re.UNICODE|re.DOTALL), event['replace_pattern'][1], source['buffer'])

                            if source['min_group_time'] and source['last_message'] == unique_message and event['appear_time'] and time.time() - event['appear_time'] < source['min_group_time']:
                                event['appear_count'] += 1
                            else:
                                process_grouped(True)

                                source['last_message'] = unique_message
                                event['appear_time'] = time.time()

                                send(source['buffer'], source_index=source_index, event_index=event_index)

                source['buffer'] = ''

        source['current_pos'] = source['file_handler'].tell()
        source['file_handler'].close

        time.sleep(1)

    tick += 1

    if tick % 60 == 0:
        process_grouped()
        tick = 0;