#!/usr/bin/env bash

set -eu

data_folder=/var/www/wiki_data/wiki

apt install nginx
mkdir -p $data_folder
cp test_data/*.html $data_folder
rm /etc/nginx/sites-available/* /etc/nginx/sites-enabled/*
cp scripts/wiki_nginx.conf /etc/nginx/sites-available/
ln -s /etc/nginx/sites-available/wiki_nginx.conf /etc/nginx/sites-enabled/
systemctl restart nginx
systemctl status -l nginx
curl --head http://localhost/wiki/Чемпионат_Европы_по_футболу_2024.html

