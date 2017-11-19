from subprocess import check_output
import pickle
import os
import glob
from os import system, chdir, getcwd, environ
import time
import sys
import urlparse

from bs4 import BeautifulSoup
import mechanize

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

if sys.platform == 'darwin':
  environ['PDFTK_PATH'] = '/usr/local/bin/pdftk'
import pypdftk


# jobid = sys.argv[1]
jobid = environ.get("JOBID")
curloutputfile = "curloutput"
with open(curloutputfile) as f:
  curlline = f.read().strip()

abstract_boilerplate = '''\
This is a job application.
'''


print "did you turn submissions back on???"

def login():

  br = mechanize.Browser()
  br.set_handle_robots(False)
  print "opening search page"
  br.open('https://search.uicbits.net/')
  br.select_form(nr=0)
  br['email']=environ.get("ROBOT_USERNAME")
  br['password']=environ.get("ROBOT_PASSWORD")
  response=br.submit()

  for link in br.links():
    if link.url == 'index':
      resp = br.follow_link(link)
      break
  return br
  


def create_applicant(name,uid,url,fname):
  br = login()
  
  for link in br.links():
    if link.text == 'New submission':
      resp = br.follow_link(link)
      break

  br.select_form(nr=1)
  br['title'] = name
  br['auname1']  = uid
  br['auemail1'] = environ.get("ROBOT_USERNAME")
  br['auaff1']   = name
  br['opt1'] = url 
  br.form.add_file(open(fname),'application/pdf',fname,nr=0)
  response = br.submit()
  resp = response.read()
  if resp.find('confirm">Submitted submission') != -1:
    print "successful:",uid
  else:
    print "unsuccessful:",uid
    print resp[:200]




def completed_applicants(pagetext):
  et = BeautifulSoup(pagetext,"lxml")
  # grab all rows of table
  applicants = et.select('#full_content tr')
  completed = []
  print "num apps: %d" % len(applicants)
  for item in applicants:
    # print item
    # print item.select('canvas[title*=Completed]')
    if len( item.select('canvas[title*=Completed]')) == 1:
      namecell =  item.select('td:nth-of-type(2) a')[0]
      pdfcell = item.select('td:nth-of-type(8) a')[0]
      url = namecell.get('href')
      name = namecell.get_text()
      pdfurl = pdfcell.get('href')
      yield (name,url,pdfurl)


candidate_id_name = 'userID=([0-9]+)&jobID=[0-9]+">([^<]+)'

list_url = 'https://employ.uillinois.edu/admin/jobs/candidates/list.cfm?jobID=%s&per=500&start=1'
ts = time.strftime("%Y%m%d")

def extract_just_cookie(cmd):
  begin, end = cmd.split("' -H 'Cookie:")
  cookie = end[1:end.find("'")] 
  return cookie


def extract_cookie_from_curl(cmd):
  begin, end = cmd.split("' -H 'Cookie:")
  cookie = "Cookie:" + end[:end.find("'")] 
  return cookie

def input_url():
  return raw_input("paste curl from chrome pls\n")

def update_applicants(updates):
  br = login()

  visited = []
  alllinks = list(br.links(url_regex='paper/'))
  numfixed = 0
  for link in alllinks:
    if link.url in visited or link.text == 'New submission':
      continue
    # print link
    br.follow_link(link)
    try:
      br.select_form(nr=2)
      this_url = br['opt1']
      if this_url in updates:
        name, uid, fname = updates[this_url]
        br.form.add_file(open(fname),'application/pdf',fname,nr=0)
        response = br.submit()
        print "updated and deleting file for %s (%s)"% (name,uid)
        os.unlink(fname)
        br.back()
        del updates[this_url]
    except Exception as e:
      print e
      print link
      br.back()
    visited.append(link.url)
    br.back()

  # all keys left in updates are new apps
  for url in updates.keys():
    name,uid,fname = updates[url]
    create_applicant(name,uid,url,fname)

broken = [
     "https://employ.uillinois.edu/admin/candidates/show.cfm?userID=841918&jobID=70888"]


