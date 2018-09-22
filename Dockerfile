FROM python:3.6-alpine

ADD main.py /
ADD requirements.txt /

RUN pip install -r requirements.txt

CMD [ "python", "/main.py" ]