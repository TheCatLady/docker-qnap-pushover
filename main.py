import os
import os.path
import pushover
import sqlite3
import time

EVENT_ID_FILE = "last_event_id.txt"
DB_FILE = "event.log"
DB_NAME = "NASLOG_EVENT"
ID_COL = "event_id"
TYPE_COL = "event_type"
DESC_COL = "event_desc"
DATE_COL = "event_date"
TIME_COL = "event_time"
USER_COL = "event_user"
IP_COL = "event_ip"
COLOR = ["grey", "#ffc311", "#ca414b"]
INFO = f" - INFO: "
WARNING = f" - WARNING: "
ERROR = f" - ERROR: "

# Banner
print(''' _,         _,                     ,  |)    _        _  ,_
/ |  /|/|  / |  |/\_----|/\_|  |  / \_|/\  / \_|  |_|/ /  |
\/|_/ | |_/\/|_/|_/     |_/  \/|_/ \/ |  |/\_/  \/  |_/   |/
  |)           (|      (|
https://github.com/TheCatLady/docker-qnap-pushover
''')

try:
    if "info" in os.environ['LOG_LEVEL'].lower():
        LOG_TYPE = 0
    elif "warn" in os.environ['LOG_LEVEL'].lower():
        LOG_TYPE = 1
    else:
        LOG_TYPE = 2
except:
    LOG_TYPE = 1
finally:
    if LOG_TYPE == 0:
        print(f"{time.asctime()}{INFO}Log level is set to INFO. " \
              f"All system log events will trigger notifications.")
    elif LOG_TYPE == 1:
        print(f"{time.asctime()}{INFO}Log level is set to WARN. " \
              f"Only WARN and ERROR system log events will trigger notifications; INFO events will not trigger notifications.")
    else:
        print(f"{time.asctime()}{INFO}Log level is set to ERROR. " \
              f"ONLY ERROR system log events will not trigger notifications; INFO and WARN events will not trigger notifications.")

try:
    POLL_INTERVAL = int(os.environ['POLL_INTERVAL'])
except:
    POLL_INTERVAL = 10
finally:
    print(f"{time.asctime()}{INFO}Poll interval is set to {POLL_INTERVAL} seconds.")

try:
    INCLUDE = os.environ['INCLUDE'].strip(",").lower().split(',')
except:
    INCLUDE = []
finally:
    if len(INCLUDE) > 0:
        print(f"{time.asctime()}{INFO}Only system log events containing the following keywords will trigger notifications: {', '.join(INCLUDE)}")
    else:
        print(f"{time.asctime()}{INFO}INCLUDE environment was not set or is invalid.")

try:
    EXCLUDE = os.environ['EXCLUDE'].strip(",").lower().split(',')
except:
    EXCLUDE = []
finally:
    if len(EXCLUDE) > 0:
        print(f"{time.asctime()}{INFO}System log events containing the following keywords will not trigger notifications: {', '.join(EXCLUDE)}")
    else:
        print(f"{time.asctime()}{INFO}EXCLUDE environment was not set or is invalid.")

try:
    TESTING_MODE = bool(os.getenv('TESTING_MODE', 'false').lower() in ['true', '1'])
except:
    TESTING_MODE = False
finally:
    print(f"{time.asctime()}{WARNING}Testing mode is " \
          f"{'enabled. The last 10 system log events will be re-queued for processing on every container start' if TESTING_MODE else 'not enabled'}.")

