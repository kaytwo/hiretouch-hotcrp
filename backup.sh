#!/bin/bash

gcloud compute --project=loyal-parser-163116 disks snapshot new-webserver --zone=us-central1-c --snapshot-names=backup-`date +%Y%m%d`
