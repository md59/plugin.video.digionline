import urllib, urllib2
import cookielib
import os

import re
from bs4 import BeautifulSoup
import json
import requests.utils
from common import *

from common import *

class Digi():

  protocol = 'https'
  siteUrl = protocol + '://www.digionline.ro'
  siteUrlProTv = protocol + '://protvplus.ro/'
  siteUrlStirileProTv = protocol + '://stirileprotv.ro'

  number_pattern = re.compile("[0-9]+")
  stirile_protv_stream_pattern = re.compile("\"" + protocol + "://" + ".*m3u8.*\"")
  protv_channel_category_general = "general"
  protv_channel_category_tematice = "tematice"
  protv_channel_category_filme = "filme"
  protv_channel_category_stiri = "stiri"
  channel_name_protv_stripped = "protv"
  channel_name_pro2_stripped = "pro2"
  channel_name_prox_stripped = "prox"
  channel_name_progold_stripped = "progold"
  channel_name_procinema_stripped = "procinema"
  channel_name_stirileprotv_stripped = "stirileprotv"
  protv_channel_default_names = {
    channel_name_protv_stripped: "Pro TV",
    channel_name_pro2_stripped: "Pro 2",
    channel_name_prox_stripped: "Pro X",
    channel_name_progold_stripped: "Pro Gold",
    channel_name_procinema_stripped: "Pro Cinema",
    channel_name_stirileprotv_stripped: "Stirile ProTV"
  }
  protv_channel_categories = {
    channel_name_protv_stripped: protv_channel_category_general,
    channel_name_pro2_stripped: protv_channel_category_tematice,
    channel_name_prox_stripped: protv_channel_category_tematice,
    channel_name_progold_stripped: protv_channel_category_tematice,
    channel_name_procinema_stripped: protv_channel_category_filme,
    channel_name_stirileprotv_stripped: protv_channel_category_filme
  }
  protv_channel_url = {
    channel_name_protv_stripped: "https://vid.hls.protv.ro/protvhdn/protvhd.m3u8?1",
    channel_name_pro2_stripped: "https://vid.hls.protv.ro/pro2n/pro2_3_34/index.m3u8?1",
    channel_name_prox_stripped: "https://vid.hls.protv.ro/proxhdn/proxhd.m3u8?1",
    channel_name_progold_stripped: "https://vid.hls.protv.ro/progoldn/progold.m3u8?1",
    channel_name_procinema_stripped: "https://vid.hls.protv.ro/procineman/procinema.m3u8?1",
    channel_name_stirileprotv_stripped: "https://vid.hls.protv.ro/protvnews/protvnews_high/index.m3u8?1"
  }
  protv_channel_default_logo = {
    channel_name_protv_stripped: "https://vignette.wikia.nocookie.net/tvfanon6528/images/e/e0/Pro_TV_(2017-.n.v.).pn",
    channel_name_pro2_stripped: "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d9/Logo_Pro_2_%282017%29.svg/1200px-Logo_Pro_2_%282017%29.svg.png",
    channel_name_prox_stripped: "https://upload.wikimedia.org/wikipedia/commons/thumb/9/99/Logo_Pro_X_%282017%29.svg/1200px-Logo_Pro_X_%282017%29.svg.png",
    channel_name_progold_stripped: "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d3/Logo_Pro_Gold_%282017%29.svg/1200px-Logo_Pro_Gold_%282017%29.svg.png",
    channel_name_procinema_stripped: "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8a/Logo_Pro_Cinema_%282017%29.svg/1024px-Logo_Pro_Cinema_%282017%29.svg.png",
    channel_name_stirileprotv_stripped: "https://vignette.wikia.nocookie.net/logopedia/images/4/45/Stirile_Pro_TV_logo_2017.png"
  }

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
      # addon_log(self.siteUrl)
      # addon_log(response)
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
      # print(response.read())
      # addon_log(response.read())


    landedUrl = response.geturl()
    # addon_log(landedUrl)
    if(landedUrl == self.siteUrl + '/auth/login'):
      print('Login error')
      return

    #retry login if we get a response page with Login link in it
    html = response.read()
    soup = BeautifulSoup(html, "html.parser")
    loginLink = soup.find('a', class_="header-account-login", href=True)
    # addon_log(loginLink)
    if(loginLink != None):
      addon_log('Login error retry by reset login')
      os.remove(self.cookieFile)
      self.cookieJar = cookielib.LWPCookieJar(filename=self.cookieFile)
      self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cookieJar))
      return self.login(username, password)

    # print(response.info())
    # print(response.geturl())
    # print(response.getcode())
    return html

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
    # addon_log(html)
    # f= open("test.html","w+")
    # f.write(html)
    # f.close()
    soup = BeautifulSoup(html, "html.parser")
    catLinks = soup.find_all('a', class_="nav-menu-item-link", href=True)
    # addon_log(catLinks)
    # print(catLinks)
    cats = []
    for link in catLinks:
      if(link['href'] != '/') and (link['href'] != '/hbo-go') and (link['href'] != '/play'):
        cats.append({'name': link['title'],
                     'url': link['href']
                    })
        # print(link['href'])
        # print(link['title'])
    return cats

  def get_protv_stripped_channel_name(self, channel_name):
    return channel_name.lower().strip().replace(" ", "")

  def get_protv_channel_category(self, channel_name):
    channel_name_stripped = self.get_protv_stripped_channel_name(channel_name)
    try:
      category = self.protv_channel_categories[channel_name_stripped]
      if category is None:
        return self.protv_channel_category_general
      return category
    except:
      return self.protv_channel_category_general

  def get_protv_channel_url(self, channel_name):
    channel_name_stripped = self.get_protv_stripped_channel_name(channel_name)
    try:
      url = self.protv_channel_url[channel_name_stripped]
      if url is None:
        return ""
      return url
    except:
      return ""

  def get_protv_channel_default_logo(self, channel_name):
    channel_name_stripped = self.get_protv_stripped_channel_name(channel_name)
    try:
      logo = self.protv_channel_default_logo[channel_name_stripped]
      if logo is None:
        return ""
      return logo
    except:
      return ""

  def scrape_protv_channels(self):
    channels = []
    html = urllib2.urlopen(self.siteUrlStirileProTv, timeout=1).read()
    soup = BeautifulSoup(html, "html.parser")
    channel_name = self.protv_channel_default_names[self.channel_name_stirileprotv_stripped]
    channel_logo = self.protv_channel_default_logo[self.channel_name_stirileprotv_stripped]
    try:
      show_title = soup.find(class_=None, href="https://stirileprotv.ro/protvnews/").text
      if show_title is None:
        show_title = channel_name
    except:
      show_title = channel_name
    channel_category = self.protv_channel_category_stiri
    try:
      channel_url = [str(stirile_protv_stream_pattern.findall(str(e))[0]).replace("\"", "") for e in soup.find_all("script", type="text/javascript") if "m3u8" in str(e)][0]
      if channel_url is None:
        channel_url = self.protv_channel_url[self.channel_name_stirileprotv_stripped]
    except:
      channel_url = self.protv_channel_url[self.channel_name_stirileprotv_stripped]
    channels.append({'name': channel_name,
                     'url': channel_url,
                     'logo': channel_logo,
                     'show_title': show_title,
                     'category': channel_category
                     })

    try:
      html = urllib2.urlopen(self.siteUrlProTv, timeout=1).read()
      soup = BeautifulSoup(html, "html.parser")
    except:
      return channels

    for e in soup.find_all("a", attrs={'data-channel-id': self.number_pattern}):
      show_title = str(e.find(class_="b-program").find(class_="e-title", recursive=False).text).title().replace("Tv", "TV")
      if show_title is None:
        show_title = "Program"
      channel_name = str(e.find(class_="e-logo").find("img")["alt"]).title().replace("Tv", "TV")
      if channel_name is None:
        channel_name = "Pro TV"
      #channel_logo = str(e.find(class_="e-logo").find("img")["src"])
      #if channel_logo is None:
      #  channel_logo = self.get_protv_channel_default_logo(channel_name)
      channel_logo = self.get_protv_channel_default_logo(channel_name)
      channel_category = self.get_protv_channel_category(channel_name)
      channel_url = self.get_protv_channel_url(channel_name)

      channels.append({'name': channel_name,
                       'url': channel_url,
                       'logo': channel_logo,
                       'show_title': show_title,
                       'category': channel_category
                      })
    return channels

  def scrapChannels(self, url):
    html = self.getPage(url)
    # print(html)
    soup = BeautifulSoup(html, "html.parser")
    
    boxs = soup.find_all(class_="box-content")
    channels = []
    for box in boxs:
      #soup = BeautifulSoup(str(box.contents), "html.parser")
      for cnt in box.contents:
        cntString = cnt.encode('utf-8')
        soup = BeautifulSoup(cntString, "html.parser")
      
        # url
        chLink = soup.find('a', class_="box-link", href=True)
        if(chLink):
          chUrl = chLink['href']

        # name
        chNameNode = soup.find('h5')
        if(chNameNode):
          chName = chNameNode.string
          chName = chName.replace('\\n', '')
          chName = re.sub('\s+', ' ', chName)
          chName = re.sub('&period', '.', chName)
          chName = re.sub('&colon', ':', chName)
          chName = re.sub('&comma', ',', chName)
          # chName = re.sub('&\w+', ' ', chName)
          # chName = chName.strip()
          
        # logo
        logo = soup.find('img', alt="logo", src=True)
        if(logo):
          logoUrl = logo['src']

      channels.append({'name': chName,
                       'url': chUrl,
                       'logo': logoUrl
                      })
    return channels

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
      # print(url);
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
    if 'stream_url' in chData and chData['stream_url']:
      # url = self.protocol + ':' + chData['stream_url']
      url = chData['stream_url']
    else:
      if 'data' in  chData and 'content' in chData['data'] and  'stream.manifest.url' in chData['data']['content'] and chData['data']['content']['stream.manifest.url']:
        url = chData['data']['content']['stream.manifest.url']
      else:
        err = chData['error']['error_message']
        soup = BeautifulSoup(err)
        err = soup.get_text()
    return {'url': url,
            'err': err}

if __name__ == "__main__":
  Digi().scrape_protv_channels()
