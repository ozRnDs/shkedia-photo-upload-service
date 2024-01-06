# FROM python:3.11.6
FROM python:3.11.6-slim

RUN mkdir -p /usr/src

WORKDIR /usr/src

COPY requirements.txt ./

COPY .autodevops/.build/pip.conf /root/.config/pip/
RUN pip install -r requirements.txt
RUN rm -rf /root/.config

COPY /src ./

ENTRYPOINT uvicorn main:app --host=0.0.0.0 --port=5000