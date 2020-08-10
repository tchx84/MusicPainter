from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject

from math import *
import json
import os
import filecmp
import cairo
import Global

class HomeView(Gtk.DrawingArea):
    
    def __init__(self, width, height, platform, main):
        self.width = width
        self.height = height
        self.platform = platform
        self.main = main
        
        self.init_graphics()
        self.init_ui()                
        self.init_data()
        
        Gtk.DrawingArea.__init__(self)                

    def init_graphics(self):
        if self.platform == "sugar-xo":
            self.top_bar_height = 0
            self.height = self.height - 75
        else:
            self.top_bar_height = 75
        
        self.y = self.top_bar_height
        
        self.cell_width = 224
        self.cell_height = 152
        self.cell_div_width = 260 # 224+36
        
        self.categories = ['Popular', 'New', 'Mine']
        self.cell_x0 = 64
        self.cell_y = [75, 345, 615]
	
	self.row_offset_x = [0, 0, 0]
	
	self.no_items_row = [-1, -1, -1]
	self.max_no_item = 6
	self.timer_interval = 25
	
	self.init_speed_rate = 0.75
	self.speed_decay = 0.80
        
        self.font = self.main.font
	self.cat_bound = []
    
    def init_data(self):
        self.fix_button = 0
	self.is_update_timer_on = False
	
	self.drag_sum_d = 0
	self.drag_row = -1
	
	self.row_slide_weight = [1, 1, 1, 2, 2, 2, 4, 4, 4, 8, 8, 8]
	self.row_state = ['rest', 'rest', 'rest']
	self.last_row_slide = [-1, -1, -1]
	self.row_dock_x = [-1, -1, -1]
	self.row_slide_buffer = [[], [], []]
	
        self.toolbar_expanded = False
	self.hover_cid = (-1, -1)
	self.select_cid = (-1, -1)
	self.hover_cat = -1	
	
	self.clickPending = "off"
	self.click_threshold = 300 # tap < 300 ms	
	self.move_threshold = 50   # 50 pixels = move
	
	self.load_cache()
	#self.like_table = {}
	
	self.likes_table = {}
	self.play_count_table = {}
	
	#self.recent_list = []
	#self.popular_list = []
	
	self.refresh_list()
	
    def refresh_view(self):
        self.queue_draw_area(0, 0, self.width, self.height)
	
    def refresh_list(self):
	self.init_query()
	self.init_my_stuff()	
	self.select_cid = (-1, -1)
    
    def init_ui(self):
        Gtk.DrawingArea.__init__(self)

        self.set_size_request(self.width, self.height)

        # Event signals
        self.connect("draw", self.expose_event)
        self.connect("configure_event", self.configure_event)
        self.connect("enter_notify_event", self.enter_notify_event)	
        self.connect("leave_notify_event", self.leave_notify_event)
        self.connect("motion_notify_event", self.on_mouse_move_event)
        self.connect("button_press_event", self.on_mouse_down_event)
        self.connect("button_release_event", self.on_mouse_up_event)

        self.set_events(Gdk.EventMask.EXPOSURE_MASK
	                | Gdk.EventMask.ENTER_NOTIFY_MASK	                
                        | Gdk.EventMask.LEAVE_NOTIFY_MASK
                        | Gdk.EventMask.BUTTON_PRESS_MASK
                        | Gdk.EventMask.BUTTON_RELEASE_MASK
                        | Gdk.EventMask.TOUCH_MASK
                        | Gdk.EventMask.POINTER_MOTION_MASK
                        | Gdk.EventMask.POINTER_MOTION_HINT_MASK)
        
    def expose_event(self, widget, cr):
        
        if self.platform == "sugar-xo" and self.toolbar_expanded:
            cr.set_source_surface(self.pixmap, 0, -75)
        else:
            cr.set_source_surface(self.pixmap, 0, 0)
        cr.paint()
		
	cr.rectangle(self.cell_x0-2, self.y, self.width-self.cell_x0+2, self.height) # apply the bound
	cr.clip()        	
	
	self.draw_hover_category(cr)
	self.draw_hover_cell(cr)
	self.draw_selected_cell(cr)
    
        return False
        
    def configure_event(self, widget, event):
        width = widget.get_allocation().width
        height = widget.get_allocation().height
       
	self.row_pixmap = []        
	
        self.pixmap = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height) # all layers
	
        self.prepare_row_pixmaps()
       
        cr = cairo.Context(self.pixmap)        
	if len(self.cat_bound) == 0: # need to initialize
	    self.init_category_bound(cr)        
	
	self.draw_bg(cr)
	self.draw_home(cr)
	
        return True
    
    def prepare_row_pixmap(self, r):
	lw = self.width - self.cell_x0 - 3*self.cell_div_width - self.cell_width
	(rw, rh) = (self.cell_div_width*(self.max_no_item-1)+self.cell_width+lw+2, self.cell_height+36)
	row_pixmap = cairo.ImageSurface(cairo.FORMAT_ARGB32, rw, rh)
	cr = cairo.Context(row_pixmap)
	self.redraw_row(cr, r)
	if len(self.row_pixmap) == 3:
	    self.row_pixmap[r] = row_pixmap
	else:
	    self.row_pixmap.append(row_pixmap)	
    
    def prepare_row_pixmaps(self):
	self.row_pixmap = []
	for r in range(3):
	    self.prepare_row_pixmap(r)

    def enter_notify_event(self, widget, event):
        return
    
    def leave_notify_event(self, widget, event):
        return

    def on_mouse_down_event(self, widget, event):
        self.fix_button = self.fix_button + 1
        if self.fix_button != 1:
            return
        if event.button != 1:
            return True 
        cid = self.on_cell(event.x, event.y)
	#if self.select_cid != -1 and self.select_cid == cid:
	if cid[0] != -1:
	    #if cid[0] == 2 and cid[1] < len(self.my_list):
	    n1 = n2 = n3 = self.max_no_item	    
	    if len(self.recent_list) == self.max_no_item:
		n1 = n1 + 1
	    if len(self.popular_list) == self.max_no_item:
		n2 = n2 + 1
	    if self.no_items_row[2] == self.max_no_item:
		n3 = n3 + 1	    
	    if cid[0] == 0 and cid[1] < n1 or cid[0] == 1 and cid[1] < n2 or cid[0] == 2 and cid[1] < n3:
		self.clickTimer = GObject.timeout_add(self.click_threshold, self.clickTimeout)
		self.clickPending = 'wait'
		(self.start_mx, self.start_my) = (event.x, event.y)
		self.drag_row = self.on_row(event.x, event.y)
		self.row_state[self.drag_row] = 'drag_on'
		self.last_drag_x = event.x
		if self.select_cid != cid:
		    t = self.select_cid
		    self.select_cid = cid
		    if t != (-1, -1):
			(x0, y0, x1, y1) = self.get_cell_bound(t[0], t[1])
			widget.queue_draw_area(x0-2, y0-2, x1-x0+4, y1-y0+4)
		    if cid != (-1, -1):
			(x0, y0, x1, y1) = self.get_cell_bound(cid[0], cid[1])
			widget.queue_draw_area(x0-2, y0-2, x1-x0+4, y1-y0+4)			    		
		return
        if self.select_cid != cid:
	    t = self.select_cid
	    self.select_cid = cid
	    if t != (-1, -1):
		(x0, y0, x1, y1) = self.get_cell_bound(t[0], t[1])
		widget.queue_draw_area(x0-2, y0-2, x1-x0+4, y1-y0+4)
	    if cid != (-1, -1):
		(x0, y0, x1, y1) = self.get_cell_bound(cid[0], cid[1])
		widget.queue_draw_area(x0-2, y0-2, x1-x0+4, y1-y0+4)			    

	row = self.on_row(event.x, event.y)
	if row != -1:
	    self.drag_row = row
	    self.row_state[row] = 'drag_on'
            self.last_drag_x = event.x
        return True       
    
    def on_mouse_up_event(self, widget, event):
        self.fix_button = 0	
	if self.main.canvas_view.wait_mouse_up:
	    self.main.canvas_view.wait_mouse_up = False
	if self.clickPending != 'off':
	    GObject.source_remove(self.clickTimer)
	if self.clickPending == 'wait':   # tap
	    if self.select_cid[0] == 0:
		if self.select_cid[1] == self.max_no_item:
		    self.main.to_homesub_mode_from_home(self.categories[self.select_cid[0]])
		else:
		    self.load_public_score(self.recent_list, self.select_cid[1], self.categories[self.select_cid[0]])
	    elif self.select_cid[0] == 1:
		if self.select_cid[1] == self.max_no_item:
		    self.main.to_homesub_mode_from_home(self.categories[self.select_cid[0]])
		else:		
		    self.load_public_score(self.popular_list, self.select_cid[1], self.categories[self.select_cid[0]])
	    elif self.select_cid[0] == 2:
		if self.select_cid[1] == 0:
		    self.new_score()
		elif self.select_cid[1] == self.max_no_item:
		    self.main.to_homesub_mode_from_home(self.categories[self.select_cid[0]])
		else:
		    self.load_score(self.my_list, self.select_cid[1], self.categories[self.select_cid[0]])	    
	    self.clickPending = "off"		
	if self.drag_row != -1:
	    if self.drag_sum_d != 0: # clear the remaining move
		self.add_move_record(self.drag_row, self.drag_sum_d)
		self.update_row_offset(self.drag_row, self.drag_sum_d)
		self.drag_sum_d = 0	    
	    self.row_state[self.drag_row] = 'drag_off'
	    self.drag_row = -1
	cat = self.on_category(event.x, event.y)
	if cat != -1: # erase the highlight before switching view
	    self.hover_cat = -1;
	    (x0, y0, x1, y1) = self.get_category_bound(self.hover_cat)
	    widget.queue_draw_area(x0, y0, x1-x0, y1-y0)	    
	    self.main.to_homesub_mode_from_home(self.categories[cat])
	    return
    
    def on_mouse_move_event(self, widget, event):
        x, y = event.x, event.y
        state = event.get_state()
	if not state & Gdk.ModifierType.BUTTON1_MASK: # not on click
	    cid = self.on_cell(x, y)
	    if cid != self.hover_cid:		
		t = self.hover_cid
		self.hover_cid = cid
		if t != (-1, -1):
		    (x0, y0, x1, y1) = self.get_cell_bound(t[0], t[1])
		    widget.queue_draw_area(x0, y0, x1-x0, y1-y0)
		if cid != (-1, -1):
		    (x0, y0, x1, y1) = self.get_cell_bound(cid[0], cid[1])
		    widget.queue_draw_area(x0, y0, x1-x0, y1-y0)		
	    cat = self.on_category(x, y)
	    if cat != self.hover_cat:
		t = self.hover_cat
		self.hover_cat = cat		
		if t != -1:
		    (x0, y0, x1, y1) = self.get_category_bound(t)
		    widget.queue_draw_area(x0, y0, x1-x0, y1-y0)
		if cat != -1:
		    (x0, y0, x1, y1) = self.get_category_bound(cat)
 		    widget.queue_draw_area(x0, y0, x1-x0, y1-y0)		    		    
	else:                                         # on click
	    if self.clickPending != "off":
		if sqrt((x - self.start_mx)*(x - self.start_mx) + (y - self.start_my)*(y - self.start_my)) > self.move_threshold:
		    self.clickPending = "move"	    
	    if self.drag_row == -1:
		return
	    if not self.is_update_timer_on:
		self.is_update_timer_on = True
		#print "m" + str(self.last_drag_x-x)
		self.add_move_record(self.drag_row, self.last_drag_x-x)
		self.update_row_offset(self.drag_row, self.last_drag_x-x)
		self.updateTimer = GObject.timeout_add(self.timer_interval, self.updateTimeout)
	    else:
		self.drag_sum_d = self.drag_sum_d + self.last_drag_x - x
	    self.last_drag_x = x
	    
    def clickTimeout(self):
        GObject.source_remove(self.clickTimer)
        self.clickPending = "timeout"
	
    def check_music_exist(self, sid):
	return os.path.isfile(Global.score_folder_download + sid + ".mp")
    
    def check_thumb_exist(self, sid):
	return os.path.isfile(Global.score_folder_download + sid + ".png")
    
    def update_music_count(self, music_id, likes, play_count):
        self.likes_table[music_id] = likes
	self.play_count_table[music_id] = play_count
	
    def save_cache(self):
	filename = Global.cache_folder + 'like_table.txt'
	stream = open(filename, 'w')
	json.dump(self.like_table, stream)
	stream.close()
	
	filename = Global.cache_folder + 'recent.txt'
	stream = open(filename, 'w')
	json.dump(self.recent_list, stream)
	stream.close()

	filename = Global.cache_folder + 'popular.txt'
	stream = open(filename, 'w')
	json.dump(self.popular_list, stream)
	stream.close()
	
    def load_cache(self):
	filename = Global.cache_folder + 'like_table.txt'
	try:
	    stream = open(filename)
	    self.like_table = json.load(stream)
	    stream.close()
	except:
	    self.like_table = {}
	    
        filename = Global.cache_folder + 'recent.txt'
	try:
	    stream = open(filename)
	    self.recent_list = json.load(stream)
	    self.no_items_row[1] = len(self.recent_list)
	    stream.close()
	except:
	    self.recent_list = []
	
        filename = Global.cache_folder + 'popular.txt'
	try:
	    stream = open(filename)
	    self.popular_list = json.load(stream)
	    self.no_items_row[0] = len(self.popular_list)
	    stream.close()
	except:
	    self.popular_list = []
	    
    def dump_recent_list(self, dobj):
	if dobj["count"] > self.max_no_item:
	    self.no_items_row[0] = self.max_no_item
	else:
	    self.no_items_row[0] = dobj["count"]
	self.recent_list = [] 
	for nobj in dobj["music_list"]:
	    if not self.check_music_exist(nobj["id"]):  # to download music
		self.main.network.download_thumb(nobj["id"], nobj["score_url"], self.download_score_finished)
 	    if not self.check_thumb_exist(nobj["id"]): 	# to download thumb
		self.main.network.download_thumb(nobj["id"], nobj["thumb_url"], self.download_thumb_finished)
		self.like_table[nobj["id"]] = False
	    elif not self.like_table.has_key(nobj["id"]):  # if thumb exist, query like
	        self.like_table[nobj["id"]] = False        # init
	        self.main.network.querylike(self.main.username, nobj["id"], self.query_like_finished)
	    self.update_music_count(nobj["id"], int(nobj["likes"]), int(nobj["play_count"]))
	    self.recent_list.append(nobj)
	#self.prepare_row_pixmap(1)
	
    def update_view_after_query(self):
	self.pixmap = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.width, self.height) # all layers
		
	cr = cairo.Context(self.pixmap)        
		
	self.draw_bg(cr)
	self.draw_home(cr)	

	self.refresh_view()     
	#print "update_view"
    
    def dump_popular_list(self, dobj):
	if dobj["count"] > self.max_no_item:
	    self.no_items_row[1] = self.max_no_item
	else:
	    self.no_items_row[1] = dobj["count"]
        self.popular_list = []
	for nobj in dobj["music_list"]:
	    if not self.check_music_exist(nobj["id"]):  # to download music
		self.main.network.download_thumb(nobj["id"], nobj["score_url"], self.download_score_finished)
	    if not self.check_thumb_exist(nobj["id"]): 	# to download thumb
		self.main.network.download_thumb(nobj["id"], nobj["thumb_url"], self.download_thumb_finished)
		self.like_table[nobj["id"]] = False
	    elif not self.like_table.has_key(nobj["id"]):  # if thumb exist, query like
		self.like_table[nobj["id"]] = False        # init
	        self.main.network.querylike(self.main.username, nobj["id"], self.query_like_finished)	    
	    self.update_music_count(nobj["id"], int(nobj["likes"]), int(nobj["play_count"]))
	    self.popular_list.append(nobj)
	#prepare_row_pixmaps
        #self.prepare_row_pixmap(0)
	    
    def query_like_finished(self, music_id, like):
	self.like_table[music_id] = like	
