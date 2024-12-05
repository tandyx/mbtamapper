#!/bin/bash

# tfw ur too lazy to figure out docker on oracle's stupid server

# specifically tailored for ubuntu server

if [ "$EUID" -ne 0 ]; then
    echo "Please run as root"
    exit
fi

apt-get update && apt-get upgrade -y
apt-get git tmux python3-venv tzdata npm -y

iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
netfilter-persistent save

python3 -m venv .venv
source .venv/bin/activate
pip3 install --upgrade -r requirements.txt

TZ=America/New_York
ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

cd static && npm install && cd ..

.venv/bin/python3 -m waitress --listen=*:80 --threads=50 --call app:create_main_app &
wait
