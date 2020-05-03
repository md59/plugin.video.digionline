import xbmc, xbmcgui, xbmcplugin, xbmcaddon
import os, urllib
import multiprocessing.dummy as multiprocessing

from common import *
from resources.digi.digi import Digi

addonId = 'plugin.video.digionline'
addon = xbmcaddon.Addon(id=addonId)
logFile = os.path.join(xbmc.translatePath(addon.getAddonInfo('profile')), addonId+'.log')
cookieFile = os.path.join(xbmc.translatePath(addon.getAddonInfo('profile')), 'cookies.txt')

def addDir(name, url, mode):
  u = sys.argv[0] + "?url=" + urllib.quote_plus(url) + '&mode=' + str(mode)

  liz = xbmcgui.ListItem(name)
  liz.setInfo( type="Video", infoLabels={ "Title": name })
  ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
  return ok

def addLink(name, url, logo, mode):
  u = sys.argv[0] + "?url=" + urllib.quote_plus(url) + "&name=" + urllib.quote_plus(name) + \
                    "&logo=" + urllib.quote_plus(logo) +'&mode=' + str(mode)

  liz = xbmcgui.ListItem(name, thumbnailImage=logo)
  liz.setInfo( type="Video", infoLabels={ "Title": name, "Plot": ''} )
  ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=False)
  return ok

def listCat():
  if(addon.getSetting('reset_login') == 'true'):
    os.remove(cookieFile)
    addon.setSetting(id='reset_login', value='false')

  digi = Digi(cookieFile = cookieFile)
  html = digi.login(addon.getSetting('username'), addon.getSetting('password'))

  #addon_log(html)
  if(html == None):
    addon_log('Login error')
    xbmcgui.Dialog().ok(addon.getLocalizedString(30015), addon.getLocalizedString(30016))
    return

  cats = digi.scrapCats(html)

  for cat in cats:
    addDir(name =  cat['name'].encode('utf8'), url=cat['url'], mode=1)

def listCh(url):
  addon_log(url)
  digi = Digi(cookieFile = cookieFile)
  channels = digi.scrapChannels(url)

  stirileprotv_channels = []
  protv_channels = []
  protv_thread_wait_time = 3
  protv_pool = multiprocessing.Pool(processes=2)
  protv_thread_result = protv_pool.apply_async(digi.scrape_protv_channels, (url,))
  stirile_protv_thread_result = protv_pool.apply_async(digi.scrape_stirileprotv_channels, (url,))
  protv_pool.close()
  try:
    protv_channels.extend(protv_thread_result.get(protv_thread_wait_time))
  except:
    pass
  try:
    stirileprotv_channels.extend(stirile_protv_thread_result.get(protv_thread_wait_time))
  except:
    pass

  for ch in channels:
    addLink(name =  ch['name'].encode('utf8'),
            url =  ch['url'],
            logo = ch['logo'],
            mode = 2)

  for ch in stirileprotv_channels + protv_channels:
    if ch['category'] in str(sys.argv[2]).lower() or ch['category'] in url.lower():
      liz = xbmcgui.ListItem(ch["show_title"] + " la " + ch["name"], thumbnailImage=ch["logo"])
      liz.setInfo(type="Video", infoLabels={"Title": ch["name"], "Plot": ""})
      xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=ch["url"], listitem=liz, isFolder=False)

def play(url, name, logo):
  addon_log(url)

  quality = None
  arrQualities = ['abr', 'hq', 'mq', 'lq']
  if(addon.getSetting('choose_quality') == 'true'):
    dialog = xbmcgui.Dialog()
    quality = dialog.select(addon.getLocalizedString(30018), arrQualities)
    quality = arrQualities[quality]
    # addon_log(quality)

  digi = Digi(cookieFile = cookieFile)
  url = digi.scrapPlayUrl(url, quality)
  if(url['err'] != None):
    addon_log(url['err'])
    xbmcgui.Dialog().ok(addon.getLocalizedString(30013), url['err'])
  else:
    listitem = xbmcgui.ListItem(name, thumbnailImage=logo)
    listitem.setInfo('video', {'Title': name})
    xbmc.Player().play(url['url'], listitem)

#######################################################################################################################
#######################################################################################################################
#######################################################################################################################
#read params
params=getParams()
try:
  mode=int(params["mode"])
except:
  mode=None
try:
  url=urllib.unquote_plus(params["url"])
except:
  url=None
try:
  name=urllib.unquote_plus(params["name"])
except:
  name=None
try:
  logo=urllib.unquote_plus(params["logo"])
except:
  logo=None

if (mode==None): #list categories
  listCat()
elif (mode==1):  #list channels
  listCh(url = url)
elif (mode==2):  #play stream
  if xbmc.Player().isPlaying():
    xbmc.Player().stop()
  play(url = url, name = name, logo=logo)

xbmcplugin.endOfDirectory(int(sys.argv[1]))