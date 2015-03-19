
import os.path
import re, sys
import urllib
import urllib2
import cookielib
#import json
#import math
import xbmcaddon
import xbmcplugin
import xbmcgui
import random

class OpenTV:
    def __init__(self, homedir='', username='', password=''):

        self.__timeout=10
        self.__username = username
        self.__password=password
        if homedir:
            self.__cookieFile=os.path.join(homedir, 'cookie.lwp')
            self.__dbFile=os.path.join(homedir, 'resources/db.xml')
        else:
            self.__cookieFile='cookie.lwp'
            self.__dbFile='resources/db.xml'

        self.__loginPage='http://vtvplus.vn/vtv/ajax.php?act=login'
        self.__channelPage='http://vtvplus.vn'
        self.__requestUrl=None
        self.__returnUrl=None
        self.__source=None
        self.__txheaders={'User-agent' : 'Mozilla/5.0 (X11; Linux x86_64) \
                          AppleWebKit/537.17 (KHTML, like Gecko) \
                          Chrome/24.0.1312.70 Safari/537.17', \
                          'Accept':'text/html,application/xhtml+xml,\
                          application/xml;q=0.9,*/*;q=0.8',\
                          'Accept-charset':'ISO-8859-1,utf-8;q=0.7,*;q=0.3',\
                          'Accept-Language':'en-US,en;q=0.8',\
                          'Origin':'http://www.vtvplus.vn'\
                          }

        self.__cj=cookielib.LWPCookieJar()
        if os.path.isfile(self.__cookieFile):
            self.__cj.load(self.__cookieFile, ignore_discard=True, \
                           ignore_expires=True)
        self.__opener=urllib2.build_opener(urllib2.\
                                           HTTPCookieProcessor(self.__cj))
    def __del__(self):
        self.__cj.save(self.__cookieFile, ignore_discard=True, ignore_expires=True)

    def __log(self, msg):
        print msg

    def __request(self, req):
        response = self.__opener.open(req, timeout=self.__timeout)
        self.__html = response.read()
        self.__returnUrl = response.geturl()
        self.__log('Request page : ' + self.__requestUrl +' / Return page : ' + self.__returnUrl)
        response.close()

    #try to open an url
    def __requestPage(self, url, params):
        self.__requestUrl = url
        self.__html=""
        txdata = None
        if params != None:
            txdata = urllib.urlencode(params)
        req = urllib2.Request(url, txdata, self.__txheaders)
        req.add_header('accept','text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8')
        self.__request(req)
    def __login(self):
        self.__log("loging in")
        txdata = { 'username':self.__username, 'password':self.__password}
        self.__requestPage(self.__loginPage, txdata)
        self.__log(self.__html)

    def getVideo(self, url):
        self.__requestPage(url, None)
        s = re.search('var responseText = \"([^\"]*?)\"', self.__html)
        channels = None
        if (s != None):
            channels=s.group(1).split(',')
        else:
            self.__login()
            self.__requestPage(url, None)
            s = re.search('var responseText = \"([^\"]*?)\"', self.__html)
            if (s != None):
                channels=s.group(1).split(',')

        if (len(channels)>0) :
            id = random.choice(range(len(channels)))
            return channels[id]
        return None

    def readGroups(self):
        f = None
        if os.path.isfile(self.__dbFile):
            f = open(self.__dbFile,'r')
        if f:
            xml = f.read()
            reg = re.compile('group id=\"(.+?)\" title=\"(.+?)\"', re.DOTALL)
            match = reg.findall(xml)
            f.close()
            return match
        return None

    def readChannels(self, g):
        f = None
        if os.path.isfile(self.__dbFile):
            f = open(self.__dbFile,'r')
            if f:
                xml = f.read()
                f.close()
                match = re.search('<group id=\"'+g+'\"(.+?)</group>', xml, re.DOTALL)
                if match:
                    return  re.findall('<channel>.*?<title>(.+?)</title>.*?<link>(.*?)</link>.*?<image>(.*?)</image>.*?</channel>', match.group(1), re.DOTALL)
        return None

#end of class OpenTV

addon = xbmcaddon.Addon('plugin.video.OpenVTV')
profile = xbmc.translatePath(addon.getAddonInfo('profile'))
mysettings = xbmcaddon.Addon(id='plugin.video.OpenVTV')
home = mysettings.getAddonInfo('path')
fanart = xbmc.translatePath(os.path.join(home, 'fanart.jpg'))

mode=None

username=addon.getSetting('username')
password=addon.getSetting('password')

myvtv = OpenTV(xbmc.translatePath(home), username, password)

def get_params():
    param=[]
    paramstring=sys.argv[2]
    if len(paramstring)>=2:
        params=sys.argv[2]
        cleanedparams=params.replace('?','')
        if (params[len(params)-1]=='/'):
            params=params[0:len(params)-2]
        pairsofparams=cleanedparams.split('&')
        param={}
        for i in range(len(pairsofparams)):
            splitparams={}
            splitparams=pairsofparams[i].split('=')
            if (len(splitparams))==2:
                param[splitparams[0]]=splitparams[1]

    return param

params=get_params()

try:
    param_link=urllib.unquote_plus(params["link"])
except:
    pass
try:
    param_title=urllib.unquote_plus(params["title"])
except:
    pass
try:
    param_image=urllib.unquote_plus(params["image"])
except:
    pass
try:
    param_gid=urllib.unquote_plus(params["gid"])
except:
    pass
try:
    mode=int(params["mode"])
except:
    pass


def add_link(title, link, image):
    give_url = sys.argv[0]+"?mode=2&link="+urllib.quote_plus(link)+"&title="+ urllib.quote_plus(title)+"&image="+ urllib.quote_plus(image)
    liz = xbmcgui.ListItem( title, title, iconImage=image, thumbnailImage=image)
    liz.setInfo(type="Video", infoLabels={"Title": title})
    liz.setProperty("Fanart_Image",fanart)
    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=give_url,listitem=liz)

def play_video(title, link, image):
    item = xbmcgui.ListItem(title, thumbnailImage=image)
    player = xbmc.Player(xbmc.PLAYER_CORE_MPLAYER)
    try:
        video = myvtv.getVideo(link)
        if video :
            player.play(video, item)
    except:
        return

def add_dir(group_id, group_title) :
    liz = xbmcgui.ListItem(group_title)
    liz.setInfo(type="Video", infoLabels={"Title": group_title})
    liz.setProperty("Fanart_Image",fanart)
    give_url = sys.argv[0]+"?mode=1&title="+urllib.quote_plus(group_title)+"&gid="+urllib.quote_plus(group_id)
    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=give_url, listitem=liz, isFolder=True)

if mode==None :
    groups = myvtv.readGroups()
    if groups:
        for g_id, g_title in groups :
            add_dir(g_id, g_title)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode==1 :
    channels = myvtv.readChannels(param_gid)
    if channels :
        for title, link, image in channels :
            add_link(title, link, image)

    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode==2 :
    play_video(param_title, param_link, param_image)