#	if like:
#	    self.like_table[music_id] = True
	
    def download_thumb_finished(self, sid, result):
	if result == None or result == "ERROR" or sid == None:
	    print "error in fetching file"
	    self.main.network.status = 'no_network'
	    return
	stream = open(Global.score_folder_download + sid + '.png', "wb")
	stream.write(result)
	stream.close()

    def download_score_finished(self, sid, result):
	if result == None or result == "ERROR" or sid == None:
	    print "error in fetching file"
	    self.main.network.status = 'no_network'
	    return
	stream = open(Global.score_folder_download + sid + '.mp', "w")
	stream.write(result)
	stream.close()
	print "score id(" + sid + ") fetched."
	
    def query_popular_finished(self, result):
	#self.timer_step = self.timer_step + 1
	#print self.timer_step
	if result == None or result == "ERROR":
	    print "error in query"
	    self.main.network.status = 'no_network'
	    return
	dobj = json.load(result)
	self.dump_popular_list(dobj)
	
    def query_recent_finished(self, result):	
	#self.timer_step = self.timer_step + 1
	#print self.timer_step
	if result == None or result == "ERROR":
	    print "error in query"
	    self.main.network.status = 'no_network'
	    return
	dobj = json.load(result)
	self.dump_recent_list(dobj)

    def timer_tick(self):
	#print "tick: (" + str(self.timer_step) + ")"
	if self.timer_step == 0:
	    self.main.network.query_music(self.max_no_item, 0, self.query_popular_finished)	
	    self.timer_step = self.timer_step + 1
	    #print self.timer_step
	elif self.timer_step == 2:
	    self.main.network.query_music(self.max_no_item, 0, self.query_recent_finished, True)
	    self.timer_step = self.timer_step + 1
	    #print self.timer_step
	elif self.timer_step >= 4:
	    GObject.source_remove(self.timer)
	    self.prepare_row_pixmaps()
	    self.update_view_after_query()	    
	    #print "timer removed"
	return True
    
    def init_query(self):	
	#self.timer_step = 0
	#self.timer = GObject.timeout_add(250, self.timer_tick)			
	#print "timer added"
	
	self.main.network.query_music(self.max_no_item, 0, self.query_popular_finished)
	self.main.network.query_music(self.max_no_item, 0, self.query_recent_finished, True)	
    
    def init_my_stuff(self):
	self.my_list = self.sorted_ls(Global.score_folder_local)
	self.my_list = filter(lambda name: name.endswith(".png") and name.find('-')!=-1, self.my_list)
	if self.platform == 'sugar-xo':
	    self.my_list.reverse()
	self.my_list.insert(0, 'NEW_PAGE')
	self.no_items_row[2] = len(self.my_list)  # the 0th item is used to new an item	
	if self.no_items_row[2] > self.max_no_item:
	    self.no_items_row[2] = self.max_no_item		
	
    def sorted_ls(self, path):
        mtime = lambda f: os.stat(os.path.join(path, f)).st_mtime
        return list(sorted(os.listdir(path), key=mtime))	  
    
    def load_public_score(self, olist, sid, category):
	mid = olist[sid]["id"]
	png_name = mid + ".png"
	mp_name = mid + ".mp"	
	self.fix_button = 0
	slist = []
	for o in olist:
	    slist.append(o["id"] + ".png")
	self.main.to_detail_mode_from_home(Global.score_folder_download + mp_name, slist, sid, category)
        
    def load_score(self, slist, sid, category):
	png_name = slist[sid]
	print png_name
	uid = png_name[0:len(png_name)-4]
	mp_name = uid + '.mp'
	self.fix_button = 0
	self.main.to_detail_mode_from_home(Global.score_folder_local + mp_name, slist, sid, category)
	
    def new_score(self):
	# should give warning if the current canvas has unsaved notes
	self.main.score.new_score()
	self.main.to_canvas_view('NEW_PAGE')
	
    def add_move_record(self, r, d):
	if len(self.row_slide_buffer[r]) == 12:
	    self.row_slide_buffer[r].pop(0)
	self.row_slide_buffer[r].append(d)
	
    def get_avg_move(self, r):
	s = 0
	j = 0
	for i in range(len(self.row_slide_buffer[r])):
	    d = self.row_slide_buffer[r][i]
	    s = s + d * self.row_slide_weight[i]
	    j = j + self.row_slide_weight[i]
	if j == 0:
	    return 0
	return s / j
    
    def get_slide_distance(self, speed):
	slide_distance = 0
	while speed >= 1:
	    slide_distance = slide_distance + speed
	    speed = speed * self.speed_decay
	return slide_distance
    
    def get_dock_x(self, i, speed):
	distance = self.get_slide_distance(speed)
	x0 = self.row_offset_x[i]+distance
	lid = int(x0 / self.cell_div_width)
	if lid < 0:
	    lid = 0
	if lid > self.no_items_row[i]-4:
	    lid = self.no_items_row[i]-4
	x_left = lid * self.cell_div_width
	rid = lid+1
	if rid > self.no_items_row[i]-4:
	    rid = self.no_items_row[i]-4		    
	x_right = rid * self.cell_div_width
	if abs(self.row_offset_x[i]-x_left) < abs(self.row_offset_x[i]-x_right): # dock toward left
	    return x_left
	else:
	    return x_right
	    
    def updateTimeout(self):
	d = [0, 0, 0]
	if self.drag_sum_d != 0: # move from user
	    self.add_move_record(self.drag_row, self.drag_sum_d)
	    d[self.drag_row] = self.drag_sum_d
	    self.drag_sum_d = 0
	    
	for i in range(3):
	    if self.row_state[i] == 'rest':
		continue
	    if self.row_state[i] == 'drag_off':
		speed = self.init_speed_rate * self.get_avg_move(i)
		self.row_slide_buffer[i] = [] # clear buffer
		self.row_state[i] = 'slide'
		d[i] = d[i] + speed
		self.last_row_slide[i] = speed
	    elif self.row_state[i] == 'slide':
		speed = self.speed_decay * self.last_row_slide[i]
		if abs(speed) <= 10:
		    self.row_dock_x[i] = self.get_dock_x(i, speed)
		    self.row_state[i] = 'dock'			
		#    x_left = 
		d[i] = d[i] + speed
		self.last_row_slide[i] = speed
	    elif self.row_state[i] == 'dock':
		diff = self.row_dock_x[i] - self.row_offset_x[i]
		if diff > 36:
		    speed = 8
		elif diff >= 16:
		    speed = 6
		elif diff >= 10:
		    speed = 4
		elif diff >= 4:
		    speed = 2
		elif diff > 0:
		    speed = 1				    
		elif diff < -36:
		    speed = -8
		elif diff <= -16:
		    speed = -6
		elif diff <= -10:
		    speed = -4
		elif diff <= -4:
		    speed = -2
		else:
		    speed = -1	
		d[i] = d[i] + speed
		
	    if abs(d[i]) >= 1:
		self.update_row_offset(i, d[i])
	    if self.row_state[i] == 'dock' and self.row_offset_x[i] == self.row_dock_x[i]:
		self.row_state[i] = 'rest'
	
	if self.row_state[0] == 'rest' and self.row_state[1] == 'rest' and self.row_state[2] == 'rest':
	    GObject.source_remove(self.updateTimer)
	    self.is_update_timer_on = False
	else:
	    self.updateTimer = GObject.timeout_add(self.timer_interval, self.updateTimeout)
	            
    def toolbar_switch(self):
        self.toolbar_expanded = not self.toolbar_expanded  
	
    def update_row_offset(self, r, d):
	#print "update_row_offset: " + str(d)
	t = self.row_offset_x[r]
	d = int(d)
	self.row_offset_x[r] = self.row_offset_x[r] + d
	if self.row_offset_x[r] > self.cell_div_width * (self.no_items_row[r] - 4):
	    self.row_offset_x[r] = self.cell_div_width * (self.no_items_row[r] - 4)
        if self.row_offset_x[r] < 0:
	    self.row_offset_x[r] = 0
	if t == self.row_offset_x[r]:
	    #print "return"
	    return
	
	cr = cairo.Context(self.pixmap)
	cr.rectangle(self.cell_x0-2, self.y+self.cell_y[r]-2, self.width-self.cell_x0+2, self.cell_height+4+36) # apply the bound
	cr.clip()		
	self.draw_row(cr, r, self.cell_x0, self.y+self.cell_y[r], self.row_offset_x[r])
	self.queue_draw_area(self.cell_x0-2, self.y+self.cell_y[r]-2, self.width-self.cell_x0+2, self.cell_height+4+36)
	
    def draw_hover_category(self, cr):
	if self.hover_cat == -1:
	    return
	
	r = self.hover_cat
	self.draw_category(cr, r, self.categories[r], self.cell_x0, self.y+self.cell_y[r], self.row_offset_x[r])	
	    
    def draw_hover_cell(self, cr):
	if self.hover_cid == (-1, -1):
	    return
	[x0, y0, x1, y1] = self.get_cell_bound(self.hover_cid[0], self.hover_cid[1])	
	cr.set_source_rgba(1, 1, 1, 0.4)
	if self.toolbar_expanded:
	    self.create_curvy_rectangle(cr, x0, y0-75, self.cell_width, self.cell_height, 10)
	else:
	    self.create_curvy_rectangle(cr, x0, y0, self.cell_width, self.cell_height, 10)
	cr.fill()
	
    def draw_selected_cell(self, cr):
	if self.select_cid == (-1, -1):
	    return
	[x0, y0, x1, y1] = self.get_cell_bound(self.select_cid[0], self.select_cid[1])
	cr.set_line_width(3)
	cr.set_source_rgb(1, 0.4, 0.4)
	if self.toolbar_expanded:
	    self.create_curvy_rectangle(cr, x0, y0-75, x1-x0, y1-y0, 10)
	else:
	    self.create_curvy_rectangle(cr, x0, y0, x1-x0, y1-y0, 10)
	cr.stroke()
        
    def draw_home(self, cr):	
	cr.rectangle(self.cell_x0, self.y, self.width-self.cell_x0, self.height) # apply the bound
	cr.clip()
	
	for r in range(3):
	    self.draw_category(cr, r, self.categories[r], self.cell_x0, self.y+self.cell_y[r], self.row_offset_x[r])
	    
    def draw_bg(self, cr):
	cr.rectangle(0, 0, self.width, self.height)
	cr.set_source_rgb(1, 1, 1)
	cr.fill()
	
	if self.platform != "sugar-xo":
	    cr.set_source_rgb(0.16, 0.16, 0.16)
	    cr.rectangle(0, 0, self.width, self.top_bar_height)
	    cr.fill()               
        
    def draw_category(self, cr, r, category, x, y, offset_x):
        img = cairo.ImageSurface.create_from_png(Global.home_img[category])              # draw icon
        self.draw_img(cr, img, x, y-6+Global.home_img_offset_y[category]-img.get_height())
                
        cr.set_source_rgb(0.16, 0.16, 0.16)                                              # draw text 
        self.set_font(cr)
        cr.set_font_size(28) 
        ex = cr.text_extents(category)
        cr.move_to(x+img.get_width()+8, y-ex[3]+6+Global.home_tag_offset_y[category])
        cr.show_text(category)
	
	if self.hover_cat != -1 and self.categories[self.hover_cat] == category:         
	    [x0, y0, x1, y1] = self.get_category_bound(self.hover_cat)
	    cr.set_source_rgba(1, 1, 1, 0.5)
	    cr.rectangle(x0, y0, x1-x0, y1-y0)
	    cr.fill()	    
	
        self.draw_row(cr, r, x, y, offset_x)                                             # draw row
	
    def draw_row(self, cr, r, x, y, offset_x):
	cr.set_source_surface(self.row_pixmap[r], x-offset_x-2, y)
	cr.paint()
        
    def redraw_row(self, cr, r):
	#print "redraw row: " + str(r)
	lw = self.width - self.cell_x0 - 3*self.cell_div_width - self.cell_width
	(rw, rh) = (self.cell_div_width*(self.no_items_row[r]-1)+self.cell_width+lw+2, self.cell_height+36)
	cr.set_source_rgb(1, 1, 1)
	cr.rectangle(0, 0, rw, rh)
	cr.fill()
	if r == 0:
	    if len(self.recent_list) == 0:
		for i in range(5):
		    self.draw_piece(cr, r, i, self.cell_div_width*i+2, 0)
	    else:
		for i in range(len(self.recent_list)):
		    if self.check_thumb_exist(self.recent_list[i]['id']):
			filename = Global.score_folder_download + self.recent_list[i]['id'] + '.png'
			self.draw_piece(cr, r, i, self.cell_div_width*i+2, 0, filename, self.recent_list[i]['likes'], self.recent_list[i]['play_count'], self.like_table[self.recent_list[i]['id']])	    
		    else:
			self.draw_piece(cr, r, i, self.cell_div_width*i+2, 0)
		if len(self.recent_list) == self.max_no_item:
		    self.draw_more_button(cr, self.cell_div_width*len(self.recent_list)+2, 0)
	elif r == 1:
	    if len(self.popular_list) == 0:
		for i in range(5):
		    self.draw_piece(cr, r, i, self.cell_div_width*i+2, 0)
	    else:
		for i in range(len(self.popular_list)):
		    if self.check_thumb_exist(self.popular_list[i]['id']):
			filename = Global.score_folder_download + self.popular_list[i]['id'] + '.png'
			self.draw_piece(cr, r, i, self.cell_div_width*i+2, 0, filename, self.popular_list[i]['likes'], self.popular_list[i]['play_count'], self.like_table[self.popular_list[i]['id']])	    
		    else:		    
			self.draw_piece(cr, r, i, self.cell_div_width*i+2, 0)
		if len(self.popular_list) == self.max_no_item:
		    self.draw_more_button(cr, self.cell_div_width*len(self.popular_list)+2, 0)		
	elif r == 2:
	    #for i in range(len(self.my_list)):
	    for i in range(self.no_items_row[2]):	
		if self.my_list[i] == 'NEW_PAGE':
		    filename = self.my_list[i]
		else:
		    filename = Global.score_folder_local + self.my_list[i]
		self.draw_piece(cr, r, i, self.cell_div_width*i+2, 0, filename, -1, -1)
	    if self.no_items_row[2] == self.max_no_item:
		self.draw_more_button(cr, self.cell_div_width*self.no_items_row[2]+2, 0)
	else:
	    for i in range(self.no_items_row[r]):
		self.draw_piece(cr, r, i, self.cell_div_width*i+2, 0)
	
    def draw_more_button(self, cr, x, y):
	self.create_curvy_rectangle(cr, x, y + self.cell_height / 3, self.cell_width * 0.4, self.cell_height / 3, 10)	
	cr.set_source_rgb(0.88, 0.88, 0.88)
	cr.fill()	    	
	
	cr.set_source_rgb(0.4, 0.4, 0.4)
	self.set_font(cr)
	cr.set_font_size(18)                
	ex = cr.text_extents(str('More'))
	cr.move_to(x+self.cell_width/5-ex[2]/2, y+self.cell_height/2+8)
	cr.show_text(str('More'))		
	
    def draw_piece(self, cr, r, c, x, y, filename = '', favorite = 0, play = 0, like = False):
	if filename == '' or filename == 'NEW_PAGE':
	    self.create_curvy_rectangle(cr, x, y, self.cell_width, self.cell_height, 10)	
	    cr.set_source_rgb(0.88, 0.88, 0.88)
	    cr.fill()	    
	    if filename == 'NEW_PAGE':
		cr.set_source_rgb(0.4, 0.4, 0.4)
		self.set_font(cr)
		cr.set_font_size(28)                
		ex = cr.text_extents(str('Create new'))
		cr.move_to(x+self.cell_width/2-ex[2]/2, y+self.cell_height/2+8)
		cr.show_text(str('Create new'))	    
	else:
	    img = cairo.ImageSurface.create_from_png(filename)
	    cr.set_source_surface(img, x, y)
	    cr.paint()	
        
        if favorite != -1 and play != -1:
	    offset_x = self.draw_count(cr, x, y+self.cell_height+6, 'favorite', like, favorite)
	    self.draw_count(cr, x+offset_x+16, y+self.cell_height+6, 'play', False, play)
	
    def mask_img(self, cr, img, x, y):
	cr.mask_surface(img, x, y)
	cr.fill()
	
    def draw_img(self, cr, img, x, y):
        cr.set_source_surface(img, x, y)
        cr.paint()        
        
    def draw_count(self, cr, x, y, ty, highlight, cnt):        
        img = cairo.ImageSurface.create_from_png(Global.home_img[ty])
	if ty == 'favorite' and highlight:
	    cr.set_source_rgb(0.84, 0, 0)
	    self.mask_img(cr, img, x, y)
	else:
	    self.draw_img(cr, img, x, y)
        
        cr.set_source_rgb(0.4, 0.4, 0.4)
        self.set_font(cr)
        cr.set_font_size(20)                
        ex = cr.text_extents(str(cnt))
        cr.move_to(x+img.get_width()+3, y+ex[3]+5)
        cr.show_text(str(cnt))
        
        return img.get_width()+4+ex[2]
    
    def on_cell_row(self, r, mx, my, rx, ry, roff_x): 
	if my < ry or my >= ry + self.cell_height or mx < self.cell_x0:
	    return -1
	n = self.no_items_row[r]
	for i in range(n):
	    if rx+self.cell_div_width*i-roff_x <= mx and mx < rx+self.cell_div_width*i+self.cell_width-roff_x:
		return i	
	if n == self.max_no_item and rx+self.cell_div_width*n-roff_x <= mx and mx < rx+self.cell_div_width*n+self.cell_width*0.4-roff_x and ry + self.cell_height/3 <= my and my < ry + 2 * self.cell_height/3:
	    return n  # more button
	return -1
    
    def on_row(self, mx, my):
	for r in range(3):
	    if self.y+self.cell_y[r] <= my and my < self.y+self.cell_y[r]+self.cell_height:
		return r
	return -1
    
    def on_cell(self, mx, my):
	for r in range(3):
	    i = self.on_cell_row(r, mx, my, self.cell_x0, self.y+self.cell_y[r], self.row_offset_x[r]) # row 1
	    if i != -1:
		return (r, i)
	return (-1, -1)
    
    def init_category_bound(self, cr):
	self.cat_bound = []
	for i in range(3):
	    c = self.categories[i]
	    x = x = self.cell_x0
	    y = self.y + self.cell_y[i] - 6 + Global.home_img_offset_y[c]-Global.home_img_size[c][1]
	    
	    self.set_font(cr)
	    cr.set_font_size(28) 
	    ex = cr.text_extents(c)		    
	    
	    w = Global.home_img_size[c][0]+8+ex[2]
	    h = Global.home_img_size[c][1]	    
	    #print str(x) + "," + str(y) + "," + str(x+w) + "," + str(y+h)
	    self.cat_bound.append([x, y, x+w, y+h])
	    
    def get_category_bound(self, i):
	return self.cat_bound[i]

    def on_category(self, mx, my): # return if cursor on category icon or label, otherwise, return -1
	for i in range(3):
	    b = self.get_category_bound(i)
	    if b[0] <= mx and mx < b[2] and b[1] <= my and my < b[3]:
		return i
	return -1
	#x = self.cell_x0
	#for i in range(3):
	    #c = self.categories[i]
	    #y = self.y + self.cell_y[i]
	    #icon_y = y - 6 + Global.home_img_offset_y[c]-Global.home_img_size[c][1]
	    #if x <= mx and mx < x + Global.home_img_size[c][0] and icon_y <= my and my < icon_y + Global.home_img_size[c][1]:   # cursor on icon
		#return i
	    #self.set_font(cr)
	    #cr.set_font_size(28) 
	    #ex = cr.text_extents(c)	    
	    #text_x = x + Global.home_img_size[c][0]+8
	    #text_y = y-ex[3]+6+Global.home_tag_offset_y[c]
	    #if text_x <= mx and mx < text_x + ex[2] and text_y <= my and my < text_y + ex[3]:
		#return i
	#return -1    
    
    def get_cell_bound(self, r, c):	
	if c < self.no_items_row[r]:
	    x0 = self.cell_x0+self.cell_div_width*c-self.row_offset_x[r]
	    y0 = self.y+self.cell_y[r]
	    x1 = self.cell_x0+self.cell_div_width*c-self.row_offset_x[r]+self.cell_width
	    y1 = self.y+self.cell_y[r]+self.cell_height
	else:
	    x0 = self.cell_x0+self.cell_div_width*c-self.row_offset_x[r]
	    y0 = self.y+self.cell_y[r]+self.cell_height/3
	    x1 = self.cell_x0+self.cell_div_width*c-self.row_offset_x[r]+0.4*self.cell_width
	    y1 = self.y+self.cell_y[r]+2*self.cell_height/3
	return (x0, y0, x1, y1)
	        
    def create_curvy_rectangle(self, cr, x0, y0, w, h, r):
        x1 = x0 + w
        y1 = y0 + h        
        cr.move_to(x0, y0+r)
        cr.arc(x0+r, y0+r, r, pi, 1.5*pi)
        cr.line_to(x1-r, y0)
        cr.arc(x1-r, y0+r, r, 1.5*pi, 2*pi)
        cr.line_to(x1, y1-r)
        cr.arc(x1-r, y1-r, r, 0, 0.5*pi)
        cr.line_to(x0+r, y1)
        cr.arc(x0+r, y1-r, r, 0.5*pi, 1.0*pi)
        cr.close_path()        

    def set_font(self, cr):
	if self.platform == 'sugar-xo':
	    cr.set_font_face(self.font)
	else:
	    cr.select_font_face(self.font, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)




	    