try:
    PUSHOVER_TOKEN = os.environ['PUSHOVER_TOKEN']
    PUSHOVER_RECIPIENT = os.environ['PUSHOVER_RECIPIENT']
    pushover_client = pushover.Client(PUSHOVER_RECIPIENT, api_token=PUSHOVER_TOKEN)
    print(f"{time.asctime()}{INFO}Using Pushover application API token {PUSHOVER_TOKEN} and recipient user/group key(s) {PUSHOVER_RECIPIENT}.")

    log_path = os.path.abspath(DB_FILE)
    event_id_path = os.path.abspath(os.path.join("data", EVENT_ID_FILE))

    if os.path.isfile(log_path):
        db_conn = sqlite3.connect(log_path) # event.log is not a text file, but a SQLite database

        try:
            with open(event_id_path, "r") as f:
                last_event_id = int(f.readline()) # read the last-processed event ID from a file if it exists
                print(f"{time.asctime()}{INFO}Read the last-processed event ID from the data file. ({last_event_id})")
        except (FileNotFoundError, ValueError):
            last_event_id = 0

        if last_event_id == 0: # set the last-processed event ID to the newest event ID if we weren't able to read it from a file
            cursor = db_conn.cursor()
            cursor.execute(f"SELECT {ID_COL} FROM {DB_NAME} ORDER BY {ID_COL} DESC LIMIT 1;")
            last_event_id = cursor.fetchone()[0]
            print(f"{time.asctime()}{INFO}Setting the last-processed event ID to the newest event ID in the database. ({last_event_id})")

        if TESTING_MODE:
            last_event_id -= 10 # for testing, re-queue the previous 10 events
            print(f"{time.asctime()}{INFO}Testing mode is enabled. Re-queuing last 10 system log events for processing.")
    else:
        raise Exception(f"Unable to open {DB_FILE}. Was the log file mounted to the container?")

    while True:
        cursor = db_conn.cursor()
        cursor.execute(f"SELECT {ID_COL} FROM {DB_NAME} ORDER BY {ID_COL} DESC LIMIT 1;")
        newest_event_id = cursor.fetchone()[0]

        if newest_event_id > last_event_id:
            new_event_count = newest_event_id - last_event_id
            print(f"{time.asctime()}{INFO}{new_event_count} new system log events detected in {DB_FILE}.")

            try:
                for i in range(new_event_count):
                    cursor = db_conn.cursor()
                    cursor.execute(f"SELECT {TYPE_COL}, {DESC_COL}, {DATE_COL}, {TIME_COL}, {USER_COL}, {IP_COL} FROM {DB_NAME} WHERE {ID_COL}={last_event_id + 1 + i};")
                    event = cursor.fetchone()
                    event_type = event[0]
                    event_desc = event[1]
                    event_datetime = f"{event[2]} {event[3]}"
                    event_user = event[4]
                    event_ip = event[5]

                    if event_type >= LOG_TYPE:
                        hasIncluded = False
                        hasExcluded = False

                        for keyword in INCLUDE:
                            if keyword.strip() in event_desc.lower():
                                hasIncluded = True
                                break

                        if len(INCLUDE) == 0:
                            hasIncluded = True

                        for keyword in EXCLUDE:
                            if keyword.strip() in event_desc.lower():
                                hasExcluded = True
                                break

                        if hasIncluded and not hasExcluded:
                            if ']' in event_desc:
                                title = event_desc[1 : event_desc.find(']')]
                                message = event_desc[event_desc.find(']') + 2 :].rstrip(".,; ")
                            else:
                                title = "System"
                                message = event_desc

                            if ". " in message:
                                s = message.find(". ")
                                message_segments = message.split('. ')
                                message = f"<font color=\"{COLOR[event_type]}\"><b>{message[: s]}</b></font><small><br/>";
                                prev = ""
                                first_line = True

                                for s in message_segments:
                                    if prev != "":
                                        if '"' in s:
                                            if first_line:
                                                message = f"<font color=\"{COLOR[event_type]}\"><b>{prev}{s}</b></font><small><br/>";
                                                first_line = False
                                            else:
                                                message += f"{prev}{s}<br/>"
                                            prev = ""
                                        else:
                                            prev += s
                                    else:
                                        if '"' in s:
                                            prev = s
                                        else:
                                            if first_line:
                                                message = f"<font color=\"{COLOR[event_type]}\"><b>{prev}{s}</b></font><small><br/>";
                                                first_line = False
                                            else:
                                                message += f"{s}<br/>"

                                message += "&nbsp;\n"
                            else:
                                message = f"<font color=\"{COLOR[event_type]}\"><b>{message}</b></font><small><br/>&nbsp;\n"

                            if event_user != "System":
                                message += f"<b>{event_user}</b><small><br/>User<br/>&nbsp;\n</small>"

                            message += f"<b>{event_ip}</b><small><br/>Source IP</small></small>"
                            timestamp = int(time.mktime(time.strptime(event_datetime, "%Y-%m-%d %H:%M:%S")))
                            priority = event_type - 1

                            answer = pushover_client.send_message(message, html=1, priority=priority, timestamp=timestamp, title=title).answer

                            if answer["status"] != 1:
                                time.sleep(5) # wait an extra 5 seconds
                                raise Exception("Unable to connect to Pushover API.")

                last_event_id = newest_event_id
                print(f"{time.asctime()}{INFO}Successfully processed {new_event_count} system log events.")
            except pushover.RequestError as e:
                i += 1
                last_event_id += i
                print(f"{time.asctime()}{WARNING}Message rejected by Pushover API because {', '.join(e.errors)}. " \
                      f"Only {i} of {new_event_count} new system log events were processed successfully. " \
                      f"Skipping the current event and re-queuing the remaining {new_event_count - i} unprocessed events.")
            except Exception as e:
                last_event_id += i
                print(f"{time.asctime()}{WARNING}{e.strerror} " \
                      f"Only {i} of {new_event_count} new system log events were processed successfully. " \
                      f"Re-queuing the remaining {new_event_count - i} unprocessed events.")
        else:
            print(f"{time.asctime()}{INFO}No new system log events detected in {DB_FILE}.")

        with open(event_id_path, "w+") as f:
            f.write(str(last_event_id))
            f.truncate()
            print(f"{time.asctime()}{INFO}Wrote the last-processed event ID to the data file. ({last_event_id})")

        time.sleep(POLL_INTERVAL)
except (pushover.InitError, pushover.UserError):
    print(f"{time.asctime()}{ERROR}Pushover application API token and recipient must be set.")
except Exception as e:
    print(f"{time.asctime()}{ERROR}{e}")