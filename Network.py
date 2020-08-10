import Global
from HttpThread import *
import os
import shutil

class Network:
    def __init__(self, main):
	self.main = main
	#self.status = 'no_network'	
	self.status = 'off'	
	#self.check_network(self.check_network_finished)
	self.login(main.username, main.platform, self.login_finished)	
	
    def querylike(self, username, music_id, callback):
	if self.status == 'no_network':
	    callback(None)
	    return

	url = Global.server_ip + '/islike'
	values = {'username' : username, 
                  'music_id': music_id}
	
	thread = HttpThread()
	thread.setup(url, values, callback, "ISLIKE")
	thread.run()	
	
    def interact(self, username, music_id, action, callback):
	if self.status == 'no_network':
	    callback(None)
	    return

	url = Global.server_ip + '/interact'
	values = {'username' : username, 
                  'music_id': music_id, 
	          'action': action}
	
	thread = HttpThread()
	thread.setup(url, values, callback, "INTERACT")
	thread.run()

    def login(self, username, platform, callback):
	if self.status == 'no_network':
	    callback(None)
	    return
	
	url = Global.server_ip + '/login'
	values = {'name' : username, 
                  'device': platform}
	
	thread = HttpThread()
	thread.setup(url, values, callback, "LOGIN")
	thread.run()
	
    def login_finished(self, result):	
	if result == None or result == "ERROR":
	    print "cannot login."
	    self.status = 'no_network'
	else:
	    print "login done: " + result
	    self.status = 'connected'
	
    def query_music(self, limit, offset, callback, pop = False):
	if self.status == 'no_network':
	    callback(None)
	    return
	
	url = Global.server_ip + '/list_music'
	if not pop:
	    values = {'limit' : limit, 
		      'offset': offset}
	else:
	    values = {'limit' : limit, 
 	              'offset': offset,
	               'pop': 'yes'}	    
	
	thread = HttpThread()
	thread.setup(url, values, callback, "LISTRECENT")
	thread.run()	
	
    def download_thumb(self, sid, url, callback): #
	if self.status == 'no_network':
	    callback(None, "Error")
	    return	
	values = {'sid' : sid} 
	thread = HttpThread()
	thread.setup(url, values, callback, "DOWNLOAD")
	thread.run()		
    
    def upload_music(self, png_name):   # post music, the file should come from the local folder
	print 'uploading, gid = ' + self.main.score.gid
	self.upload_uid = uid = png_name[0:len(png_name)-4]	
        if self.main.score.gid == '':
	    key_id = str(-1)
	else:
	    key_id = self.main.score.gid
	thumb_name = Global.score_folder_local + uid + ".png"
	score_name = Global.score_folder_local + uid + ".mp"
	
	if self.status == 'connected':
	    url = Global.server_ip + '/music_upload'
	    values = {'username' : self.main.username,
	              'key_id' : str(key_id), 
	              'thumb': open(thumb_name, "rb"), 
	              'score': open(score_name, "rb")}	
	    thread = HttpThread()
	    thread.setup(url, values, self.upload_complete, "UPLOADTHUMB")
	    thread.run()	    
	else:
	    print 'no upload, d/c'
    
    def upload_complete(self, data):
	if data.startswith('Upload successful. ID = '):
	    gid = data.replace('Upload successful. ID = ', '')
	    print "upload complete, gid = " + gid
	    shutil.copy(Global.score_folder_local + self.upload_uid + ".mp", Global.score_folder_download + gid +".mp")
	    shutil.copy(Global.score_folder_local + self.upload_uid + ".png", Global.score_folder_download + gid +".png")
	    print "copy to download folder as " + gid + ".mp"
	    self.main.score.gid = gid
	    self.main.activity.upload_callback()
	elif data.startswith('Update successful. ID = '):
	    gid = data.replace('Update successful. ID = ', '')
	    print "update complete, gid = " + gid
	    if self.main.score.gid != gid:
		print "gid mismatch"
	    else:
		shutil.copy(Global.score_folder_local + self.upload_uid + ".mp", Global.score_folder_download + gid +".mp")
 	        shutil.copy(Global.score_folder_local + self.upload_uid + ".png", Global.score_folder_download + gid +".png")
	        print "copy to download folder as " + gid + ".mp"
	    self.main.activity.upload_callback()
	
    def check_network(self, callback): # echo
	url = Global.server_ip + '/echo'	
	thread = HttpThread()
	thread.setup(url, None, callback, "ECHO")
	thread.run()	
	
    def check_network_finished(self, result):
	if result == None or result == "ERROR":
	    print "No Internet detected."
	    self.status = 'no_network'
	else:
	    print "Internet detected."
	    self.status = 'connected'