def main():
  jobfile = "applicants.%s.pkl"%jobid
  try:
    os.mkdir(jobid)
  except OSError:
    print "jobid dir already exists"
  chdir(jobid)
  try:
    with open(jobfile,"rb") as f:
      app_record = pickle.load(f)
  except IOError:
    app_record = {}

  updates = {}
  # data is persistent list of apps already created,
  # attempted is ones we've done this iteration

  # cookie = extract_cookie_from_curl(input_url())
  cookie = 'Cookie: ' + curlline
  getthisurl = list_url % jobid
  curlargs = ["curl","-s",getthisurl,"-H",cookie]
  h =  check_output(curlargs)
  for name,url,pdfurl in completed_applicants(h):
    if url in broken:
      print "SKIPING BROKE APP"
      continue

    qs = urlparse.urlparse(url).query
    uid = urlparse.parse_qs(qs)['userID'][0]
    fname = "%s.%s.%s.pdf" % (jobid,uid,ts)

    # need to submit this form to receive the concatenated PDFs
    br = mechanize.Browser()
    br.addheaders = [('Cookie',curlline)]
    br.set_handle_robots(False)
    br.open(pdfurl)
    br.select_form(nr=0)
    response=br.submit()
    file_content = response.read()
    with open(fname,'wb') as f:
      f.write(file_content)

    

    # system("curl -s '%s' -H '%s' > %s" % (pdfurl,cookie,fname))
    
    # accumulate updates for full pass on applicants
    
    num_pages = pypdftk.get_num_pages(fname)
    if app_record.get(uid,0) == num_pages:
      print "%s (%s) unchanged number of pages, skipping" % (uid, name)
      os.unlink(fname)
    else:
      print "%s (%s) new/changed" % (uid, name)
      print "oldnum: %d\nnewnum: %d" % (app_record.get(uid,0),num_pages)
      updates[url] = (name,uid,fname)
      app_record[uid] = num_pages
  
  update_applicants(updates)
  with open(jobfile,"wb") as f:
    pickle.dump(app_record,f)
      

def fixme():
  chdir(jobid)
  filenames = glob.glob("*.pdf")
  updates = {}
  for fn in filenames:
    ji, appid, dt,dc = fn.split('.')
    url = "https://employ.uillinois.edu/admin/candidates/show.cfm?userID=%s&jobID=%s" % (appid,ji)
    updates[url] = ("updated applicant",appid,fn)
  update_applicants(updates)

if __name__=='__main__':
  # fixme()
  main()

'''
with open('users.' + ts) as f:
  for line in f.readlines():
    uid,url,lname,fname = line.strip().split(',')
    system("curl 'https://employ.uillinois.edu/admin/app/controllers/cnt_documents.cfc?method=downloadDocumentsByUserID&userID=" + uid + "&jobID=37195' -H 'DNT: 1' -H 'Accept-Encoding: gzip,deflate,sdch' -H 'Host: employ.uillinois.edu' -H 'Accept-Language: en-US,en;q=0.8' -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/30.0.1599.66 Safari/537.36' -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8' -H 'Referer: https://employ.uillinois.edu/admin/documents/open_merged.cfm?method=downloadDocumentsByUserID&userID=" + uid + "&jobID=37195' -H 'Cookie: TESTID=test; ARRHireTouchIllinoisAdminAffinity1=49760a4ef48c29adc1948e3d72948c0e1888f31473c3b7714c3496dcd03f9d8e; cookies=%7B%22weather_zip%22%3A%22%22%7D; applicant_overview=demographics%2Creferences%2Cdocuments; HIRETOUCH_ADAEAAAADBBAE_SESSIONTOKEN=0727F9AD%2D3595%2D460A%2DB11C%2DC7C02935733E; RedirectString=https%3A%2F%2Fappserv6.admin.uillinois.edu%2Fappslogin%2Fservlet%2Fappslogin%3FappName%3Dedu.uillinois.aits.HireTouchHelper; EnterpriseSessionId=52756894-2102-4ba7-b987-de1717d52ce3-131.193.40.235; ILLINOIS_EAS=true; HireTouchSessionTimeout=1385609143437' -H 'Connection: keep-alive' -H 'Cache-Control: max-age=0' --compressed > " + uid + "." + date + ".pdf")


'''
