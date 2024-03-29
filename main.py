import logging
import os
import os.path
import pushover
import re
import sqlite3
import time

EVENT_LOG_PATH = "/event.log"
EVENT_ID_PATH = "/data/last_event_id.txt"
FONT_COLOR = ["grey", "#ffc311", "#ca414b"]
NOTIFY_LEVEL = {
    'error': 2,
    'warn': 1,
    'warning': 1,
    'info': 0,
    'information': 0
}
LOGGING_LEVEL = {
    'critical': logging.CRITICAL,
    'error': logging.ERROR,
    'warn': logging.WARNING,
    'warning': logging.WARNING,
    'info': logging.INFO,
    'information': logging.INFO,
    'debug': logging.DEBUG
}

# Banner
print('''
 _,         _,                     ,  |)    _        _  ,_
/ |  /|/|  / |  |/\_----|/\_|  |  / \_|/\  / \_|  |_|/ /  |
\/|_/ | |_/\/|_/|_/     |_/  \/|_/ \/ |  |/\_/  \/  |_/   |/
  |)           (|      (|
https://github.com/TheCatLady/docker-qnap-pushover
''')

logging_level = LOGGING_LEVEL.get(os.environ['LOG_LEVEL'].lower())

if logging_level is None:
    logging_level = logging.INFO

logging.basicConfig(format="%(levelname)s: %(message)s", level=logging_level)

NOTIFY_LEVEL_NAME = {value: key.upper() for key, value in NOTIFY_LEVEL.items()}

try:
    notify_levels = dict()
    
    for level in filter(str.strip, os.environ['NOTIFY_ONLY'].lower().split(',')):
        notify_levels[NOTIFY_LEVEL[level]] = NOTIFY_LEVEL_NAME[NOTIFY_LEVEL[level]]
except Exception:
    notify_levels.clear()
    logging.debug("NOTIFY_ONLY is not set.")

try:
    min_level = NOTIFY_LEVEL[os.environ['NOTIFY_LEVEL'].lower().strip()]
    if len(notify_levels) > 0:
        notify_levels.clear()
        logging.warning("Both NOTIFY_ONLY and NOTIFY_LEVEL are set. Ignoring NOTIFY_ONLY.")
except Exception:
    min_level = 1
finally:
    if len(notify_levels) == 0:
        for level in range(min_level, 3):
            notify_levels[level] = NOTIFY_LEVEL_NAME[level]

for level_name in notify_levels.values():
    logging.info(f"Sending notifications for {level_name} system log events.")

try:
    POLL_INTERVAL = int(os.environ['POLL_INTERVAL'])
except Exception:
    POLL_INTERVAL = 10
finally:
    logging.info(f"Polling for new system log events every {POLL_INTERVAL} seconds.")

try:
    INCLUDE = list(filter(str.strip, os.environ['INCLUDE'].lower().split(',')))
except Exception:
    INCLUDE = []
finally:
    if len(INCLUDE) > 0:
        logging.info(f"Only system log events containing the following keywords will trigger notifications: {', '.join(INCLUDE)}")
    else:
        logging.debug("INCLUDE keyword filter is not set.")

try:
    EXCLUDE = list(filter(str.strip, os.environ['EXCLUDE'].lower().split(',')))
except Exception:
    EXCLUDE = []
finally:
    if len(EXCLUDE) > 0:
        logging.info(f"System log events containing the following keywords will not trigger notifications: {', '.join(EXCLUDE)}")
    else:
        logging.debug("EXCLUDE keyword filter is not set.")

try:
    TESTING_MODE = bool(os.getenv('TESTING_MODE', 'false').lower().strip() in ['true', '1'])
except Exception:
    TESTING_MODE = False
finally:
    if TESTING_MODE:
        logging.warning("Testing mode is enabled. The last 10 system log events will be re-queued for processing on EVERY container start.")
    else:
        logging.debug("Testing mode is not enabled.")

