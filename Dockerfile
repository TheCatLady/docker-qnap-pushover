FROM python:alpine

COPY requirements.txt /

RUN pip install -r requirements.txt

COPY main.py /

ENTRYPOINT ["python", "-u", "/main.py"]
