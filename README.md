# `qnap-pushover` &#x1F514;

[![Image Size](https://img.shields.io/docker/image-size/thecatlady/qnap-pushover/latest?style=flat-square&logoColor=white&logo=docker&label=image%20size)](https://hub.docker.com/r/thecatlady/qnap-pushover)
[![Last Commit](https://img.shields.io/github/last-commit/TheCatLady/docker-qnap-pushover?style=flat-square&logoColor=white&logo=github)](https://github.com/TheCatLady/docker-qnap-pushover)
[![Build Status](https://img.shields.io/github/workflow/status/TheCatLady/docker-qnap-pushover/Build%20Docker%20Images?style=flat-square&logoColor=white&logo=github%20actions)](https://github.com/TheCatLady/docker-qnap-pushover)<br/>
[![Python](https://img.shields.io/github/languages/top/TheCatLady/docker-qnap-pushover?style=flat-square&logoColor=white&logo=python)](https://github.com/TheCatLady/docker-qnap-pushover)
[![Code Quality](https://img.shields.io/lgtm/grade/python/github/TheCatLady/docker-qnap-pushover?style=flat-square&logoColor=white&logo=lgtm&label=code%20quality)](https://lgtm.com/projects/g/TheCatLady/docker-qnap-pushover/)
[![License](https://img.shields.io/github/license/TheCatLady/docker-qnap-pushover?style=flat-square&logoColor=white&logo=open%20source%20initiative)](https://github.com/TheCatLady/docker-qnap-pushover/blob/main/LICENSE)<br/>
[![Become a GitHub Sponsor](https://img.shields.io/badge/github%20sponsors-become%20a%20sponsor-ff69b4?style=flat-square&logo=github%20sponsors)](https://github.com/sponsors/TheCatLady)
[![Donate via PayPal](https://img.shields.io/badge/paypal-make%20a%20donation-blue?style=flat-square&logo=paypal)](http://paypal.me/DHoung)

[Pushover](https://pushover.net/) notifications for [QNAP](https://www.qnap.com/) NAS system events

## Usage

Docker images are available from both [GitHub Container Registry (GHCR)](https://github.com/users/TheCatLady/packages/container/package/qnap-pushover) and [Docker Hub](https://hub.docker.com/r/thecatlady/qnap-pushover).

If you would prefer to pull from GHCR, simply replace `thecatlady/qnap-pushover` with `ghcr.io/thecatlady/qnap-pushover` in the examples below.

### Docker Compose (recommended)

Add the following volume and service definitions to a `docker-compose.yml` file:

```yaml
volumes:
  qnap-pushover:
services:
  qnap-pushover:
    image: thecatlady/qnap-pushover
    container_name: qnap-pushover
    environment:
      - LOG_LEVEL=WARN #optional
      - NOTIFY_LEVEL=WARN #optional
      - NOTIFY_ONLY= #optional
      - POLL_INTERVAL=10 #optional
      - INCLUDE= #optional
      - EXCLUDE= #optional
      - TESTING_MODE=false #optional
      - PUSHOVER_TOKEN=<Pushover application API token>
      - PUSHOVER_RECIPIENT=<Pushover user and/or group key(s)>
    volumes:
      - qnap-pushover:/data
      - /etc/logs/event.log:/event.log:ro
    restart: always
```

Then, run the following command from the directory containing your `docker-compose.yml` file:

```bash
docker-compose up -d
```

### Docker CLI

Run the following command to create the required named volume:

```bash
docker volume create qnap-pushover
```

Then, run the following command to create the container:

```bash
docker run -d \
  --name=qnap-pushover \
  -e LOG_LEVEL=WARN `#optional` \
  -e NOTIFY_LEVEL=WARN `#optional` \
  -e NOTIFY_ONLY= `#optional` \
  -e POLL_INTERVAL=10 `#optional` \
  -e INCLUDE= `#optional` \
  -e EXCLUDE= `#optional` \
  -e TESTING_MODE=false `#optional` \
  -e PUSHOVER_TOKEN=<Pushover application API token> \
  -e PUSHOVER_RECIPIENT=<Pushover user and/or group key(s)> \
  -v qnap-pushover:/data \
  -v /etc/logs/event.log:/event.log:ro \
  --restart always \
  thecatlady/qnap-pushover
```

## Updating

The process to update the container when a new image is available is dependent on how you set it up initially.

### Docker Compose

Run the following commands from the directory containing your `docker-compose.yml` file:

```bash
docker-compose pull qnap-pushover
docker-compose up -d
docker image prune
```

### Docker CLI

Run the commands below, followed by your original `docker run` command:

```bash
docker stop qnap-pushover
docker rm qnap-pushover
docker pull thecatlady/qnap-pushover
docker image prune
```

## Parameters

The container image is configured using the following parameters passed at runtime:

|Parameter|Function|Default Value|Required?|
|---|---|---|---|
|`-e LOG_LEVEL=`|Container logging level; `DEBUG` < `INFO` < `WARNING` < `ERROR` < `CRITICAL`|`WARNING`|no|
|`-e NOTIFY_LEVEL=`|Minimum system event type to generate a notification; `INFO` < `WARNING` < `ERROR`|`WARNING`|no|
|`-e NOTIFY_ONLY=`|Set of system event types for which to generate a notification (comma-delimited), e.g. `INFO,ERROR`<br/>(Value is ignored if `NOTIFY_LEVEL` is also set)||no|
|`-e POLL_INTERVAL=`|Poll interval in seconds|`10`|no|
|`-e INCLUDE=`|List of keywords which _must_ be present in the event description to trigger a notification (comma-delimited)||no|
|`-e EXCLUDE=`|List of keywords which _must not_ be present in the event description to trigger a notification (comma-delimited)||no|
|`-e TESTING_MODE=`|Testing mode (`true` or `false`); if set to `true`, will re-queue the last 10 system log events at _every_ container start and result in duplicate notifications|`false`|no|
|`-e PUSHOVER_TOKEN=`|[Pushover application API token](https://pushover.net/api#registration); e.g., `azGDORePK8gMaC0QOYAMyEEuzJnyUi`||**yes**|
|`-e PUSHOVER_RECIPIENT=`|[Pushover user and/or group key(s)](https://pushover.net/api#identifiers); e.g., `uQiRzpo4DXghDmr9QzzfQu27cmVRsG` or `gznej3rKEVAvPUxu9vvNnqpmZpokzF` (up to 50, comma-delimited)||**yes**|
|`-v qnap-pushover:/data`|Container data volume||**yes**|
|`-v /etc/logs/event.log:/event.log:ro`|QNAP event logs (mounted as read-only)||**yes**|
|`--restart`|Container [restart policy](https://docs.docker.com/engine/reference/run/#restart-policies---restart) (`always` or `unless-stopped` recommended)|`no`|no|

## Building Locally

If you would like to make modifications to the code, you can build the Docker image yourself instead of pulling the pre-built image available from [GitHub Container Registry (GHCR)](https://github.com/users/TheCatLady/packages/container/package/qnap-pushover) and [Docker Hub](https://hub.docker.com/r/thecatlady/qnap-pushover).

```bash
git clone https://github.com/TheCatLady/docker-qnap-pushover.git
cd docker-qnap-pushover
docker build --no-cache --pull -t thecatlady/qnap-pushover .
```

Once the image has been built, follow the directions in the "Usage" section above to start the container.

## How to Contribute

Show your support by starring this project! &#x1F31F;  Pull requests, bug reports, and feature requests are also welcome!

You can also support me by [becoming a GitHub sponsor](https://github.com/sponsors/TheCatLady) or [making a one-time PayPal donation](http://paypal.me/DHoung) &#x1F496;