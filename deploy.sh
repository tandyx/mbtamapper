#!/bin/bash

# tfw ur too lazy to figure out docker on oracle's stupid server

# specifically tailored for ubuntu server

if [ "$EUID" -ne 0 ]; then
    echo "Please run as root"
    exit
fi

# git checkout master
git pull

apt-get update && apt-get upgrade -y
apt-get install git tmux python3-venv tzdata npm python3-pip python3-dev build-essential -y

iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
netfilter-persistent save

# python
python3 -m venv .venv
source .venv/bin/activate
pip3 install --upgrade -r requirements.txt

# npm
npm install
npm run bundle

TZ=America/New_York
ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# restart processes
sudo pkill .venv -f

echo "starting mbtamapper!"

sudo .venv/bin/python3 -m waitress --host=127.0.0.1 --port=5000 --threads=50 --call app:create_main_app &

sleep 5s

for item in "subway" "rapid_transit" "commuter_rail" "bus" "ferry"; do
    echo "starting cache for $item"
    curl "http://127.0.0.1:5000/$item/vehicles?include=route,next_stop,stop_time&cache=5" > /dev/null
done

wait
