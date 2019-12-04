# QNAP-pushover
This project allows system notifications to be send to pushover. It runs in a docker container.

<img src="https://raw.githubusercontent.com/vincentcox/QNAP-pushover/master/notification.png" alt="notification" width="200px">

# Docker Hub Installation

From the command line:

    docker run -d --rm -e LOG_TYPE="0" -e TOKEN="XXXXXX" -e USER_KEY="YYYYYYYY" -v /etc/logs/event.log:/event.log mtlott/qnap-pushover qnap-pushover

Or from docker-compose:

    version: "2"

    services:
      pushover:
        container_name: qnap-pushover
        image: mtlott/qnap-pushover:latest
        restart: unless-stopped
        volumes:
          - /etc/logs/event.log:/event.log
          - /etc/logs/conn.log:/conn.log
          - /etc/logs/notice.log:/notice.log
        environment:
          - LOG_TYPE=0 
          - TOKEN=XXXXXX
          - USER_KEY=YYYYYYYY
          - POLL_INTERVAL=10

Adding the following line to the environment stanza will resend the last 10 messages

          - TESTING=True


# Local Installation

Log via SSH into your NAS (which has docker/Container station installed).

    cd /tmp
    wget https://github.com/vincentcox/QNAP-pushover/archive/master.zip 
    unzip master.zip
    cd QNAP-pushover-master/
    # (QNAP has no package manager...)

    docker build . -t qnap-pushover

    docker run -d --rm -e LOG_TYPE="0" -e TOKEN="XXXXXX" -e USER_KEY="YYYYYYYY" -v /etc/logs/event.log:/event.log --name "QNAP-Pushover" qnap-pushover

LOG_TYPE:
- -1: everything (not recommended)
- 0: warnings and errors
- 1: errors only
