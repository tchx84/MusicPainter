from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject

from PaintScore import *
from math import *
import cairo

import os
import shutil

class DetailView(Gtk.DrawingArea):
    
    def __init__(self, width, height, gwid, ghei, platform, main):
        self.width = width
        self.height = height
        self.gwid = gwid
        self.ghei = ghei
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
	self.y_offset = 0
        
        self.canvas_x, self.canvas_y = (130, 106)  # 106 # 156
        self.canvas_width, self.canvas_height = (768, 455)
        self.unit_w, self.unit_h = (1.0 * self.canvas_width / self.gwid, 1.0 * (self.canvas_height+1) / self.ghei)
    
	self.scale_block_width = 57
	self.scale_block_height = 57
	
	self.font = self.main.font
	
    def init_data(self):
	self.score = PaintScore(self.gwid, self.ghei, self.platform, self.main)
	
        self.fix_button = 0
        self.toolbar_expanded = False                        
	self.hover_icon = 'none'
	self.hover_canvas = False
	self.has_list = False
	self.list_category = ''
	self.is_favorite = False
		
	self.box_message = ''
	self.is_msg_box_visible = False
	
	self.play_count = 0
	self.favorite_count = 0
	
	self.highlight_gx = -1
	
	self.tooltip_threshold = 640 # ms
	
	self.tooltip_target = 'none'
	self.tooltip_state = -1
	self.tooltip_cx = -1
	
	self.show_tooltip = 'none'
	self.tooltip_bound = [-1, -1, -1, -1]
	
	self.category = ''
    
    def refresh_view(self):
        self.queue_draw_area(0, 0, self.width, self.height)
    
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
        
        cr.set_source_surface(self.pixmap, 0, self.y_offset)
        cr.paint()
	
	if self.main.csa.play_state == 'play':
	    self.draw_highlight_line(cr)
	else:
	    self.draw_play(cr)	

	if self.show_tooltip != 'none':
	    self.draw_tooltip(cr)
	    
	if self.is_msg_box_visible:
	    self.draw_msg_box(cr)
	        
        return False
        
    def configure_event(self, widget, event):
        width = widget.get_allocation().width
        height = widget.get_allocation().height
       
        self.score_pixmap = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.canvas_width, self.canvas_height) # the score layer
        self.pixmap = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height) # all layers
        
        self.prepare_pixmap()
       
        #cr = cairo.Context(self.pixmap)        
        #cr.set_source_surface(self.bg_pixmap, 0, 0)
        #cr.paint()
        
        return True
    
    def redraw(self):
	self.prepare_pixmap()
	self.refresh_view()
    
    def prepare_pixmap(self):
        cr = cairo.Context(self.pixmap)
        cr.rectangle(0, 0, self.width, self.height)
        cr.set_source_rgb(1, 1, 1)
        cr.fill()
        
        if self.platform != "sugar-xo":
            cr.set_source_rgb(0.16, 0.16, 0.16)
            cr.rectangle(0, 0, self.width, self.top_bar_height)
            cr.fill()       
            
        self.prepare_score_pixmap()
	self.draw_info(cr)
        
	self.create_curvy_rectangle(cr, self.canvas_x, self.y + self.canvas_y, self.canvas_width, self.canvas_height, 10)
	cr.clip()
        cr.set_source_surface(self.score_pixmap, self.canvas_x, self.y + self.canvas_y)
	cr.paint()	
	
    def draw_highlight(self, gx):
	if self.highlight_gx == gx:
	    return
	
	t = self.highlight_gx
	self.highlight_gx = gx
	if t != -1:
	    self.queue_draw_area(self.canvas_x+t*self.unit_w, self.canvas_y, self.unit_w, self.canvas_height)
	if gx != -1:
	    self.queue_draw_area(self.canvas_x+gx*self.unit_w, self.canvas_y, self.unit_w, self.canvas_height)
	else:
	    self.queue_draw_area(415, self.y + 175, 240, 240)
	
    def draw_highlight_line(self, cr):
	cr.set_antialias(cairo.ANTIALIAS_NONE)
	cr.set_source_rgba(1, 1, 1, 0.7)
	i = self.highlight_gx
	cr.rectangle(self.canvas_x+i*self.unit_w, self.canvas_y+self.y_offset, self.unit_w, self.canvas_height)
	cr.fill()	
	
    def draw_play(self, cr):
	r = 12
	cr.move_to(415, self.y+self.y_offset + 213)
	cr.line_to(415, self.y+self.y_offset + 453)
	cr.line_to(655, self.y+self.y_offset + 333)
	cr.close_path()
	if not self.hover_canvas:
	    cr.set_source_rgba(1, 1, 1, 0.7)
	else:
	    cr.set_source_rgba(1, 1, 1, 0.55)
	cr.fill();
	
	#cr.arc(x0+r, y0+r, r, pi, 1.5*pi)	
	
    def prepare_score_pixmap(self):
	cr = cairo.Context(self.score_pixmap)
	for j in range(self.ghei):
	    g = self.get_gradient(j)
	    cr.set_source_rgb(g, g, g)
	    cr.rectangle(0, self.unit_h * j, self.unit_w*self.gwid, self.unit_h-1)
	    cr.fill()
	
	for ins in range(8):
	    for j in range(self.ghei):
		for i in range(self.gwid):
		    if self.score.note_map[ins][i][j] != 0 and (i == 0 or self.score.note_map[ins][i-1][j] == 0 or self.score.cut[ins][i-1][j] == 1):
			du = 1
			while self.score.cut[ins][i+du-1][j] == 0 and i+du < self.gwid and self.score.note_map[ins][i+du][j] != 0:
			    du = du + 1
			vol = self.score.note_map[ins][i][j]
			if vol >= 128:
			    t = pow(1.0*vol/128, 0.82)
			    cr.set_source_rgba(Global.get_color_red_float(ins)/t, Global.get_color_green_float(ins)/t, Global.get_color_blue_float(ins)/t, 0.7)
			else:
			    t = pow(1.0*vol/128, 1.18)
			    cr.set_source_rgba(1 + t*(Global.get_color_red_float(ins)-1), 1 + t*(Global.get_color_green_float(ins)-1), 1 + t*(Global.get_color_blue_float(ins)-1), 0.7)
			self.create_curvy_rectangle(cr, self.unit_w*i, self.unit_h*j, self.unit_w*du, self.unit_h-1, 2)
			cr.fill()	
	
	self.draw_scale(cr, self.canvas_width - self.scale_block_width, 0)	
	
    def enter_notify_event(self, widget, event):
        return
    
    def leave_notify_event(self, widget, event):
	self.handle_tooltip()

    def on_mouse_down_event(self, widget, event):
        self.fix_button = self.fix_button + 1
        if self.fix_button != 1:
            return
	if self.is_msg_box_visible:
	    return True
	x, y = event.x, event.y - self.y_offset
        if event.button != 1:
            return True      
	self.handle_tooltip()
	if self.is_on_canvas(x, y):
	    self.play()
	cid = self.is_on_icon(x, y)
	if cid == 'rewind':
	    self.rewind()
	elif cid == 'forward':
	    self.forward()
	elif cid == 'favorite':
	    self.favorite()
	elif cid == 'play':
	    self.play()
	    
    def clear_highlight(self, widget, cid):
	self.hover_icon = 'none'
	cr = cairo.Context(self.pixmap)
	self.draw_icon_1(cr, cid)
	(x0, y0, x1, y1) = self.get_icon_bound(cid)
	widget.queue_draw_area(x0, y0+self.y_offset, x1-x0, y1-y0)	    	
    
    def on_mouse_up_event(self, widget, event):
	x, y = event.x, event.y - self.y_offset
        self.fix_button = 0
	if self.is_msg_box_visible:
	    self.is_msg_box_visible = False
	    self.main.activity.msg_box_callback()
	    return	
	self.handle_tooltip()
	cid = self.is_on_icon(x, y)
	if cid == 'edit':
	    self.clear_highlight(widget, cid)    	    
	    if self.has_list:
		self.edit(self.slist[self.sid])
	    else:
		#self.main.activity.to_canvas_mode(widget)
		self.main.to_detail_mode_from_sugar()
	elif cid == 'delete':
	    self.clear_highlight(widget, cid)    
	    self.hover_icon = 'none'
	    cr = cairo.Context(self.pixmap)
	    self.draw_icon_1(cr, cid)
	    (x0, y0, x1, y1) = self.get_icon_bound(cid)
	    widget.queue_draw_area(x0, y0+self.y_offset, x1-x0, y1-y0)	    
	    
	    if self.has_list:
	        self.delete(self.slist[self.sid])
	    else:
		self.delete(self.main.score.uid + '.png')
	elif cid == 'upload':
	    if self.has_list:
		self.main.network.upload_music(self.slist[self.sid])
	    else:
		self.main.network.upload_music(self.main.score.uid)
    
    def on_mouse_move_event(self, widget, event):
        x, y = event.x, event.y - self.y_offset
        state = event.get_state()
	if self.is_msg_box_visible:
	    return True
	if not state & Gdk.ModifierType.BUTTON1_MASK: # not on click
	    oc = self.is_on_canvas(x, y)
	    if self.hover_canvas != oc:
		self.hover_canvas = oc
		widget.queue_draw_area(415, self.y+175+self.y_offset, 260, 260)
	    cid = self.is_on_icon(x, y)
	    if cid != self.hover_icon:			
		t = self.hover_icon
		self.hover_icon = cid
		if t != 'none':
		    cr = cairo.Context(self.pixmap)
		    self.draw_icon_1(cr, t)
		    (x0, y0, x1, y1) = self.get_icon_bound(t)
		    widget.queue_draw_area(x0, y0+self.y_offset, x1-x0, y1-y0)
		if cid != 'none':
		    cr = cairo.Context(self.pixmap)
		    self.draw_icon_1(cr, cid)
		    (x0, y0, x1, y1) = self.get_icon_bound(cid)
		    widget.queue_draw_area(x0, y0+self.y_offset, x1-x0, y1-y0)
	    if cid == 'edit':
		self.handle_tooltip_move('Edit')
	    elif cid == 'delete':
		self.handle_tooltip_move('Delete')
	    elif cid == 'upload':
	        self.handle_tooltip_move('Share')
	    else:
		self.handle_tooltip_move('none')
	return True
    
    def set_toolbar_expanded(self, flag):
        self.toolbar_expanded = flag
	if self.toolbar_expanded:
	    self.y_offset = 0 # -75
	else:
	    self.y_offset = 0
	    
    def show_message_box(self, msg):
	self.box_message = msg
	self.is_msg_box_visible = True
	b = self.get_msg_box_bound()
	self.queue_draw_area(b[0], b[1], b[2], b[3])
        
    def init_score(self, filename, slist, sid, category):	
	self.music_id = filename[filename.rfind('/')+1:-3]
	if self.main.home_view.like_table.has_key(self.music_id):
	    self.is_favorite = self.main.home_view.like_table[self.music_id]
	else:
	    self.is_favorite = False
	if self.main.home_view.likes_table.has_key(self.music_id):
	    self.favorite_count = int(self.main.home_view.likes_table[self.music_id])
	else:
	    self.favorite_count = -1
	if self.main.home_view.play_count_table.has_key(self.music_id):
	    self.play_count = int(self.main.home_view.play_count_table[self.music_id])
	else:
	    self.play_count = -1
        self.score.read_score_detail(filename)
	self.slist = slist # this is a list of png files
	self.sid = sid
	self.has_list = True	
	self.category = category
        
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
	
    def get_gradient(self, row):
	level = 0.10
	return 1.0 - level * (self.score.get_map_gradient(row)+3) / 12
	
    def set_font(self, cr, style = 'normal'):
	if self.platform == 'sugar-xo':
	    cr.set_font_face(self.font)	    
	else:
	    if style == 'normal':
		cr.select_font_face(self.font, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
	    elif style == 'italic':
	        cr.select_font_face(self.font, cairo.FONT_SLANT_ITALIC, cairo.FONT_WEIGHT_NORMAL)
	    elif style == 'bold':
		cr.select_font_face(self.font, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
		
    def draw_icon_1(self, cr, name):
	(x0, y0, x1, y1) = self.get_icon_bound(name)
	if name == 'favorite':
	    #self.draw_count(cr, x0, y0, name, self.hover_icon == name or self.is_favorite, self.favorite_count)
	    self.draw_count(cr, x0, y0, name, self.hover_icon == name, self.favorite_count)
	elif name == 'play':
	    self.draw_count(cr, x0, y0, name, False, self.play_count)
	else:
	    self.draw_icon(cr, name, x0, y0)
	    
    def draw_info(self, cr):	
	for icon in Global.detail_icons:
	    if not self.has_list and (icon == 'rewind' or icon == 'forward'):
		continue
	    if icon == 'delete' and self.category != 'Mine' and self.score.author != self.main.username and self.main.username != 'wuhsi': 
		continue
	    self.draw_icon_1(cr, icon)	
	self.draw_text_info(cr)

    def draw_text_info(self, cr):
	img = cairo.ImageSurface.create_from_png(Global.detail_img['avatar'])
        cr.set_source_surface(img, 135 - 10, self.y + 16)
	cr.paint()

	cr.set_font_size(22) 	
	cr.set_source_rgb(0.231, 0.349, 0.596)        # draw text 
	w = self.draw_text(cr, self.score.author, 200, self.y + 48, False, 'bold') + 8
	cr.set_font_size(20) 	
	cr.set_source_rgb(0.32, 0.32, 0.32)        # draw text 
	w = w + self.draw_text(cr, "created", 200 + w, self.y + 48, False) + 8
	cr.set_font_size(22) 	
	cr.set_source_rgb(0.16, 0.16, 0.16)        # draw text 
	w = w + self.draw_text(cr, '\"' + self.score.title + '\"', 200 + w, self.y + 48, False) + 8
	
	#self.draw_text(cr, self.score.datetime, 200, self.y + 78, False)
	cr.set_font_size(20) 	
	cr.set_source_rgb(0.32, 0.32, 0.32)        # draw text 
	self.draw_text(cr, self.get_date_string(self.score.datetime), 200, self.y + 78, False)
	#self.draw_text(cr, "2 days ago, USA", 200, self.y + 78, False)
	
	cr.set_font_size(28)
	cr.set_source_rgb(0.16, 0.16, 0.16)        # draw text 
	w = self.draw_text(cr, 'Story', 135, self.y+self.canvas_y+self.canvas_height+42, False) + 16	
	self.draw_story(cr, w)		
	
	self.draw_instruments(cr, 135, self.y + 732)
	
    def draw_story(self, cr, w):
	cr.set_font_size(20) 	
	cr.set_source_rgb(0.16, 0.16, 0.16)        # draw text 
	text = self.score.description
	if text == '':
	    text = 'Add your story here'
	    cr.set_source_rgb(0.5, 0.5, 0.5)        # draw text 	    
	#text = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Ut porttitor velit sed ultrices tincidunt. Phasellus imperdiet neque nec mollis dictum. Nullam consectetur imperdiet hendrerit. Proin eget ipsum ut magna ultrices feugiat. Praesent consectetur dignissim dui, sed lacinia turpis luctus non. "
	self.draw_paragraph(cr, text, 135, self.y+self.canvas_y+self.canvas_height+42, 36, w, self.canvas_width)
		
    def draw_paragraph(self, cr, text, x, y, div, first_line_offset, width):
	words = text.split()
	cnt = len(words)
	if cnt == 0:
	    return
	
	self.set_font(cr)
	lcnt = 0
	line = ''
	for i in range(cnt):
	    ex = cr.text_extents(line + ' ' + words[i])
	    if (lcnt == 0 and ex[2] + first_line_offset > width) or ex[2] > width: # to output line
		if lcnt == 0:
		    cr.move_to(x + first_line_offset, y + lcnt*div)
		else:
		    cr.move_to(x, y + lcnt*div)
		cr.show_text(line)
		lcnt = lcnt + 1
		if lcnt % 2 == 0:
		    line = words[i];
		else:
		    line = ' ' + words[i];
	    else:
		line = line + ' ' + words[i]	    	
	if line != '':
	    if lcnt == 0:
		cr.move_to(x + first_line_offset, y + lcnt*div)
	    else:
		cr.move_to(x, y + lcnt*div)	    
	    cr.show_text(line)

    def draw_scale(self, cr, x0, y0):
#	y0 = y0 - 22
	i = self.score.scale_mode
        cr.set_source_rgb(0.6, 0.6, 0.6)
        self.create_curvy_rectangle(cr, x0, y0, self.scale_block_width, self.scale_block_height, 12)
        cr.fill()
        ys = self.main.score.get_scale_ys(i)
        l = len(ys)
        uw = 1.0 * (self.scale_block_width - 6 - 6) / (l-1)
	uh = 3
	cr.set_source_rgb(0.8, 0.8, 0.8)
        for j in range(l):
            if ys[j] != -1:
                cr.rectangle(uw*j+x0+3, y0+ys[j]*uh, 6, 6)
                cr.fill()
    
    def draw_instruments(self, cr, x, y):
	cnt = 0
	for ins in range(8):
	    if not self.is_instrument_used(ins):
		continue
	    label = self.score.instruments[ins]
	    img = Global.get_img_sm_label(label)
	    cr.set_source_surface(cairo.ImageSurface.create_from_png(img), x + cnt * 46, y)
	    cr.paint()
	    cnt = cnt + 1
	
    def draw_count(self, cr, x, y, name, highlight, cnt): 
	if cnt == -1:
	    return
	wid = self.draw_icon(cr, name, x, y)
	
	cr.set_source_rgb(1, 1, 1)
	cr.rectangle(x+wid+7, y, 100, 34)
	cr.fill()
        
        cr.set_source_rgb(0.4, 0.4, 0.4)
        self.set_font(cr)
        cr.set_font_size(28)
        ex = cr.text_extents(str(cnt))
        cr.move_to(x+wid+7, y+ex[3]+6)
        cr.show_text(str(cnt))        

    def draw_text(self, cr, st, x, y, align_right, style = 'normal'):
	self.set_font(cr, style)
	ex = cr.text_extents(st)
	if align_right:
	    cr.move_to(x - ex[2], y)
	else:
	    cr.move_to(x, y)
	cr.show_text(st)
	return ex[2]
    
    def draw_icon(self, cr, name, x, y):
	if name == 'favorite' and self.is_favorite:
	    img = cairo.ImageSurface.create_from_png(Global.detail_img['favorited'])
	else:
	    img = cairo.ImageSurface.create_from_png(Global.detail_img[name])
	self.draw_img(cr, img, x, y)
	if self.hover_icon == name or name == 'rewind' and self.sid == 0 or name == 'forward' and self.sid == len(self.slist)-1:
	    [x0, y0, x1, y1] = self.get_icon_bound(name)
	    cr.rectangle(x0, y0, x1-x0, y1-y0)
	    cr.set_source_rgba(1, 1, 1, 0.7)
	    cr.fill()
	return img.get_width()
    
    def draw_img(self, cr, img, x, y):
        cr.set_source_surface(img, x, y)
        cr.paint()
	
    def is_on_canvas(self, mx, my):
	[x0, y0, x1, y1] = self.get_icon_bound('canvas')
	return x0 <= mx and mx < x1 and y0 <= my and my < y1
	
    def is_on_icon(self, mx, my):
	for icon in Global.detail_icons:
	    if not self.has_list and (icon == 'rewind' or icon == 'forward'):
		continue
	    if icon == 'play' and self.play_count == -1:
		continue
	    if icon == 'favorite' and self.favorite_count == -1:
		continue 
	    if icon == 'delete' and self.category != 'Mine' and self.score.author != self.main.username and self.main.username != 'wuhsi': 
		continue
	    [x0, y0, x1, y1] = self.get_icon_bound(icon)
	    if x0 <= mx and mx < x1 and y0 <= my and my < y1:
		return icon
	return 'none'
	
    def get_icon_bound(self, name):
	if name == 'play':
	    return [self.canvas_x + self.canvas_width + 36, self.y + 200, self.canvas_x + self.canvas_width + 36 + 38, self.y + 200 + 34]
	elif name == 'favorite':
	    return [self.canvas_x + self.canvas_width + 36, self.y + 248, self.canvas_x + self.canvas_width + 36 + 38, self.y + 248 + 34]
	elif name == 'edit':
	    return [self.canvas_x + self.canvas_width + 36, self.y + 80, self.canvas_x + self.canvas_width + 36 + 70, self.y + 80 + 80]
	elif name == 'delete':
	    return [self.canvas_x + self.canvas_width + 36 + 76, self.y + 80 - 3, self.canvas_x + self.canvas_width + 36 + 76 + 70, self.y + 80 + 80 - 3]
	elif name == 'upload':
	    return [self.canvas_x + self.canvas_width + 36 + 76 + 76, self.y + 80 - 3, self.canvas_x + self.canvas_width + 36 + 76 + 76 + 70, self.y + 80 + 80 - 3]	
	elif name == 'rewind':
	    return [45, self.y + 475, 45 + 55, self.y + 475 + 70]
	elif name == 'forward':
	    return [self.canvas_x + self.canvas_width + 30, self.y + 475, self.canvas_x + self.canvas_width + 30 + 55, self.y + 475 + 70]
	elif name == 'canvas':
	    return [self.canvas_x, self.y+self.canvas_y, self.canvas_x+self.canvas_width, self.canvas_y+self.y+self.canvas_height]
	else:
	    print "unidentify icon: " + str(name)
	    return [0, 0, 0, 0]
	
    def handle_tooltip(self):
	if self.tooltip_state == 'wait':
	    GObject.source_remove(self.tooltip_timer)
	if self.tooltip_state != 'none':
	    self.tooltip_state = 'none'        
	    self.tooltip_target = ''
	    self.update_tooltip('none', self.tooltip_cx)    
	    
    def handle_tooltip_move(self, item):
	if item != 'none' and self.tooltip_target != item:
	    self.tooltip_target = item
	    if item == 'Edit':
		self.tooltip_cx = self.canvas_x + self.canvas_width + 36 + 32
	    elif item == 'Delete':
		self.tooltip_cx = self.canvas_x + self.canvas_width + 36 + 76 + 35
	    elif item == 'Share':
		self.tooltip_cx = self.canvas_x + self.canvas_width + 36 + 76 + 76 + 35	    
	    if self.tooltip_state == 'none':
		self.tooltip_state = 'wait'
		self.tooltip_timer = GObject.timeout_add(self.tooltip_threshold, self.tooltip_show)
	    elif self.tooltip_state == 'wait':
		GObject.source_remove(self.tooltip_timer)
		self.tooltip_timer = GObject.timeout_add(self.tooltip_threshold, self.tooltip_show)                
	    elif self.tooltip_state == 'show':
		self.update_tooltip(self.tooltip_target, self.tooltip_cx)        
	elif item == 'none':
	    self.handle_tooltip()		

    def tooltip_show(self):        
        GObject.source_remove(self.tooltip_timer)
        self.tooltip_state = 'show'
        self.update_tooltip(self.tooltip_target, self.tooltip_cx)    
		
    def update_tooltip(self, tip, cx):
	if tip == 'none' and self.show_tooltip != 'none':
	    b = self.tooltip_bound
	    self.queue_draw_area(b[0], b[1], b[2], b[3])
	    self.show_tooltip = 'none'
	elif tip != 'none' and self.show_tooltip != tip:
	    if self.show_tooltip != 'none':
		self.show_tooltip = tip
		b = self.tooltip_bound
	        self.queue_draw_area(b[0], b[1], b[2], b[3])		
	    self.show_tooltip = tip
	    b = self.get_tooltip_bound(tip, cx)  # calculate bound	  	    
	    self.tooltip_bound = b
	    self.queue_draw_area(b[0], b[1], b[2], b[3])	
	    
    def get_tooltip_bound(self, tip, cx):
	cr = cairo.Context(self.pixmap) 
	self.set_font(cr)
	cr.set_font_size(24)	    
	ex = cr.text_extents(str(tip))
        b = [cx-ex[2]/2-14, self.y + self.y_offset + 80 + 80, ex[2]+28, 40]
	return b
    
    def get_msg_box_bound(self):
	if len(self.box_message) <= 20:
	    x = self.width/3
	    w = self.width/3
	else:
	    x = self.width/4
 	    w = self.width/2
	    
	y = self.height*3/7 + self.y_offset
	h = self.height/7	    
	return [x, y, w, h]
    
    def draw_msg_box(self, cr):
	b = self.get_msg_box_bound()	
	cr.set_source_rgb(0.88, 0.88, 0.88)
	cr.rectangle(b[0], b[1], b[2], b[3])		
	cr.fill()
	
	cr.set_source_rgb(0.12, 0.12, 0.12)
	cr.rectangle(b[0]+3, b[1]+3, b[2]-6, b[3]-6)		
	cr.fill()
	
	cr.set_source_rgb(0, 0, 0)
	cr.rectangle(b[0], b[1], b[2], b[3])		
	cr.stroke()
	
	cr.set_source_rgb(1, 1, 1)  # set up font
	self.set_font(cr)
	cr.set_font_size(24)                
	
	ex = cr.text_extents(str(self.box_message))
	cr.move_to(b[0]+b[2]/2-ex[2]/2, b[1]+b[3]/2+ex[3]/2)
	cr.show_text(str(self.box_message))	  
	
    def draw_tooltip(self, cr):	
	b = self.tooltip_bound
	cr.set_source_rgb(0, 0, 0)
	cr.rectangle(b[0], b[1], b[2], b[3])		
	cr.fill()
	
	cr.set_source_rgb(1, 1, 1)  # set up font
	self.set_font(cr)
	cr.set_font_size(24)                
	
	ex = cr.text_extents(str(self.show_tooltip))
	cr.move_to(b[0]+b[2]/2-ex[2]/2, b[1]+b[3]-12)
	cr.show_text(str(self.show_tooltip))	    	
	    	
    def load_from_list(self, sid):
	self.sid = sid
	png_name = self.slist[sid]
	uid = png_name[0:len(png_name)-4]
	mp_name = uid + '.mp'
	if self.category == 'Mine':
            self.init_score(Global.score_folder_local + mp_name, self.slist, sid, self.category)
	else:
	    self.init_score(Global.score_folder_download + mp_name, self.slist, sid, self.category)
	self.redraw()	
	
    def delete_local_score(self, png_name):
	# to do: if gid exists, and the user is the author, ask if he/she wants to unshare the file
	# if so, do delete_server_score using the gid	
	print "delete_local_score(" + png_name + ")"
	mid = png_name[0:len(png_name)-4]
	mp_name = mid + '.mp'
	if os.path.isfile(Global.score_folder_local + png_name):
	    os.remove(Global.score_folder_local + png_name)
	if os.path.isfile(Global.score_folder_local + mp_name):
	    os.remove(Global.score_folder_local + mp_name)	   
	if not self.has_list:
	    self.main.score.clear_score()
	    self.main.to_detail_mode_from_sugar()
	else:
	    if mid == self.main.score.uid:
		self.main.score.clear_score()
	    self.main.go_home()
	
    def delete_server_score(self, png_name):
	print "delete_server_score(" + png_name + ")"
	self.main.network.interact(self.main.username, self.music_id, 'delete', self.delete_callback)  # call server to mark the file as inactive
		
	gid = png_name[0:len(png_name)-4]   # delete file from download folder
	mp_name = gid + '.mp'
	if os.path.isfile(Global.score_folder_download + png_name):
	    os.remove(Global.score_folder_download + png_name)
	if os.path.isfile(Global.score_folder_download + mp_name):
	    os.remove(Global.score_folder_download + mp_name)	    	
	
	# to do: if local file exists, delete gid
	filename = self.find_local_file_by_gid(gid)
	if filename != None:
	    self.remove_score_gid(filename)
    
    def delete(self, png_name):
	if self.category == 'Popular' or self.category == 'New':
	    self.delete_server_score(png_name)
	elif self.category == 'Mine':
	    self.delete_local_score(png_name)
	    
    def get_score_gid(self, filename):
	stream = open(filename)
	d = json.load(stream)
	stream.close()
	for key in d.keys():
	    if key == 'gid':
		return d[key]
	return None
    
    def get_score_author(self, filename):
	stream = open(filename)
	d = json.load(stream)
	stream.close()
	for key in d.keys():
	    if key == 'author':
		return d[key]
	return None    
    
    def remove_score_gid(self, filename):
	stream = open(filename)
	d = json.load(stream)
	stream.close()
	
	if not d.has_key('gid'):
	    return
	gid = d.pop('gid')
	if self.score.gid == gid:
	    self.score.gid = ''
	if self.music_id == gid:
	    self.music_id = ''
	if self.main.score.gid == gid:
	    self.main.score.gid = ''
	
	stream = open(filename, 'w')	
	json.dump(d, stream)
	stream.close()	
	    
    def find_local_file_by_gid(self, gid):
	local_list = os.listdir(Global.score_folder_local)
	local_list = filter(lambda name: name.endswith(".mp") and name.find('-')!=-1, local_list)
	for name in local_list:
	    if gid == self.get_score_gid(Global.score_folder_local + name):
		return name
	return None
	    
    def edit(self, png_name):
	
	self.fix_button = 0
	uid = png_name[0:len(png_name)-4]
	mp_name = uid + '.mp'
	
	if self.category == 'Popular' or self.category == 'New':
	    gid = uid
	    author = self.get_score_author(Global.score_folder_download + mp_name)
	    if author == self.main.username:   # this is my uploaded piece -> find the local file, it is possible that the content has been changed
		filename = self.find_local_file_by_gid(gid)
	        if filename == None:           # cannot find it, re-create the local piece
		    uid = self.score.generate_uid()
		    shutil.copy(Global.score_folder_download + png_name, Global.score_folder_local + 'temp.png')
  		    shutil.copy(Global.score_folder_download + mp_name, Global.score_folder_local + 'temp.mp')		    
		    print "copy " + mp_name + " to temp.mp"
		    mp_name = 'temp.mp'
		    #shutil.copy(Global.score_folder_download + png_name, Global.score_folder_local + uid + '.png')
		    #shutil.copy(Global.score_folder_download + mp_name, Global.score_folder_local + uid + '.mp')
		    #print "copy " + mp_name + " to " + uid + '.mp'
		else:                          # found it, open it
		    uid = filename[:-3]
		    mp_name = uid + '.mp'
		    print "to open " + uid + '.mp'
	    else:                              # create a local piece (ignore the possibility that a local copy might exist already)
		uid = self.score.generate_uid()
		shutil.copy(Global.score_folder_download + png_name, Global.score_folder_local + 'temp.png')
		shutil.copy(Global.score_folder_download + mp_name, Global.score_folder_local + 'temp.mp')		
		print "copy " + mp_name + " to temp.mp"
		mp_name = 'temp.mp'
		#shutil.copy(Global.score_folder_download + png_name, Global.score_folder_local + uid + '.png')
	        #shutil.copy(Global.score_folder_download + mp_name, Global.score_folder_local + uid + '.mp')		
		#print "copy " + mp_name + " to " + uid + '.mp'
	    self.main.score.uid = uid
	    if self.platform == 'sugar-xo':
		self.main.activity.update_uid(uid)	
	    self.main.to_canvas_view(Global.score_folder_local + mp_name)	
	    self.main.score.gid = gid          # assign the gid
	elif self.category == 'Mine':			
	    self.main.score.uid = uid
	    if self.platform == 'sugar-xo':
		self.main.activity.update_uid(uid)	    
	    self.main.to_canvas_view(Global.score_folder_local + mp_name)	

    def favorite(self):
	self.is_favorite = not self.is_favorite
	if self.is_favorite:
	    self.main.network.interact(self.main.username, self.music_id, 'like', self.interact_callback)
	    self.favorite_count = self.favorite_count + 1
	    if self.main.home_view.likes_table.has_key(self.music_id):
		self.main.home_view.likes_table[self.music_id] = self.main.home_view.likes_table[self.music_id] + 1	    
	    if self.main.home_view.like_table.has_key(self.music_id):
		self.main.home_view.like_table[self.music_id] = self.is_favorite		
	else:
	    self.main.network.interact(self.main.username, self.music_id, 'unlike', self.interact_callback)
	    self.favorite_count = self.favorite_count - 1
	    if self.main.home_view.likes_table.has_key(self.music_id):
		self.main.home_view.likes_table[self.music_id] = self.main.home_view.likes_table[self.music_id] - 1	    
  	    if self.main.home_view.like_table.has_key(self.music_id):
	        self.main.home_view.like_table[self.music_id] = self.is_favorite			    
	cr = cairo.Context(self.pixmap)
	(x0, y0, x1, y1) = self.get_icon_bound('favorite')
	self.draw_count(cr, x0, y0, 'favorite', self.hover_icon == 'favorite', self.favorite_count)
	self.queue_draw_area(x0, y0, x1-x0+100, y1-y0)	
	
    def play(self):
	if self.main.csa.play_state == 'play':
	    self.main.csa.stop_music()
	    self.draw_highlight(-1)
	else:
	    self.main.csa.play_music(0, 'detail')
	    self.main.network.interact(self.main.username, self.music_id, 'play', self.interact_callback)
	    if self.main.home_view.play_count_table.has_key(self.music_id):
		self.main.home_view.play_count_table[self.music_id] = self.main.home_view.play_count_table[self.music_id] + 1
	    self.play_count = self.play_count + 1
	    cr = cairo.Context(self.pixmap)
	    (x0, y0, x1, y1) = self.get_icon_bound('play')	    
	    self.draw_count(cr, x0, y0, 'play', self.hover_icon == 'play', self.play_count)
	    self.queue_draw_area(x0, y0, x1-x0+100, y1-y0)	
	self.queue_draw_area(415, self.y + 175, 240, 240)
	
    def rewind(self):
	if self.sid == 0:
	    return
	if self.sid == 1 and self.slist[0].find('NEW') == 0:
	    return
	self.load_from_list(self.sid - 1)
	
    def forward(self):
	if self.sid == len(self.slist) - 1:
	    return
	self.load_from_list(self.sid + 1)
	
    def interact_callback(self, result):
	return
	
    def delete_callback(self, result):
	self.main.go_home()
    
    def is_instrument_used(self, ins):
	for i in range(self.gwid):
	    for j in range(self.ghei):	
		if self.score.note_map[ins][i][j] != 0:
		    return True
	return False
    
    def split_date_string(self, st):
	t = st.split(' ')
	t1 = t[0].split('-')
	t2 = t[1].split(':')
	return [int(t1[0]), int(t1[1]), int(t1[2]), int(t2[0]), int(t2[1])]
	
    def get_date_string(self, score_time_str):
	if score_time_str == '':
	    return ''
	[Y, m, d, H, M] = self.split_date_string(score_time_str)	
	now_time = datetime.datetime.now()
	mins = now_time.minute - M + (now_time.hour - H) * 60 + (now_time.day - d) * 60 * 24 + (now_time.month - m) * 60 * 24 * 30 + (now_time.year - Y) * 60 * 24 * 365
	if mins < 60:
	    if mins == 1:
		return "one minute ago"
	    else:
		return str(mins) + " minutes ago"
	else:
	    hours = mins / 60
	    if hours < 24:
		if hours == 1:
		    return "one hour ago"
		else:
		    return str(hours) + " hours ago"
	    else:
		days = hours / 24
		if days < 7:
		    if days == 1:
			return "one day ago"
		    else:
			return str(days) + " days ago"
		elif days < 30:
		    weeks = days / 7
		    if weeks == 1:
			return "one week ago"
		    else:
			return str(weeks) + " weeks ago"
		else:
		    return score_time_str	