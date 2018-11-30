#!/bin/bash
# docker run -ti --rm --name gcloud-config google/cloud-sdk gcloud compute --project=loyal-parser-163116 disks snapshot new-webserver --zone=us-central1-c --snapshot-names=backup-`date +%Y%m%d`

cd /home/ckanich/hiretouch-hotcrp

node extract_cookie.js > curloutput
python populate.py > last_populate
