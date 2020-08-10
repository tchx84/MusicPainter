from gi.repository import Gtk
from gi.repository import Gdk

from random import randrange
from math import *
import json
import filecmp
import os
import cairo
import Global

class HomeSubView(Gtk.DrawingArea):
    
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
	self.cell_div_height = 240
	
	self.cell_x0 = 96 #64
	self.cell_y0 = 75
	
	self.font = self.main.font
    
    def init_data(self):
        self.fix_button = 0
        self.toolbar_expanded = False
        self.category = 'Mine'
	
	self.page = 0
	self.page_no_items = 0
	self.page_max_items = 12
	
	self.total_pages = 0
	self.no_items = 0
	
	self.hover_cid = -1
	self.hover_icon = 'none'
	
	self.refresh_list()
	
    def set_category(self, category):
	self.category = category
	self.refresh_list()
    
    def refresh_view(self):
        self.queue_draw_area(0, 0, self.width, self.height)
	
    def refresh_list(self):
	self.page = 0
	if self.category == 'Mine':
	    self.init_my_stuff()	
	elif self.category == 'New':
	    self.init_music(False)
	elif self.category == 'Popular':
	    self.init_music(True)
    
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
                        | Gdk.EventMask.POINTER_MOTION_MASK)
                        #| Gdk.EventMask.POINTER_MOTION_HINT_MASK)
        
    def expose_event(self, widget, cr):
        
        cr.set_source_surface(self.pixmap, 0, 0)
        cr.paint()
	
	self.draw_hover_cell(cr)
	self.draw_arrows(cr)
    
        return False
        
    def configure_event(self, widget, event):
        self.width = width = widget.get_allocation().width
        self.height = height = widget.get_allocation().height
       
        self.bg_pixmap = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height) # the background layer
        self.pixmap = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height) # all layers
        
        self.prepare_bg_pixmap()
       
        cr = cairo.Context(self.pixmap)        
        cr.set_source_surface(self.bg_pixmap, 0, 0)
        cr.paint()
        
        return True
    
    def prepare_bg_pixmap(self):
	self.bg_pixmap = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.width, self.height) # the background layer
        cr = cairo.Context(self.bg_pixmap)
        cr.rectangle(0, 0, self.width, self.height)
        cr.set_source_rgb(1, 1, 1)
        cr.fill()
        
        if self.platform != "sugar-xo":
            cr.set_source_rgb(0.16, 0.16, 0.16)
            cr.rectangle(0, 0, self.width, self.top_bar_height)
            cr.fill()               
	    
	self.draw_sub(cr)

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
	iid = self.on_icon(event.x, event.y)
	if iid != 'none':
	    if iid == 'rewind' and self.page != 0:
		self.switch_page(self.page - 1)
	    elif iid == 'forward' and self.page != self.total_pages - 1:
		self.switch_page(self.page + 1)
    
    def on_mouse_up_event(self, widget, event):
        self.fix_button = 0
	cid = self.on_cell(event.x, event.y)
	if cid != -1:		    
	    if self.category == 'Mine' and self.page == 0 and cid == 0: # new piece
		self.new_score()
	    elif self.category != 'Mine':
		self.load_public_score(self.all_item_list, cid+self.page*self.page_max_items)
	    else:
		self.load_score(self.all_item_list, cid-1+self.page*self.page_max_items)
    
    def on_mouse_move_event(self, widget, event):
        x, y = event.x, event.y
        state = event.get_state()
	if not state & Gdk.ModifierType.BUTTON1_MASK: # not on click
	    cid = self.on_cell(x, y)
	    if cid != self.hover_cid:		
		t = self.hover_cid
		self.hover_cid = cid
		if t != -1:
		    (x0, y0, x1, y1) = self.get_cell_bound(t)
		    widget.queue_draw_area(x0, y0, x1-x0, y1-y0)
		if cid != -1:
		    (x0, y0, x1, y1) = self.get_cell_bound(cid)
		    widget.queue_draw_area(x0, y0, x1-x0, y1-y0)	
		    
	    iid = self.on_icon(x, y)
	    if iid != self.hover_icon:
		t = self.hover_icon
		self.hover_icon = iid
		if t != 'none':
		    (x0, y0, x1, y1) = self.get_icon_bound(t)
		    widget.queue_draw_area(x0, y0, x1-x0, y1-y0)	
		if iid != 'none':
		    (x0, y0, x1, y1) = self.get_icon_bound(iid)
		    widget.queue_draw_area(x0, y0, x1-x0, y1-y0)	
		    
        return True
        
    def toolbar_switch(self):
        self.toolbar_expanded = not self.toolbar_expanded        
	
    def init_music(self, popular):
	self.main.network.query_music(self.page_max_items, 0, self.query_finished, popular)

    def dump_list(self, dobj):
	self.no_items = dobj["count"]
	self.total_pages = (self.no_items+self.page_max_items-1)/self.page_max_items
        self.all_item_list = []
	for nobj in dobj["music_list"]:
	    if not self.check_thumb_exist(nobj["id"]): 	# to download thumb
		self.main.network.download_thumb(nobj["id"], nobj["thumb_url"], self.main.home_view.download_thumb_finished)
	    if not self.check_music_exist(nobj["id"]):  # to download music
		self.main.network.download_thumb(nobj["id"], nobj["score_url"], self.main.home_view.download_score_finished)
	    self.all_item_list.append(nobj)
	    if not self.main.home_view.like_table.has_key(nobj["id"]):
	        self.main.home_view.like_table[nobj["id"]] = False
	        self.main.network.querylike(self.main.username, nobj["id"], self.main.home_view.query_like_finished)	
	    self.main.home_view.update_music_count(nobj["id"], int(nobj["likes"]), int(nobj["play_count"]))
	self.init_page(self.page)
	
    def query_finished(self, result):
	if result == None or result == "ERROR":
	    print "error in query"
	    self.main.network.status = 'no_network'
	    return
	dobj = json.load(result)
	self.dump_list(dobj)
	   
    def init_my_stuff(self):
	self.all_item_list = self.sorted_ls(Global.score_folder_local)
	self.all_item_list = filter(lambda name: name.endswith(".png") and name.find('-')!=-1, self.all_item_list)
	#self.all_item_list = filter(lambda name: name.endswith(".png"), self.all_item_list)
	if self.platform == 'sugar-xo':
	    self.all_item_list.reverse()
	    
	self.no_items = len(self.all_item_list) + 1   # the 0th item is used to new an item	
	self.total_pages = int((self.no_items+self.page_max_items-1) / self.page_max_items)	
	self.init_my_page(0)
	
    def init_page(self, page):
	self.page = page
	self.page_item_list = []
	for obj in self.all_item_list:
	    self.page_item_list.append(obj["id"]+".png")
	self.page_no_items = len(self.page_item_list)
	
    def init_my_page(self, page):
	self.page = page
	self.page_item_list = []
	if page == 0:
	    iid = 0
	    self.page_item_list.append('NEW_PAGE')
	    while len(self.page_item_list) < self.page_max_items and iid < len(self.all_item_list):
		self.page_item_list.append(self.all_item_list[iid])
		iid = iid + 1
	else:
	    iid = page * self.page_max_items - 1
	    while len(self.page_item_list) < self.page_max_items and iid < len(self.all_item_list):
		self.page_item_list.append(self.all_item_list[iid])
		iid = iid + 1
	self.page_no_items = len(self.page_item_list)
	
    def switch_page(self, page):
	if self.page == page:
	    return
	if self.category == 'Mine':
	    self.init_my_page(page)
	else:
	    self.page = page
	    self.main.network.query_music(self.page_max_items, self.page_max_items * page, self.query_finished, self.category == 'Popular')
	self.prepare_bg_pixmap()
	
	cr = cairo.Context(self.pixmap)        
	cr.set_source_surface(self.bg_pixmap, 0, 0)
	cr.paint()		
	
	self.refresh_view()		    
	
    def sorted_ls(self, path):
        mtime = lambda f: os.stat(os.path.join(path, f)).st_mtime
        return list(sorted(os.listdir(path), key=mtime))	  

    def load_public_score(self, olist, sid):
	mid = olist[sid]["id"]
	png_name = mid + ".png"
	mp_name = mid + ".mp"	
	self.fix_button = 0
	slist = []
	for o in olist:
	    slist.append(o["id"] + ".png")
	self.main.to_detail_mode_from_home(Global.score_folder_download + mp_name, slist, sid, self.category)
    
    def load_score(self, slist, sid):
	png_name = slist[sid]
	uid = png_name[0:len(png_name)-4]
	mp_name = uid + '.mp'
	self.fix_button = 0
	self.main.to_detail_mode_from_home(Global.score_folder_local + mp_name, slist, sid, self.category)
	
    def new_score(self):
	#if self.platform == 'sugar-xo':
	    #uid = self.generate_uid()
	    #self.main.activity.create_journal()
	    #self.main.activity.update_uid(uid)	
	
	# should give warning if the current canvas has unsaved notes
	self.main.score.new_score()
	self.main.to_canvas_view('NEW_PAGE')
	
    def draw_hover_cell(self, cr):
	if self.hover_cid == -1:
	    return
	[x0, y0, x1, y1] = self.get_cell_bound(self.hover_cid)	
	cr.set_source_rgba(1, 1, 1, 0.4)
        self.create_curvy_rectangle(cr, x0, y0, self.cell_width, self.cell_height, 10)
	cr.fill()        
	
    def draw_sub(self, cr):	
	(x, y) = (self.cell_x0, self.y+self.cell_y0)
	img = cairo.ImageSurface.create_from_png(Global.home_img[self.category])
	self.draw_img(cr, img, x, y-6+Global.home_img_offset_y[self.category]-img.get_height())
	
	cr.set_source_rgb(0.16, 0.16, 0.16)
	self.set_font(cr)
	cr.set_font_size(28) 
	ex = cr.text_extents(self.category)
	cr.move_to(x+img.get_width()+8, y-ex[3]+6+Global.home_tag_offset_y[self.category])
	cr.show_text(self.category)
	
	for i in range(self.page_no_items):
	#for i in range(self.page_max_items):
	    if i >= self.page_no_items:
		self.draw_piece(cr, x+self.cell_div_width*(i%4), y+self.cell_div_height*(i/4))
	    elif self.category == 'Mine':
		self.draw_piece(cr, x+self.cell_div_width*(i%4), y+self.cell_div_height*(i/4), self.page_item_list[i])
	    else:
		self.draw_piece(cr, x+self.cell_div_width*(i%4), y+self.cell_div_height*(i/4), self.page_item_list[i], self.all_item_list[i]['likes'], self.all_item_list[i]['play_count'], self.main.home_view.like_table[self.all_item_list[i]['id']])
		
    def draw_piece(self, cr, x, y, filename = '', likes = 0, play_count = 0, like = False):
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
	    if self.category == 'Mine':
		path = Global.score_folder_local + filename
	    else:
		path = Global.score_folder_download + filename
	    img = cairo.ImageSurface.create_from_png(path)
	    cr.set_source_surface(img, x, y)
	    cr.paint()	
        
        if self.category != 'Mine':   # if a piece is uploaded, should still display the number
            offset_x = self.draw_count(cr, x, y+self.cell_height+6, 'favorite', like, likes)
	    self.draw_count(cr, x+offset_x+16, y+self.cell_height+6, 'play', False, play_count)
	
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
    
    def draw_arrows(self, cr):
	r = f = True
	if self.page == 0 or self.hover_icon == 'rewind':
	    r = False
	if self.page == self.total_pages-1 or self.hover_icon == 'forward':
	    f = False	    
	
	img = cairo.ImageSurface.create_from_png(Global.detail_img['rewind'])	
	[x0, y0, x1, y1] = self.get_icon_bound('rewind')
	cr.set_source_surface(img, x0, y0)
	cr.paint()	
	if not r:
	    cr.set_source_rgba(1, 1, 1, 0.7)
	    cr.rectangle(x0, y0, x1-x0, y1-y0)
	    cr.fill()
	
        img = cairo.ImageSurface.create_from_png(Global.detail_img['forward'])	
	[x0, y0, x1, y1] = self.get_icon_bound('forward')
	cr.set_source_surface(img, x0, y0)
	cr.paint()		
	if not f:
	    cr.set_source_rgba(1, 1, 1, 0.7)
	    cr.rectangle(x0, y0, x1-x0, y1-y0)
	    cr.fill()	    
	
    def on_icon(self, mx, my):
	[x0, y0, x1, y1] = self.get_icon_bound('rewind')
	if x0 <= mx and mx < x1 and y0 <= my and my < y1:
	    return 'rewind'
	[x0, y0, x1, y1] = self.get_icon_bound('forward')
	if x0 <= mx and mx < x1 and y0 <= my and my < y1:
	    return 'forward'	
	return 'none'		
    
    def on_cell(self, mx, my):
	for i in range(self.page_no_items):
	    [x0, y0, x1, y1] = self.get_cell_bound(i)
	    if x0 <= mx and mx < x1 and y0 <= my and my < y1:
		return i
	return -1
    
    def get_icon_bound(self, name):
	x0 = self.cell_x0 - 20 - 55
	x1 = self.cell_x0 + 3 * self.cell_div_width + self.cell_width + 20
	y = self.y + 360
	if name == 'rewind':
	    return [x0, y, x0 + 55, y + 70]
	elif name == 'forward':
	    return [x1, y, x1 + 55, y + 70]
    
    def get_cell_bound(self, i):
	x0 = self.cell_x0+self.cell_div_width*(i%4)
        y0 = self.y+self.cell_y0+self.cell_div_height*(i/4)
        x1 = x0+self.cell_width
        y1 = y0+self.cell_height
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
	    
    def no_to_c(self, n):
	if n < 10:
	    return str(n)
	else:
	    return chr(ord('a')+n-10)

    def check_music_exist(self, sid):
	return os.path.isfile(Global.score_folder_download + sid + ".mp")
    
    def check_thumb_exist(self, sid):
	return os.path.isfile(Global.score_folder_download + sid + ".png")
