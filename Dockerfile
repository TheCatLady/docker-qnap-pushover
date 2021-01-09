FROM python:3-alpine

ADD main.py /
ADD requirements.txt /

RUN pip install -r requirements.txt

ENTRYPOINT ["python", "-u", "/main.py"]
