# syntax=docker/dockerfile:1

FROM python:3.12.0-bookworm

RUN apt-get update && apt-get install -y nodejs npm

WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip3 install --upgrade pip
RUN pip3 install --upgrade -r requirements.txt
COPY . .

RUN apt-get install -y tzdata
ENV TZ=America/New_York
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ >/etc/timezone

CMD "./start.sh"
