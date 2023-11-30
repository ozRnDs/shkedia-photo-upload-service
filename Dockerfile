FROM python:3.11.6

RUN mkdir -p /usr/src

WORKDIR /usr/src

COPY requirements.txt ./

RUN pip install -r requirements.txt

COPY /src ./

ENTRYPOINT uvicorn main:app --host=0.0.0.0 --port=5000