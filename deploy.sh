#!/bin/bash

# tfw ur too lazy to figure out docker on oracle's stupid server

# specifically tailored for ubuntu server

if [ "$EUID" -ne 0 ]; then
    echo "Please run as root"
    exit
fi

DOMAIN="mbtamapper.com"

git pull

sudo apt install software-properties-common
sudo add-apt-repository ppa:certbot/certbot
apt-get update && apt-get upgrade -y
apt-get git tmux python3-venv tzdata npm python3-certbot-nginx nginx psmisc -y

iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
netfilter-persistent save

python3 -m venv .venv
source .venv/bin/activate
pip3 install --upgrade -r requirements.txt

TZ=America/New_York
ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN
letsencrypt certonly -a webroot --webroot-path=/var/www/$DOMAIN/html/ -d $DOMAIN -d www.$DOMAIN
cat .env.nginx.conf > /etc/nginx/sites-available/default

cd static && npm install && cd ..

sudo pkill .venv -f

sudo fuser -k 80/tcp && sudo fuser -k 443/tcp &&
    echo "starting mbtamapper!"

sudo .venv/bin/python3 -m waitress --port=5000 --threads=50 --url-scheme=https --call app:create_main_app &
wait
