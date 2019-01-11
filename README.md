### Plumbing to ingest HireTouch based job applicants into a hotCRP instance

#### setup TLDR

* Install hotCRP, add a user that will submit application packets
* add `URL` option to the submission form of type text. This needs to be the first custom field added.
* add secrets/configuration to `dotenv-template`, rename to `.env`
* Install pdftk, node, python2, and needed language packages (`npm install` & `pip install -r requirements.txt`)
* Fix the working directory in `backup.sh` and add it as a daily cron job.
* For recent Ubuntu/Debian, `pdftk` cannot be installed from default apt: https://askubuntu.com/questions/1028522/how-can-i-install-pdftk-in-ubuntu-18-04-and-later


#### Goal/architecture

HireTouch is super slow and basically unusable for managing a large number of job applicants for e.g. a CS faculty search. This collection of scripts will programmatically download each application packet, "submit" it as a "paper" to a hotCRP instance, and when rerun will keep those application packets up to date as reference letters come in.

#### Non-goals

This system does NOT request letters, it does not mark applications as complete, and it does not mark them as "meets minimum qualifications." These still need to be done by the search committee or an office admin.

#### Before using these scripts

Install https://github.com/kohler/hotcrp and create a user account that will be used for uploading all of the application materials.

#### Pipeline

`backup.sh` coordinates everything and can be added to a daily cron job. Some form of backup should be added (the gcloud command line option if being run in GCP is currently commented out) out of band to recover from any catastrophic failures. The git repository location also needs to be updated as it's currently hardcoded.

`dotenv-template` should be filled out with both the HireTouch user's UIC credentials (no way around this :(), the submission bot account credentials, and the job ID from hiretouch (can be found in the URL for the job under a jobID URL parameter). Rename this file to `.env` and DO NOT COMMIT IT TO VERSION CONTROL.

**Run once**: install node, and then run `npm install` to download the packages needed for the cookie extraction script. Install python 2 and pip, and run `pip install -r requirements.txt` to install the packages needed for the download & submission script.

`extract_cookie.js` loads the UIC hiretouch page, logs in using the username from `.env`, and then extracts the cookie from the cookie jar so that automated requests can be made to the HireTouch server. If you do not want to save your UIC credentials on the virtual machine, you can run `node extract_cookie.js > curloutput` someplace else, and then copy that file (which has an auth cookie in it) to the VM. I don't know how long that cookie lasts before it expires, but it's certainly more than a few hours.

`populate.py` is a horrible spaghetti code abomination that has grown over the past few years of slight changes to hotCRP and hiretouch. As of January 2019 it doesn't cause errors on any of the couple hundred applications it's been used to download, but that can always change.

#### Debugging

Regretfully "ask Chris to look at it" might be the best plan at this point. The output of the populate script has some basic print debugging, and `backup.sh` saves this to the text file `last_populate` so that may be of use.
