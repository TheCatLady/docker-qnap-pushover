FROM        python:3.9.1-alpine3.12
COPY        requirements.txt /
RUN         pip install -r requirements.txt
COPY        main.py /
ENTRYPOINT  ["python", "-u", "/main.py"]
