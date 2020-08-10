import urllib
import urllib2
import thread
import threading
import MultipartPostHandler
import cookielib

class HttpThread(threading.Thread):
#    def on_thread_finished(self, thread, data):
#        pass
    
    #def __init__(self):
	#self._is_running = False
	
    def setup(self, url, values, callback, action):
	self.url = url
	self.values = values
	self.callback = callback
	self.action = action
	
    def login_routine(self):
	try:	    
	    if self.values != None:
		data = urllib.urlencode(self.values)
	    req = urllib2.Request(self.url, data)
	    response = urllib2.urlopen(req)
	    result = response.read()	    
	    if self.callback != None:
		self.callback(result)
	except:
	    if self.callback != None:
		self.callback("ERROR")
		
    def download_routine(self):
	try:
	    req = urllib2.Request(self.url, None)
	    response = urllib2.urlopen(req)
	    result = response.read()	    
	    if self.callback != None:
		self.callback(self.values['sid'], result)
	except:
	    if self.callback != None:
	        self.callback(None, "ERROR")
		
    def upload_routine(self):
	#try: 
	cookies = cookielib.CookieJar()
	#print "build_opener"
	opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookies),
                            MultipartPostHandler.MultipartPostHandler)
	#print "opener.open"
	#params = { "username" : "wuhsi", 
	#           "file" : open("filename", "rb") }    
	response = opener.open(self.url, self.values)   #.read().strip()
	#print "response.read"	    
	result = response.read()
	#print "result = " + result
	if self.callback != None:
	    self.callback(result)
	#except:
	#    print "except"
	#    if self.callback != None:
	#    	self.callback("ERROR")	    
	
    def query_routine(self):
	try:	    
	    if self.values != None: 
		data = urllib.urlencode(self.values)
	    url = self.url + '?' + data
	    req = urllib2.Request(url, None)
	    response = urllib2.urlopen(req)
	    if self.callback != None:
		self.callback(response)
	except:
	    if self.callback != None:
		self.callback("ERROR")
		
    def echo_routine(self):
	try:	    
	    url = self.url
	    req = urllib2.Request(url, None)
	    response = urllib2.urlopen(req)
	    result = response.read()
	    if self.callback != None:
		self.callback(result)
	except:	    
	    if self.callback != None:
		self.callback("ERROR")

    def interact_routine(self):
	try:	    
	    if self.values != None:
		data = urllib.urlencode(self.values)
	    req = urllib2.Request(self.url, data)
	    response = urllib2.urlopen(req)
	    result = response.read()	    
	    if self.callback != None:
		self.callback(result)
	except:
	    if self.callback != None:
		self.callback("ERROR")
    
    def querylike_routine(self):
	try:	    
	    if self.values != None:
		data = urllib.urlencode(self.values)
	    url = self.url + '?' + data
	    req = urllib2.Request(url, None)
	    response = urllib2.urlopen(req)
	    result = response.read()
	    if result == '1' and self.callback != None:
		self.callback(self.values['music_id'], True)
	    elif result == '0' and self.callback != None:
		self.callback(self.values['music_id'], False)
	except:	    
	    if self.callback != None:
		self.callback("ERROR")
    
    def run(self):
	if self.action == "LOGIN":
	    self.login_routine()
	elif self.action == "ECHO":
	    self.echo_routine()
	elif self.action == "UPLOADTHUMB":
	    self.upload_routine()
	elif self.action == "LISTRECENT":
	    self.query_routine()
	elif self.action == "DOWNLOAD":
	    self.download_routine()
	elif self.action == "INTERACT":
	    self.interact_routine()
	elif self.action == "ISLIKE":
	    self.querylike_routine()