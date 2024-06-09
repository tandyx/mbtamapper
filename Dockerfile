# syntax=docker/dockerfile:1

FROM python:3.12.3-bookworm

RUN apt-get update && apt-get install -y nodejs npm

WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip3 install --upgrade pip
RUN pip3 install --upgrade -r requirements.txt
COPY . .

RUN apt-get install -y tzdata
ENV TZ=America/New_York
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ >/etc/timezone

RUN cd static && npm install && cd ..
# python3 -m waitress --listen=*:80 --threads=50 --call main:create_default_app
CMD ["python3", "-m", "waitress", "--listen=*:80", "--threads=50", "--call", "app:create_main_app"]