try:
    PUSHOVER_TOKEN = os.environ['PUSHOVER_TOKEN'].strip()
    PUSHOVER_RECIPIENT = ''.join(os.environ['PUSHOVER_RECIPIENT'].split())
    pushover_client = pushover.Client(PUSHOVER_RECIPIENT, api_token=PUSHOVER_TOKEN)
    logging.info(f"Using Pushover application API token {PUSHOVER_TOKEN} and recipient user/group key(s) {PUSHOVER_RECIPIENT}.")

    if os.path.isfile(EVENT_LOG_PATH):
        db_conn = sqlite3.connect(EVENT_LOG_PATH) # event.log is not a text file, but a SQLite database

        try:
            with open(EVENT_ID_PATH, "r") as f:
                last_event_id = int(f.readline()) # read the last-processed event ID from a file if it exists
                logging.info(f"Read the last-processed event ID from the data file. ({last_event_id})")
        except (FileNotFoundError, ValueError):
            last_event_id = 0

        if last_event_id == 0: # set the last-processed event ID to the newest event ID if we weren't able to read it from a file
            cursor = db_conn.cursor()
            cursor.execute(f"SELECT event_id FROM NASLOG_EVENT ORDER BY event_id DESC LIMIT 1;")
            last_event_id = cursor.fetchone()[0]
            logging.info(f"Setting the last-processed event ID to the newest event ID in the database. ({last_event_id})")

        if TESTING_MODE:
            last_event_id -= 10 # for testing, re-queue the previous 10 events
            logging.info("Testing mode is enabled. Re-queuing last 10 system log events for processing.")
    else:
        raise Exception(f"Unable to open {EVENT_LOG_PATH}. Was the log file mounted to the container?")

    while True:
        cursor = db_conn.cursor()
        cursor.execute(f"SELECT event_id FROM NASLOG_EVENT ORDER BY event_id DESC LIMIT 1;")
        newest_event_id = cursor.fetchone()[0]

        if newest_event_id > last_event_id:
            new_event_count = newest_event_id - last_event_id
            logging.info(f"{new_event_count} new system log events detected in {EVENT_LOG_PATH}.")

            try:
                for i in range(new_event_count):
                    cursor = db_conn.cursor()
                    cursor.execute(f"SELECT event_type, event_desc, event_date, event_time, event_user, event_ip FROM NASLOG_EVENT WHERE event_id={last_event_id + 1 + i};")
                    event = cursor.fetchone()
                    event_type = event[0]
                    event_desc = event[1].strip()
                    event_datetime = f"{event[2]} {event[3]}"
                    event_user = event[4]
                    event_ip = event[5]

                    if event_type in notify_levels.keys():
                        hasIncluded = False
                        hasExcluded = False

                        if len(INCLUDE) == 0:
                            hasIncluded = True
                        else:
                            for keyword in INCLUDE:
                                if keyword in event_desc.lower():
                                    hasIncluded = True
                                    break

                        if hasIncluded == False:
                            logging.debug(f"Skipping system log event because it does not contain at least one INCLUDE keyword: {INCLUDE}")

                        for keyword in EXCLUDE:
                            if keyword in event_desc.lower():
                                hasExcluded = True
                                logging.debug(f"Skipping system log event because it contains an EXCLUDE keyword: {keyword}")
                                break

                        if hasIncluded and not hasExcluded:
                            if ']' in event_desc:
                                title = event_desc[1 : event_desc.find(']')]
                                message = event_desc[event_desc.find(']') + 2 :].rstrip(".,;")
                            else:
                                title = "System"
                                message = event_desc

                            if ". " in message:
                                first_line = True
                                prev = ""
                                quotes = 0

                                for s in message.split('. '):
                                    quotes += len(re.findall('"', s))

                                    if quotes % 2 == 0:
                                        if first_line:
                                            message = f"<font color=\"{FONT_COLOR[event_type]}\"><b>{prev}{s}</b></font><small>";
                                            first_line = False
                                        else:
                                            message += f"\n{prev}{s}"

                                        prev = ""
                                        quotes = 0
                                    else:
                                        prev += f"{s}. "
                            else:
                                message = f"<font color=\"{FONT_COLOR[event_type]}\"><b>{message}</b></font><small>"

                            message_details = ""

                            if event_user != "System":
                                message_details += f"<b>{event_user}</b><small>\nUser"

                            if event_ip != "127.0.0.1":
                                if message_details != "":
                                    message_details += "\n\n</small>"

                                message_details += f"<b>{event_ip}</b><small>\nSource IP"

                            if message_details != "":
                                message += f"\n\n{message_details}</small></small>"
                            else:
                                message += "</small>"

                            timestamp = int(time.mktime(time.strptime(event_datetime, "%Y-%m-%d %H:%M:%S")))
                            priority = event_type - 1

                            pushover_answer = pushover_client.send_message(message, html=1, priority=priority, timestamp=timestamp, title=title).answer
                            logging.debug(f"Pushover API response: {pushover_answer}")

                            if pushover_answer["status"] != 1:
                                time.sleep(5) # wait an extra 5 seconds
                                raise Exception("Unable to connect to Pushover API.")
                    else:
                        logging.debug(f"Skipping system log event because it is of type {NOTIFY_LEVEL_NAME[event_type]}.")

                last_event_id = newest_event_id
                logging.info(f"Successfully processed {new_event_count} system log events.")
            except pushover.RequestError as e:
                i += 1
                last_event_id += i
                logging.warning(f"Message rejected by Pushover API because {', '.join(e.errors)}. " \
                      f"Only {i} of {new_event_count} new system log events were processed successfully. " \
                      f"Skipping the current event and re-queuing the remaining {new_event_count - i} unprocessed events.")
            except Exception as e:
                last_event_id += i
                logging.warning(f"{e}. " \
                      f"Only {i} of {new_event_count} new system log events were processed successfully. " \
                      f"Re-queuing the remaining {new_event_count - i} unprocessed events.")
        else:
            logging.debug(f"No new system log events detected in {EVENT_LOG_PATH}.")

        with open(EVENT_ID_PATH, "w+") as f:
            f.write(str(last_event_id))
            f.truncate()
            logging.debug(f"Wrote the last-processed event ID to the data file. ({last_event_id})")

        time.sleep(POLL_INTERVAL)
except (pushover.InitError, pushover.UserError):
    logging.critical(f"Pushover application API token and recipient must be set.")
except Exception as e:
    logging.critical(f"{e}.")