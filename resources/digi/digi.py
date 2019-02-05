import urllib, urllib2
import cookielib

import re
from bs4 import BeautifulSoup
import json
import requests.utils

class Digi():

  protocol = 'https'
  siteUrl = protocol + '://www.digionline.ro'

  headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Encoding': 'identity',
    'Accept-Language': 'en-US,en;q=0.5', 
    'Connection': 'keep-alive',
    'Host': 'www.digionline.ro',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:60.0) Gecko/20100101 Firefox/60.0'
  }

  cookieFile = 'cookies.txt'

  def __init__( self , *args, **kwargs):
    if(kwargs.get('cookieFile')):
      self.cookieFile=kwargs.get('cookieFile')
    self.cookieJar = cookielib.LWPCookieJar(filename=self.cookieFile)
    try:
      self.cookieJar.load(filename=self.cookieFile, ignore_discard=True, ignore_expires=True)
    except:
      pass
    self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cookieJar))

  def login( self, username, password):
    if(self.getCookie('deviceId') != None):
      request = urllib2.Request(self.siteUrl, None, self.headers)
      response = self.opener.open(request)
      # print(response.read())
    else:
      request = urllib2.Request(self.siteUrl + '/auth/login', None, self.headers)
      response = self.opener.open(request)
      self.cookieJar.save(filename=self.cookieFile, ignore_discard=True, ignore_expires=True)

      logindata = urllib.urlencode({
        'form-login-email': username,
        'form-login-password': password,
      })
      request = urllib2.Request(self.siteUrl + '/auth/login', logindata, self.headers)
      response = self.opener.open(request)
      self.cookieJar.save(filename=self.cookieFile, ignore_discard=True, ignore_expires=True)
      
      logindata = urllib.urlencode({
        'form-login-mode': 'mode-all'
      })
      request = urllib2.Request(self.siteUrl + '/auth/login', logindata, self.headers)
      response = self.opener.open(request)
      self.cookieJar.save(filename=self.cookieFile, ignore_discard=True, ignore_expires=True)
      #print(response.read())
    
   
    landedUrl = url = response.geturl()
    if(landedUrl == self.siteUrl + '/auth/login'):
      print('Login error')
      return

    # print(response.info())
    # print(response.geturl())
    # print(response.getcode())
    return response.read()

  def getPage(self, url, data=None, xhr=False):
    if (data != None):
      data = urllib.urlencode(data)
    request = urllib2.Request(self.siteUrl + url, data, self.headers)
    if(xhr):
      request.add_header('X-Requested-With', 'XMLHttpRequest')
    if (data != None):
      request.add_header('Content-Type', 'application/x-www-form-urlencoded')
    response = self.opener.open(request)
    return response.read()

  def scrapCats(self, html):
    if(html == None):
      return
    # print(html)
    soup = BeautifulSoup(html, "html.parser")
    catLinks = soup.find_all('a', class_="nav-menu-item-link", href=True)
    # print(catLinks)
    cats = []
    for link in catLinks:
      if(link['href'] != '/'):
        cats.append({'name': link['title'],
                     'url': link['href']
                    })
        # print(link['href'])
        # print(link['title'])
    return cats
  
  def scrapChannels(self, url):
    html = self.getPage(url)
    # print(html)
    soup = BeautifulSoup(html, "html.parser")
    
    boxs = soup.find_all(class_="box-content")
    channels = []
    for box in boxs:
      soup = BeautifulSoup(str(box.contents), "html.parser")
      # url
      chLink = soup.find('a', class_="box-link", href=True)
      chUrl = chLink['href']
      # name
      chName = soup.find('h5')
      chName = chName.text
      chName = chName.replace('\\n', '')
      chName = re.sub('\s+', ' ', chName)
      chName = chName.strip()
      # logo
      logo = soup.find('img', alt="logo", src=True)
      logoUrl = logo['src']

      channels.append({'name': chName,
                       'url': chUrl,
                       'logo': logoUrl
                      })
    return channels;

  def getCookie(self, name):
    cookies = requests.utils.dict_from_cookiejar(self.cookieJar)
    try:
      return cookies[name]
    except:
      return None

  def scrapPlayUrl(self, url, quality = None):
    html = self.getPage(url)
    # print(html)
    soup = BeautifulSoup(html, "html.parser")
    player = soup.select("[class*=video-player] > script")
    # print(player)
    if(len(player) == 0):
      return
    jsonStr = player[0].text.strip()
    # print(jsonStr)
    chData = json.loads(jsonStr)
    url = chData['new-info']['meta']['streamUrl']
    chId = chData['new-info']['meta']['streamId']
    #detect Quality or try the manualy choosed one
    if(quality != None):
      arrQuality = [quality]
    else: 
      abr = False
      if hasattr(chData['new-info']['meta'], 'abr'):
        abr = chData['new-info']['meta']['abr']
      if(abr):
        arrQuality = ['abr', 'hq', 'mq', 'lq']
      else:
        arrQuality = ['hq', 'mq', 'lq']

    if(chData['shortcode'] == 'livestream'):
      data = {
        'id_stream': chId,
        'quality': None 
      }
    elif(chData['shortcode'] == 'nagra-livestream'):
      data = {
        'id_device': self.getCookie('deviceId'),
        'id_stream': chId,
        'quality': None 
      }
    for q in arrQuality:
      data['quality'] = q
      # print(data)
      # print(q)
      jsonStr = self.getPage(url, data, xhr=True)
      if(jsonStr):
        try:    
          chData = json.loads(jsonStr)
          if(chData['stream_url']):
            break
        except:
          pass

    err = None 
    url=None
    if(chData['stream_url']):
      url = self.protocol + ':' + chData['stream_url']
    else:
      err = chData['stream_err']
    return {'url': url,
            'err': err}