FROM python:3

ADD main.py /
ADD requirements.txt /

RUN pip install -r requirements.txt

CMD [ "python", "./main.py" ]