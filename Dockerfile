FROM        python:3.9.1-alpine3.13
COPY        requirements.txt /
RUN         pip install -r requirements.txt && \
            rm -f requirements.txt && \
            apk add --update --no-cache tini
COPY        main.py /
ENTRYPOINT  ["/sbin/tini", "--", "python", "-u", "/main.py"]
