# -*- coding: utf-8 -*-
import datetime,re,requests
# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
REPORT_DAYS = 1
MAILGUN_KEY = 'key-297e3d8d51b08f45259c1f9d9191548d'
MAILGUN_SANDBOX = 'sandboxbb254b3e33c14969979996793b5e3ec2.mailgun.org'
MAILGUN_RECIPIENT = 'daniel@erateconsulting.org'

def today():
  return datetime.datetime.now().strftime('%Y-%m-%d')

def sendEMAIL(html='',csv='',total=0):
  request_url = 'https://api.mailgun.net/v2/{0}/messages'.format(MAILGUN_SANDBOX)
  data={
    'from': 'FRN Denial Job <usac@scrappinghub.com>',
    'to': MAILGUN_RECIPIENT,
    'subject': 'UASAC FRNs Denied on %s' % datetime.datetime.now().strftime('%Y-%m-%d'),
    'text': 'Founded %s %s in %s %s.' % (total,'item' if total==1 else 'items',REPORT_DAYS,'day' if REPORT_DAYS==1 else 'days')
  }
  if html:
    data['html'] = html
  files = [("attachment", ("report%s.csv" % today(), csv))] if csv and total else []
  request = requests.post(request_url, auth=('api', MAILGUN_KEY), data=data,files=files)
  
reportFields = [
    'FCDLDate', 'FRNStatus', 'BilledEntityName', 'BEN', 'ApplicantState',
    'FourSeventyOneContactEmail', 'ApplicantType', 'FCDLCommentforFRN', 'FCDLCommentforFourSeventyOneApplication',
    'FourSeventyOneContactName', 'BENAccountAdministrator', 'BENAccountAdministratorEmail', 'FourSeventyOneConsultingFirmName',
    'OrigFundingRequest', 'CmtdFundingRequest', 'OrigDiscount', 'OrigFRNServiceType',
    'FRN', 'FourSeventyOneApplicationNumber'
  ]
  
def makeHTMLTR(item):
  tr = '<tr>'
  for field in reportFields:
    tr+= '<td>'+str(item[field])+'</td>'
  tr+= '</tr>'  
  return tr

def makeCSVrow(item):
  row = ','.join(['"'+str(item[field]).replace('"',"'")+'"' for field in reportFields])+'\n'
  return row
  
def makeHTMLReport(TRs):
  html = '<html><body>'
  if TRs:
    html+= '<h3>Founded %s items in %s days</h3>' % (len(TRs),REPORT_DAYS)
    html+= '<table border="1"><thead>'
    for field in reportFields:
      html+= '<th>'+field+'</th>'
    html+= '</thead><tbody>'
    for tr in TRs:
      html+= tr
    html+= '</tbody></table>'
  else:
    html+='<h1>No items found in %s days</h1>' % REPORT_DAYS
  html+= '</body></html>'
  return html  

def makeCSVReport(csv_rows):
  csv = ','.join(['"%s"' % f for f in reportFields])+'\n'
  for row in csv_rows:
    csv+= row
  return csv
  
def isPresent(raw,present_date):
  if not re.match('\d{2}/\d{2}/\d{4}',str(raw)):
    return False 
  m,d,y = [int(x) for x in raw.split('/')]
  dt = datetime.datetime(y,m,d)
  return dt > present_date

class UsacPipeline(object):
    def process_item(self, item, spider):
        if isPresent(item['FCDLDate'],self.present_date):
          self.TRs.append(makeHTMLTR(item))
          self.csv_rows.append(makeCSVrow(item))
        return item
    
    def open_spider(self,spider):
        self.present_date = datetime.datetime.now()-datetime.timedelta(days=REPORT_DAYS+1)
        self.TRs = []
        self.csv_rows = []
    
    def close_spider(self,spider):
        html = makeHTMLReport(self.TRs)
        csv = makeCSVReport(self.csv_rows)
        sendEMAIL(csv=csv,total=len(self.csv_rows))