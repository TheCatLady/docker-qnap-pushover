import sqlite3, os.path, time, os
from pushover import init, Client
DB_NAME = "NASLOG_EVENT"
try:
    LOG_TYPE = int(os.environ['LOG_TYPE'])
except:
    LOG_TYPE = 0 # -1 for all; 0 for error and warning, 1 for error
try:
    TESTING = bool(os.environ['TESTING'])
except:
    TESTING = False
try:
    TOKEN = os.environ['TOKEN']
    USER_KEY = os.environ['USER_KEY']
except:
    print("Tokens need to be set via the docker environment.")


CURRENT_EVENT_ID = 0 # Init value
LATEST_EVENT_ID = 0 # Init value

init(TOKEN) # Init Pushover
Client(USER_KEY).send_message("Starting QNAP Pushover Server...")
event_log = os.path.join(os.path.curdir, 'event.log') # The event_log needs to be mapped via docker: -v /etc/logs/event.log:event.log

conn = sqlite3.connect(event_log) # The event.log is not a log file, it's a SQL3lite database. QNAP and their logic...


# At beginning program get the latest event_id. We don't want pushover to sent the entire event.log DB to our phone. Only the events starting from now.
cursor = conn.cursor()
cursor.execute("SELECT * FROM "+DB_NAME+" ORDER BY event_id DESC LIMIT 1;")
LATEST_EVENT_ID = cursor.fetchone()[0]

if (TESTING == True):
    LATEST_EVENT_ID = LATEST_EVENT_ID -10

while True:
    # Check for new event_id's
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM "+DB_NAME+" ORDER BY event_id DESC LIMIT 1;")
    CURRENT_EVENT_ID = cursor.fetchone()[0]

    if (CURRENT_EVENT_ID != LATEST_EVENT_ID):
        print("New events detected")
        New_event_count = CURRENT_EVENT_ID - LATEST_EVENT_ID
        # for testing:

        error = False
        for i in range(New_event_count):
            # print(i)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM " + DB_NAME + " where event_id="+str(LATEST_EVENT_ID-i)+";")
            event = cursor.fetchone()
            if event[1] > LOG_TYPE:
                # print(event[7])
                try:
                    Client(USER_KEY).send_message(event[2]+" - "+event[3]+": "+event[7], title="NAS notification")
                except:
                    error= True
        if (error == True):
            print("There was an error while sending the latest batch. Retrying next round.")
            CURRENT_EVENT_ID = LATEST_EVENT_ID
        else:
            LATEST_EVENT_ID = CURRENT_EVENT_ID
    else:
        print("No new events detected")

    time.sleep(10)
