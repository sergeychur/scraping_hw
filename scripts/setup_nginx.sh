#!/usr/bin/env bash

set -eu

if [[ $# != 1 ]]; then
    echo "Usage: $0 <path to local folder>"
    exit 1
fi

data_folder=/var/www/wiki_data/wiki
local_folder=$(realpath $1)

apt install nginx
mkdir -p $data_folder
tar xvf $local_folder/htmls.tar.gz -C $data_folder
rm /etc/nginx/sites-available/* /etc/nginx/sites-enabled/*
cp scripts/wiki_nginx.conf /etc/nginx/sites-available/
ln -s /etc/nginx/sites-available/wiki_nginx.conf /etc/nginx/sites-enabled/
systemctl restart nginx
systemctl status -l nginx
curl --head http://localhost/wiki/Чемпионат_Европы_по_футболу_2024.html

