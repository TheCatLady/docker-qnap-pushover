import sqlite3, os.path, time, os
from pushover import init, Client
DB_NAME = ["NASLOG_EVENT", "NASLOG_CONN", "NASLOG_NOTICE"]
DB_FILENAME = ["event.log", "conn.log", "notice.log"]
event_id=["event_id", "conn_id", "id"]
try:
    LOG_TYPE = int(os.environ['LOG_TYPE'])
except:
    LOG_TYPE = 0 # -1 for all; 0 for error and warning, 1 for error
try:
    POLL_INTERVAL = int(os.environ['POLL_INTERVAL'])
except:
    POLL_INTERVAL = 10
try:
    TESTING = bool(os.environ['TESTING'])
except:
    TESTING = False
try:
    TOKEN = os.environ['TOKEN']
    USER_KEY = os.environ['USER_KEY']
except:
    print("Tokens need to be set via the docker environment.")


CURRENT_EVENT_ID = [0, 0, 0] # Init value
LATEST_EVENT_ID = [0, 0, 0] # Init value

init(TOKEN) # Init Pushover
Client(USER_KEY).send_message("Starting QNAP Pushover Server...")

log = [None, None, None]
conn = [None, None, None]

for k in range(0,2):
    if os.path.isfile(DB_FILENAME[k]):
        log[k] = os.path.join(os.path.curdir, DB_FILENAME[k]) # The event_log needs to be mapped via docker: -v /etc/logs/event.log:event.log
        conn[k] = sqlite3.connect(log[k]) # The event.log is not a log file, it's a SQL3lite database. QNAP and their logic...
        # At beginning program get the latest event_id. We don't want pushover to sent the entire event.log DB to our phone. Only the events starting from now.
        cursor = conn[k].cursor()
        cursor.execute("SELECT * FROM "+DB_NAME[k]+" ORDER BY "+event_id[k]+" DESC LIMIT 1;")
        LATEST_EVENT_ID[k] = cursor.fetchone()[0]
        if (TESTING == True):
            LATEST_EVENT_ID[k] = LATEST_EVENT_ID[k] -10
    else:
        conn[k] = None

while True:
    for j in range(0,2):
        # Check for new event_id's
        if conn[j] is None:
            pass
        else:
            cursor = conn[j].cursor()
            cursor.execute("SELECT * FROM "+DB_NAME[j]+" ORDER BY "+event_id[k]+" DESC LIMIT 1;")
            CURRENT_EVENT_ID[j] = cursor.fetchone()[0]

            if (CURRENT_EVENT_ID[j] != LATEST_EVENT_ID[j]):
                print("New events detected on "+DB_NAME[j])
                New_event_count = CURRENT_EVENT_ID[j] - LATEST_EVENT_ID[j]
                # for testing:

                error = False
                for i in range(New_event_count):
                    # print(i)
                    cursor = conn[j].cursor()
                    cursor.execute(
                        "SELECT * FROM " + DB_NAME[j] + " where "+event_id[k]+"="+str(LATEST_EVENT_ID[j]-i)+";")
                    event = cursor.fetchone()
                    if event[1] > LOG_TYPE:
                        # print(event[7])
                        try:
                            Client(USER_KEY).send_message(event[2]+" - "+event[3]+": "+event[7], title="NAS notification")
                        except:
                            error= True
                if (error == True):
                    print("There was an error while sending the latest batch. Retrying next round.")
                    CURRENT_EVENT_ID[j] = LATEST_EVENT_ID[j]
                else:
                    LATEST_EVENT_ID[j] = CURRENT_EVENT_ID[j]
            else:
                print("No new events detected")

    time.sleep(POLL_INTERVAL)
