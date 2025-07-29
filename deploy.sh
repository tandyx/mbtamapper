#!/bin/bash

# tfw ur too lazy to figure out docker on oracle's stupid server

# specifically tailored for ubuntu server

if [ "$EUID" -ne 0 ]; then
    echo "Please run as root"
    exit
fi

DOMAIN="mbtamapper.com"
SITES_CONF="/etc/nginx/sites-available/mbtamapper"

git pull

apt-get update && apt-get upgrade -y
apt-get install git tmux python3-venv letsencrypt tzdata npm nginx psmisc python3-certbot-nginx python3-pip python3-dev build-essential libssl-dev libffi-dev python3-setuptools -y

iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
netfilter-persistent save

python3 -m venv .venv
source .venv/bin/activate
pip3 install --upgrade -r requirements.txt

TZ=America/New_York
ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# sudo letsencrypt certonly -a webroot --webroot-path=/var/www/$DOMAIN/html/ -d $DOMAIN -d www.$DOMAIN
cat .env.nginx.conf > $SITES_CONF
sudo ln -s $SITES_CONF /etc/nginx/sites-enabled

cd static && npm install && cd ..

sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN

# restart processes
sudo pkill .venv -f
sudo fuser -k 80/tcp
sudo fuser -k 443/tcp
sudo systemctl restart nginx

echo "starting mbtamapper!"

sudo .venv/bin/python3 -m waitress --port=5000 --threads=50 --url-scheme=https --call app:create_main_app &
wait
