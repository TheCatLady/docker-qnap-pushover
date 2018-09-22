# QNAP-pushover
This project allows notifications to be send to pushover. It runs in a docker container.

# Installation

Log via SSH into your NAS (which has docker/Container station installed).

    git clone https://github.com/vincentcox/QNAP-pushover.git

    cd QNAP-pushover

    docker build . -t QNAP-pushover

    docker run -d -rm -e LOG_TYPE="0" -e TOKEN="XXXXXX" -e USER_KEY="YYYYYYYY" -v /etc/logs/event.log:event.log --name "QNAP-Pushover"

LOG_TYPE:
- -1: everything (not recommended)
- 0: warnings and errors
- 1: errors only

# Support
This is smashed together, I won't provide active support for this repo. Only pull request will be reviewed.