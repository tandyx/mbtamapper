# syntax=docker/dockerfile:1

FROM python:3.12.5-bookworm

RUN apt-get update && \
    apt-get install -y nodejs npm tzdata
ENV TZ=America/New_York
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ >/etc/timezone

WORKDIR /app
ENV PYTHONPATH="${PYTHONPATH}:/app/app"
RUN pip3 install --upgrade pip
COPY requirements.txt requirements.txt
RUN pip3 install --upgrade -r requirements.txt

COPY app app
RUN cd app/static && npm install
CMD ["python3", "-m", "waitress", "--listen=*:80", "--threads=50", "--call", "app.app:create_main_app"]
