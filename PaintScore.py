from random import randrange
import os
import datetime
import json
import filecmp
import Global

class PaintScore():
    def __init__(self, gwid, ghei, platform, main):
        self.width = gwid
        self.height = ghei
	self.platform = platform
	self.main = main
	
	self.init_data()
	
    def init_data(self):
	self.vol_increase = 1.05
	self.vol_decrease = 0.96
	
	self.scale_mode = 0
	self.score_shift = 0
	self.instruments = []
	self.tempo_r = 0.5
	
	self.author = ''
	self.description = ''
	self.datetime = ''
	
	self.ins = 8 # number of instruments
	
	self.title = ''
	self.description = ''
	
	#self.note_str = '' # to check unedit piece	
	self.note_map = self.zeros3(self.ins, self.width, self.height)	
	self.cut = self.zeros3(self.ins, self.width, self.height)
	self.is_edited_during_loop = 'off'
	
	self.update_jobs = []
	self.uid = ''
	self.gid = ''
	self.prev_gid = ''
		
	self.generate_scales()	
	
    def new_score(self):
	print "new_score()"
	self.clear_score()
	self.uid = self.generate_uid()
	self.author = self.main.username
	print "temp uid: " + self.uid
	if self.platform == 'sugar-xo':	    
	    self.main.activity.update_uid(self.uid)	
	self.main.canvas_view.bottom_bar.init_random_instruments()
	self.instruments = self.main.canvas_view.bottom_bar.instruments
	
    def save_score(self):
	print "save_score(), gid = " + self.gid
	if self.gid != '' and self.author != self.main.username:  # if this is downloaded from others, check if changes are made. 
	    if self.check_changes(self.gid): # change is made
		self.prev_gid = self.gid
		self.author = self.main.username
		self.gid = ''	    			    
	self.write_score(Global.score_folder_local + self.uid + ".mp")
	self.main.canvas_view.save_thumb(Global.score_folder_local + self.uid + ".png")
	return True
	
    def save_score_as(self):
	print "save_score_as(), gid = " + self.gid
	if self.gid != '' and self.author != self.main.username:
	    change = self.check_changes(self.gid)
	    if not change:
		return False
	    else:
		self.prev_gid = self.gid
		self.author = self.main.username
		self.gid = ''	    			    		
		self.write_score(Global.score_folder_local + self.uid + ".mp")
		self.main.canvas_view.save_thumb(Global.score_folder_local + self.uid + ".png")		
		return True
	else: 
	    self.uid = self.generate_uid()
	    if self.platform == 'sugar-xo':
		self.main.activity.update_uid(self.uid)	
	    self.prev_music_id = self.gid
	    self.gid = ''
	    self.write_score(Global.score_folder_local + self.uid + ".mp")
	    self.main.canvas_view.save_thumb(Global.score_folder_local + self.uid + ".png")    
	    return True
	    
    def upload_eligible(self):
	if self.gid == '':
	    return True
	if self.author == self.main.username:
	    return True
	if self.check_changes(self.gid):
	    return True
	return False
	
    def check_changes(self, prev_gid):
	scale_change = False
	tempo_change = False
	pitch_change = False
	score_change = False
	instrument_change = False
	
	stream = open(Global.score_folder_download + prev_gid + ".mp")
	d = json.load(stream)
	stream.close()
	for key in d.keys():
	    if key == 'scale':
		if self.scale_mode != d[key]:
		    scale_change = True
	    elif key == 'shift':
		if self.score_shift != d[key]:
		    pitch_change = True
	    elif key == 'tempo_sval':
		if self.tempo_r != d[key]:
		    tempo_change = True
	    elif key == 'instrument_list':
		if self.instruments != d[key]:
		    instrument_change = True		    
	    elif key == 'note_list':
		if self.encode_score_base64_string() != d[key]:
		    score_change = True
	
	if score_change:
	    return True
	if instrument_change:
	    return True
	if tempo_change or scale_change or pitch_change:
	    return True
	return False
    
    def read_journal(self, filename, uid):
	self.uid = uid
	if not os.path.isfile(Global.score_folder_local + uid + '.mp'):
	    name = self.find_duplicate(filename)
	    if name != '':
		old_uid = name[0:len(name)-3]
		print "update uid: " + old_uid + " -> " + uid
		os.rename(Global.score_folder_local + old_uid + '.mp', Global.score_folder_local + uid + '.mp')
		os.rename(Global.score_folder_local + old_uid + '.png', Global.score_folder_local + uid + '.png')
		
	self.read_score(filename)	
	
    def check_filename(self, filename):
	if filename.find('-') == -1: 
	    self.gid = filename[0:len(filename)-3]	    
    
    def read_score(self, filename, no_redraw = False):
	print "read score: " + filename
	self.check_filename(filename)
	stream = open(filename)
	d = json.load(stream)
	stream.close()
	self.read_score_dict(d)
	if not no_redraw:
	    self.main.canvas_view.redraw()
    
    def read_score_detail(self, filename):
	self.check_filename(filename)
	stream = open(filename)
	d = json.load(stream)
	stream.close()
	self.read_score_dict(d, False)	
    
    def write_score(self, filename):
	print "write score: " + filename
	stream = open(filename, 'w')
	d = self.generate_score_dict()
	json.dump(d, stream)
	stream.close()
	
    def write_journal(self, filename, uid):
	print "write journal: " + filename + ", uid = " + uid + ", prev uid = " + self.uid
	self.write_score(filename) # journal
	if uid != self.uid:
	    if not os.path.isfile(Global.score_folder_local + uid + ".mp"): # this is a new uid
		if os.path.isfile(Global.score_folder_local + self.uid + ".mp"):
		    print "remove " + self.uid + ".mp"
		    os.remove(Global.score_folder_local + self.uid + ".mp")
		if os.path.isfile(Global.score_folder_local + self.uid + ".png"):
		    os.remove(Global.score_folder_local + self.uid + ".png")
  	    print "write " + uid + ".mp"
	    self.write_score(Global.score_folder_local + uid + ".mp")
	    self.main.canvas_view.save_thumb(Global.score_folder_local + uid + ".png")
	    self.uid = uid
	    if self.main.activity.get_description() != self.description and self.main.current_view == 'detail':
		self.main.detail_view.redraw()		
	else:
	    print "consistent uid, write " + uid + ".mp"
	    self.write_score(Global.score_folder_local + uid + ".mp")
	    self.main.canvas_view.save_thumb(Global.score_folder_local + uid + ".png")	    	    	    
	    
    def sorted_ls(self, path):
        mtime = lambda f: os.stat(os.path.join(path, f)).st_mtime
        return list(sorted(os.listdir(path), key=mtime))	  
    
    def find_duplicate(self, filename):
	file_list = self.sorted_ls(Global.score_folder_local)
	file_list = filter(lambda name: name.endswith(".mp"), file_list)
	if self.platform == 'sugar-xo':
	    file_list.reverse()
	for target in file_list:
	    if filecmp.cmp(Global.score_folder_local + target, filename):
		print 'find duplicate file: ' + target
		return target
	return ''
	
    def clear_score(self):	
	self.gid = ''
	#self.uid = ''  # keep using the uid
	self.prev_gid = ''
	
	self.scale_mode = 0
	self.score_shift = 0
	self.tempo_r = 0.5
	
	self.author = ''
	self.title = ''
	self.description = ''
	self.datetime = ''		
	
	for i in range(self.width):
	    for k in range(self.ins):
		for j in range(self.height):
		    self.note_map[k][i][j] = 0
		    self.cut[k][i][j] = 0
	
    def cut_grid(self, ins, gx, gy): # has confirmed the grid is cuttable before calling
	if self.cut[ins][gx][gy] == 1:
	    self.cut[ins][gx][gy] = 0
	else:
	    self.cut[ins][gx][gy] = 1
	if gx == self.width-1:
	    self.update_jobs.append([gx, gx, gy])
	else:
	    self.update_jobs.append([gx, gx+1, gy])
	if self.main.csa.play_state == 'play' and self.main.canvas_view.bottom_bar.is_looping and self.is_edited_during_loop == 'off':
	    self.is_edited_during_loop = 'on'
	return True
		    
    def add_grid(self, ins, gx, gy):
	if self.note_map[ins][gx][gy] == 127:
	    return False
	self.note_map[ins][gx][gy] = 127
	if self.main.csa.is_non_hangable_color(ins):
	    self.cut[ins][gx][gy] = 1
	a = b = 0
	if gx-a-1 >= 0 and self.note_map[ins][gx-a-1][gy] != 0 and self.cut[ins][gx-a-1][gy] == 0:
	    a = a + 1
        if gx+b+1 < self.width and self.note_map[ins][gx+b+1][gy] != 0 and self.cut[ins][gx+b+1][gy] == 0:
	    b = b + 1	
	self.update_jobs.append([gx-a, gx+b, gy]);
	if self.main.csa.play_state == 'play' and self.main.canvas_view.bottom_bar.is_looping and self.is_edited_during_loop == 'off':
	    self.is_edited_during_loop = 'on'
	return True
    
    def erase_grid(self, ins, gx, gy, ins_only = False):
	if self.note_map[ins][gx][gy] == 0 and ins_only:
	    return
	if self.note_map[ins][gx][gy] == 0:
	    for i in range(8):
		if self.note_map[i][gx][gy] != 0:
		    break;
	    if i == 8:  # the grid is empty
		return
	else:
	    i = ins 	
	self.note_map[i][gx][gy] = 0
	self.cut[i][gx][gy] = 0
	a = b = 0
	if gx-a-1 >= 0 and self.note_map[i][gx-a-1][gy] != 0 and self.cut[i][gx-a-1][gy] == 0:
	    a = a + 1
        if gx+b+1 < self.width and self.note_map[i][gx+b+1][gy] != 0 and self.cut[i][gx+b+1][gy] == 0:
	    b = b + 1	
	self.update_jobs.append([gx-a, gx+b, gy]);
	if self.main.csa.play_state == 'play' and self.main.canvas_view.bottom_bar.is_looping and self.is_edited_during_loop == 'off':
	    self.is_edited_during_loop = 'on'
	
    def touch_grid(self, ins, gx, gy): # add when blank, erase when occupy
	if self.note_map[ins][gx][gy] == 0:
	    self.add_grid(ins, gx, gy)
	    return True
	else:
	    self.erase_grid(ins, gx, gy, True)
	    return False
	
    def increase_volume(self, gx, gy):
	return self.adjust_volume(gx, gy, self.vol_increase)
        
    def decrease_volume(self, gx, gy):
	return self.adjust_volume(gx, gy, self.vol_decrease)

    def adjust_volume(self, gx, gy, r):
	ins = self.main.canvas_view.bottom_bar.active_instrument
	if self.note_map[ins][gx][gy] == 0:
	    for i in range(8):
		if self.note_map[i][gx][gy] != 0:
		    break;
	    if i == 7 and self.note_map[i][gx][gy] == 0:  # the grid is empty
		return -1
	else:
	    i = ins
	gxa = gx
	while gxa > 0 and self.note_map[i][gxa-1][gy] != 0 and self.cut[i][gxa-1][gy] == 0:
	    gxa = gxa - 1
	gxb = gx
	while self.cut[i][gxb][gy] == 0 and gxb < self.width - 1 and self.note_map[i][gxb+1][gy] != 0:
	    gxb = gxb + 1
	for j in range(gxb-gxa+1):
	    self.note_map[i][j+gxa][gy] = (int)(1.0 * self.note_map[i][j+gxa][gy] * r)
	    if self.note_map[i][j+gxa][gy] > 255:
		self.note_map[i][j+gxa][gy] = 255
	    elif self.note_map[i][j+gxa][gy] < 25:
		self.note_map[i][j+gxa][gy] = 25		
	self.update_jobs.append([gxa, gxb, gy])
	return self.note_map[i][gxa][gy]
    
    def generate_scales(self):
	basic_major_scale = [0, 2, 4, 5, 7, 9, 11]
	basic_minor_scale = [0, 2, 3, 5, 7, 8, 11]
	basic_chinese_scale = [0, 2, 4, 7, 9]
	basic_japanese_scale = [0, 4, 5, 9, 11]
	basic_blue_scale = [0, 3, 5, 6, 7, 10]
	basic_chromatic_scale = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
	
	self.major_scale = []
	self.minor_scale = []
	self.chinese_scale = []
	self.japanese_scale = []
	self.blue_scale = []
	self.chromatic_scale = []

	for j in range(self.height):
	    i = j + 4
	    self.major_scale.append(basic_major_scale[i%7] + (i/7)*12)
	    i = j + 4
            self.minor_scale.append(basic_minor_scale[i%7] + (i/7)*12)
	    i = j + 3
            self.chinese_scale.append(basic_chinese_scale[i%5] + (i/5)*12) 
	    i = j + 2
            self.japanese_scale.append(basic_japanese_scale[i%5] + (i/5)*12)
	    i = j + 4
            self.blue_scale.append(basic_blue_scale[i%6] + (i/6)*12)
	    i = j
	    self.chromatic_scale.append(basic_chromatic_scale[i%12] + (i/12)*12)

    def get_scale_ys(self, mode):
	scale = {
	    0: [0, 2, 4, 5, 7, 9, 11], 
	    1: [0, 2, 3, 5, 7, 8, 11], 
	    2: [0, 2, 4, 7, 9], 
	    3: [0, 4, 5, 9, 11], 
	    4: [0, 3, 5, 6, 7, 10], 
	    5: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
	}
	begin_gy = self.height-4
	seq = []
	for i in range(len(scale[mode])):
	    seq.append(begin_gy-scale[mode][i])
	seq.append(begin_gy-12)
	seq.append(begin_gy-12)
	for i in range(len(scale[mode])):
	    seq.append(begin_gy-scale[mode][len(scale[mode])-1-i])	
	return seq
    
    def get_scale_pitches(self, mode):
	scale = {
	    0: [0, 2, 4, 5, 7, 9, 11], 
	    1: [0, 2, 3, 5, 7, 8, 11], 
	    2: [0, 2, 4, 7, 9], 
	    3: [0, 4, 5, 9, 11], 
	    4: [0, 3, 5, 6, 7, 10], 
	    5: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
	}
	begin = 48
	seq = []
	for i in range(len(scale[mode])):
	    seq.append(begin+scale[mode][i])
	seq.append(begin+12)
	seq.append(begin+12)
	for i in range(len(scale[mode])):
	    seq.append(begin+scale[mode][len(scale[mode])-1-i])	
	return seq

    def map_scale(self, val, mode, shift):
	options = {
	    0: 36 + self.major_scale[self.height-val-1] + shift, 
	    1: 36 + self.minor_scale[self.height-val-1] + shift, 
	    2: 36 + self.chinese_scale[self.height-val-1] + shift, 
	    3: 36 + self.japanese_scale[self.height-val-1] + shift, 
	    4: 36 + self.blue_scale[self.height-val-1] + shift, 
	    5: 48 + self.chromatic_scale[self.height-val-1] + shift
	}
	return options[mode]
    
    def drum_random(self):
	dlist = [24, 26, 28, 30, 32, 34, 36, 38, 40, 42, 44, 46, 48]
	return dlist[randrange(len(dlist))]
    
    def drum_map(self, val):	
        map = [24, 26, 28, 30, 32, 34, 36, 38, 40, 42, 44, 46, 48, 24, 26, 28, 30, 32, 34]
        return map[self.height-val-1]
    
    def get_map_pitch(self, val):    # return midi pitch number
	return self.map_scale(val, self.scale_mode, self.score_shift)
    
    def get_map_name(self, val):
	m = [3, 3, 2, 3, 2, 0]
	root_pitch = self.get_map_pitch(self.height-m[self.scale_mode]-1)
	pitch = self.get_map_pitch(val)
	letter = Global.root_map[root_pitch%12][pitch%12]
	number = int(pitch/12)-1
	return letter + str(number)		
    
    def get_map_gradient(self, val): # return 0 - 11
	return self.map_scale(val, self.scale_mode, 0) % 12
    
    def zeros3(self, n1, n2, n3):
        array = [[[0 for i in range(n3)] for j in range(n2)] for k in range(n1)]
        return array
    
    def generate_score_dict(self):
	d = {'format':'v0'}
	d['scale'] = self.scale_mode
	if self.score_shift != 0:
	    d['shift'] = self.score_shift
	d['tempo_sval'] = self.main.canvas_view.bottom_bar.tempo_r  #tempo_sval = slider value between 0-1
	d['bpm'] = self.main.csa.getTempo()
	#if self.platform == 'sugar-xo':
	if self.author == '':
	    d['author'] = self.main.username
	else:
	    d['author'] = self.author
	d['platform'] = self.platform
	now_time = datetime.datetime.now()
	d['date'] = now_time.strftime("%Y-%m-%d %H:%M")
	if self.title != '':
	    d['title'] = self.title
	if self.description != '':
	    d['description'] = self.description
	if self.gid != '':
	    d['gid'] = self.gid
	d['instrument_list'] = self.main.canvas_view.bottom_bar.instruments
	d['note_list'] = self.encode_score_base64_string()
	d['prev_gid'] = self.prev_gid
	
	return d
    
    def read_score_dict(self, d, on_canvas = True):	
	self.clear_score()
	for key in d.keys():
	    if key == 'format':
		format_type = d[key]
	    elif key == 'scale':
		self.scale_mode = d[key]
	    elif key == 'shift':
		self.score_shift = d[key]
	    elif key == 'tempo_sval':
		self.tempo_r = d[key]
		if on_canvas:
		    self.main.canvas_view.bottom_bar.tempo_r = d[key]
		    if self.main.hasCSound:
			self.main.csa.setTempo()
	    elif key == 'title':
		self.title = d[key]
		if on_canvas and self.platform == 'sugar-xo':		    
		    self.main.activity.update_title(self.title)
	    elif key == 'description':
		self.description = d[key]
		if self.platform == 'sugar-xo':
		    buf = self.main.activity.desc_btn._text_view.get_buffer()
		    buf.set_text(self.description)		    
	    elif key == 'instrument_list':
		ins = d[key]
		self.instruments = ins
		if on_canvas:
		    self.main.canvas_view.bottom_bar.instruments = ins
		    self.main.instrument_view.instruments = ins
	    elif key == 'note_list':
		#self.note_str = d[key]
		#self.parse_note_str(self.note_str)		
		self.parse_note_str(d[key])
	    elif key == 'author':
		self.author = d[key]
	    elif key == 'date':
		self.datetime = d[key]
	    elif key == 'gid':
		self.gid = d[key]
	    elif key == 'prev_gid':
		self.prev_gid = d[key]
		
    def parse_note_str(self, s):
	str_len = len(s)
	n_tokens = int(str_len/5)
	for i in range(n_tokens):
	    sub = s[5*i:5*i+5]
	    [st, du, vol, ins, pitch] = self.decode_note_base64_string(sub)
	    if st != 0 and self.note_map[ins][st-1][pitch] != 0:
		self.cut[ins][st-1][pitch] = 1
	    for j in range(du):		
		self.note_map[ins][st+j][pitch] = vol		
    
    def c_to_64(self, c):
	if ord('A') <= ord(c) and ord(c) <= ord('Z'):
	    return ord(c)-ord('A')  # 0 - 25
	if ord('a') <= ord(c) and ord(c) <= ord('z'):
	    return 26+ord(c)-ord('a')
	if ord('0') <= ord(c) and ord(c) <= ord('9'):
	    return 52+ord(c)-ord('0')	
	if c == '+':
	    return 62
	if c == '/':
	    return 63
	
    def no_to_c(self, n):
	if n < 26:
	    return chr(ord('A')+n)
	if n < 52:
	    return chr(ord('a')+n-26)
	if n < 62:
	    return chr(ord('0')+n-52)
	if n == 62:
	    return '+'
	if n == 63:
	    return '/'
		
    def encode_note_base64_string(self, st, du, vol, ins, pitch):
	# st 0:63, du 1:64, vol 0:255, ins 0:7, pitch 0:18
	string = self.no_to_c(st) + self.no_to_c(du-1) + self.no_to_c(pitch) + self.no_to_c(vol%64) + self.no_to_c(ins + int(vol/64) * 8)
	return string
	
    def decode_note_base64_string(self, string):
	st = self.c_to_64(string[0])
	du = self.c_to_64(string[1])+1
	pitch = self.c_to_64(string[2])
	vol = self.c_to_64(string[3]) + int(self.c_to_64(string[4])/8)*64
	ins = self.c_to_64(string[4])%8
	#print str(st) + " " + str(du) + " " + str(pitch) + " " + str(vol) + " " + str(ins)
	return [st, du, vol, ins, pitch]
    
    def encode_score_base64_string(self):
	string = ''
	for i in range(self.width):
	    for k in range(self.ins):
		for j in range(self.height):
		    if self.note_map[k][i][j] != 0 and (i == 0 or (self.note_map[k][i-1][j] == 0 or self.cut[k][i-1][j] == 1)):			
			du = 1
			while self.cut[k][i+du-1][j] == 0 and i+du < self.width and self.note_map[k][i+du][j] != 0:
			    du = du + 1
			string = string + self.encode_note_base64_string(i, du, self.note_map[k][i][j], k, j)
	return string
			
	
    def generate_uid(self):  # imitate the uid generated by sugar
	uid = ''
	for i in range(8):
	    uid = uid + self.no_to_c2(randrange(16))
	uid = uid + '-'
	for i in range(4):
	    uid = uid + self.no_to_c2(randrange(16))
	uid = uid + '-'
	for i in range(4):
	    uid = uid + self.no_to_c2(randrange(16))
	uid = uid + '-'
	for i in range(4):
	    uid = uid + self.no_to_c2(randrange(16))
	uid = uid + '-'
	for i in range(12):
	    uid = uid + self.no_to_c2(randrange(16))	    
	return uid
    
    def no_to_c2(self, n):
	if n < 10:
	    return str(n)
	else:
	    return chr(ord('a')+n-10)

