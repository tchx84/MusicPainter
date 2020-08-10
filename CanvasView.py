from gi.repository import Gtk
from gi.repository import Gdk
from Musicpainter import *
from BToolbar import *
from PaintScore import *
import Global

class CanvasView(Gtk.DrawingArea):

    def __init__(self, width, height, gwid, ghei, platform, main):
        
        self.main = main
        self.platform = platform
        self.width = width
        self.height = height
        self.gwid = gwid
        self.ghei = ghei
        
        self.init_data()
        self.init_graphics()
        self.init_ui()
        
        Gtk.DrawingArea.__init__(self)        
        
        #self.set_size_request(self.width, self.height)

    def init_graphics(self):
        if self.platform == "sugar-xo":
            self.top_bar_height = 0
            self.height = self.height - 75
            #self.bottom_bar_height = 105
            self.unit_height = 36
            self.unit_div_height = 38	    	    
        elif self.platform == "windows" and self.height == 720:
            self.top_bar_height = 0
            self.unit_height = 30
            self.unit_div_height = 32
            #self.bottom_bar_height = 104
        else:
            self.top_bar_height = 75
            #self.bottom_bar_height = 105
            self.unit_height = 36
            self.unit_div_height = 38
	    	    
            
        self.canvas_height = self.unit_div_height * (self.ghei-1) + self.unit_height
        self.bottom_bar_height = self.height - self.top_bar_height - self.canvas_height 
        
        self.top_bar_y = 0        
        self.canvas_y = self.top_bar_y + self.top_bar_height
        self.bottom_bar_y = self.canvas_y + self.canvas_height
        
        self.bottom_bar = BToolbar(self.width, self.bottom_bar_height, self.bottom_bar_y, self.main)
        #self.bottom_bar = BToolbar(self.width, self.bottom_bar_height, self.unit_height, self.bottom_bar_y, self.main)
        
        self.grid_line_width = 1.5        
        self.unit_width = 1.0 * self.width / self.gwid
        
        #self.unit_height = 1.0 * (self.canvas_height - self.grid_line_width * (self.ghei - 1)) / self.ghei
        #self.unit_div_height = self.unit_height + self.grid_line_width        
        #self.unit_width = 18
        
        self.scale_block_width = 102
        self.scale_block_height = 114
        self.scale_block_div = 12	
	
	self.nos_time_grid_line = 8
	self.show_time_grid_line = 0	
	self.show_keymap = False
	self.show_pitchmap = False
	
	self.font = self.main.font
        
    def init_data(self):
        self.hover_scale_box = -1
        self.is_configured = False
        self.toolbar_expanded = False
        self.is_scale_bar_visible = False
        self.fix_button = 0
        self.just_clean = False
	self.show_aim = False
	self.wait_mouse_up = False
        self.last_highlight_gx = -1
        self.mouse_down_area = ''
        (self.last_gx, self.last_gy) = (-1, -1)
	
	self.show_tooltip = 'none'
	self.tooltip_bound = [-1, -1, -1, -1]
	
	self.show_keyon = [0 for i in range(self.ghei)]
    
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
        
        if self.platform == "sugar-xo" and self.toolbar_expanded:
            cr.set_source_surface(self.pixmap, 0, -75)
        else:
            cr.set_source_surface(self.pixmap, 0, 0)
        cr.paint()
	
	self.draw_canvas_tag(cr)
	
	self.draw_key_presses(cr)
	
	if self.show_time_grid_line != 0:
	    self.draw_time_grid_line(cr)
	    
	if self.is_scale_bar_visible:
	    self.draw_scale_boxes(cr)
	    
	if self.show_aim:
	    self.draw_aim_lines(cr)
	    
	if self.show_tooltip != 'none':
	    self.draw_tooltip(cr)
	    self.bottom_bar.draw_center(cr)	    
	    
        return False
        
    def configure_event(self, widget, event):
        width = widget.get_allocation().width
        height = widget.get_allocation().height
       
        self.canvas_pixmap = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height) # the background
        self.score_pixmap = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height) # the score layer
        self.pixmap = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height) # all layers
        
        self.prepare_canvas_pixmap()
       
        #scr = cairo.Context(self.score_pixmap) 
        #scr.set_source_surface(self.canvas_pixmap, 0, 0)
        #scr.paint()
        
        self.draw_score(widget)
        
        #cr = cairo.Context(self.pixmap)        
        #cr.set_source_surface(self.score_pixmap, 0, 0)
        #cr.paint()
        
        #widget.queue_draw_area(0, 0, width, height)
        self.is_configured = True
        
        return True
    
    def enter_notify_event(self, widget, event):
        return
    
    def leave_notify_event(self, widget, event):
        cr = cairo.Context(self.pixmap)
        if self.is_scale_bar_visible and self.hover_scale_box != -1:
            self.update_scale_boxes()            
        if self.bottom_bar.leave(cr) == True:
            widget.queue_draw_area(0, self.bottom_bar_y, self.width, self.bottom_bar_height)
        if not (self.last_gx == -1 and self.last_gy == -1):
            self.erase_cursor(widget, self.last_gx, self.last_gy)
	    (lx, ly) = (self.last_gx, self.last_gy)
	    (self.last_gx, self.last_gy) = (-1, -1)
	    if self.show_aim:
		self.update_aim_lines_move(lx, ly, -1, -1)
    
    def on_mouse_down_event(self, widget, event):
        self.fix_button = self.fix_button + 1
        if self.fix_button != 1:
            return
        if event.button != 1:
            return True
        if self.is_scale_bar_visible:
            i = self.on_scale_box(event.x, event.y)
            if i == -1:
                #self.scale_view() # switch off when click out of bound
		self.main.activity.set_scale(False)
                return
            elif i == 0:
                return
            else:  # i >= 1
                self.select_scale(i-1)
                return True
            
        if self.bottom_bar.is_inbound(event.x, event.y):
            self.mouse_down_area = 'bottom_bar'
            cr = cairo.Context(self.pixmap)
            update = self.bottom_bar.on_mouse_down_event(cr, event.x, event.y)
            if update == 1:
                widget.queue_draw_area(0, self.bottom_bar_y, self.width, self.bottom_bar_height)
            elif update == 2:
                self.draw_score(widget, self.bottom_bar.active_instrument)
		self.bottom_bar.draw_toolset(cr)
                self.bottom_bar.draw_instruments(cr)
                widget.queue_draw_area(0, self.bottom_bar_y, self.width, self.bottom_bar_height)
        elif self.on_canvas(event.x, event.y):
            self.mouse_down_area = 'canvas'
            (gx, gy) = self.within_score(event.x, event.y)
            if self.bottom_bar.active_tool_index == 0: # pen
                (self.last_gx, self.last_gy) = (gx, gy)		
                if not self.main.score.touch_grid(self.bottom_bar.active_instrument, gx, gy):
                    self.just_clean = True
                self.main.csa.drag_on(self.bottom_bar.active_tool_index, self.bottom_bar.active_instrument, gy)  # make dragging sound
                self.do_canvas_update_job(widget)   
            elif self.bottom_bar.active_tool_index == 1: # eraser
                self.main.score.erase_grid(self.bottom_bar.active_instrument, gx, gy)
                self.do_canvas_update_job(widget)
            elif self.bottom_bar.active_tool_index == 2: # forte
                v = self.main.score.increase_volume(gx, gy)
                if v != -1:
                    self.do_canvas_update_job(widget)   
                    self.main.csa.drag_on_vol(self.bottom_bar.active_instrument, gy, 1.0*v/255)                        
            elif self.bottom_bar.active_tool_index == 3: # piano
                v = self.main.score.decrease_volume(gx, gy)
                if v != -1:
                    self.do_canvas_update_job(widget)   
                    self.main.csa.drag_on_vol(self.bottom_bar.active_instrument, gy, 1.0*v/255)              
#            elif self.bottom_bar.active_tool_index == 4: # select
#                return            
            elif self.bottom_bar.active_tool_index == 4: # cut
		ins = self.get_cut_ins_grid(gx, gy)
		if ins != -1:
		    self.main.score.cut_grid(ins, gx, gy)
		    self.do_canvas_update_job(widget)                
        return True

    def on_mouse_up_event(self, widget, event):
        self.fix_button = 0
        self.just_clean = False
	self.wait_mouse_up = False
        self.mouse_down_area = ''
	#self.last_gx = self.last_gy = -1
        if self.is_scale_bar_visible:
            return True
        self.main.csa.drag_off(self.bottom_bar.active_tool_index, self.bottom_bar.active_instrument)  # make dragging sound
        if self.bottom_bar.is_inbound(event.x, event.y):
            cr = cairo.Context(self.pixmap)
            if self.bottom_bar.on_mouse_up_event(cr, event.x, event.y) != 0:
                widget.queue_draw_area(0, self.bottom_bar_y, self.width, self.bottom_bar_height)
                widget.queue_draw_area(self.width/2-25, self.bottom_bar_y-6, 51, 6)
        if self.bottom_bar.clickPending != "off":
            self.bottom_bar.clickPending = "off"
        return True
                
    def on_mouse_move_event(self, widget, event):
        #if event.is_hint:
        #    print dir(event.window.get_pointer())
        #    x = event.window.get_pointer().x
        #    y = event.window.get_pointer().y
        #    state = event.window.get_pointer().state
        #else:
        x, y = event.x, event.y
        state = event.get_state()
	
	if self.wait_mouse_up:
	    return 
        
        if self.is_scale_bar_visible:
            i = self.on_scale_box(x, y)
            if self.hover_scale_box != i:
                self.hover_scale_box = i
                self.update_scale_boxes()
            return True
      
        if self.on_canvas(event.x, event.y) and self.mouse_down_area != 'bottom_bar':
            cr = cairo.Context(self.pixmap)
            if self.bottom_bar.leave(cr):
                widget.queue_draw_area(0, self.bottom_bar_y, self.width, self.bottom_bar_height)
                widget.queue_draw_area(self.width/2-25, self.bottom_bar_y-6, 51, 6)
                
            (gx, gy) = self.within_score(event.x, event.y)
            if not state & Gdk.ModifierType.BUTTON1_MASK: # not on click
		if not (gx == self.last_gx and gy == self.last_gy):
		    self.erase_cursor(widget, self.last_gx, self.last_gy)
		    self.draw_cursor(widget, gx, gy)
		    (lx, ly) = (self.last_gx, self.last_gy)
		    (self.last_gx, self.last_gy) = (gx, gy)            
		    if self.show_aim:
		        self.update_aim_lines_move(lx, ly, gx, gy)
		return True
            else:            
                if not (gx == self.last_gx and gy == self.last_gy):
                    if self.bottom_bar.active_tool_index == 0: # pen
                        if self.just_clean:
                            self.just_clean = False # need to undo clean
                            self.main.score.add_grid(self.bottom_bar.active_instrument, self.last_gx, self.last_gy)
                        self.main.score.add_grid(self.bottom_bar.active_instrument, gx, gy)
                        self.do_canvas_update_job(widget)   
                        if not self.last_gy == gy:
                            self.main.csa.drag_on(self.bottom_bar.active_tool_index, self.bottom_bar.active_instrument, gy)  # make dragging sound                    
                    elif self.bottom_bar.active_tool_index == 1: # eraser
                        self.main.score.erase_grid(self.bottom_bar.active_instrument, gx, gy)
                        self.do_canvas_update_job(widget)    
                    elif self.bottom_bar.active_tool_index == 2: # forte
                        v = self.main.score.increase_volume(gx, gy)
                        if v != -1:
                            self.do_canvas_update_job(widget)   
                            self.main.csa.drag_on_vol(self.bottom_bar.active_instrument, gy, 1.0*v/255)                        
                    elif self.bottom_bar.active_tool_index == 3: # piano
                        v = self.main.score.decrease_volume(gx, gy)
                        if v != -1:
                            self.do_canvas_update_job(widget)   
                            self.main.csa.drag_on_vol(self.bottom_bar.active_instrument, gy, 1.0*v/255)                     
                    self.erase_cursor(widget, self.last_gx, self.last_gy)
                    self.draw_cursor(widget, gx, gy)
		    (lx, ly) = (self.last_gx, self.last_gy)
		    (self.last_gx, self.last_gy) = (gx, gy)            
		    if self.show_aim:
		        self.update_aim_lines_move(lx, ly, gx, gy)
	    
        else: 
            if self.bottom_bar.is_inbound(event.x, event.y) or (self.bottom_bar.clickPending != "off" and event.y > self.bottom_bar_y - 2 * self.unit_div_height):
                cr = cairo.Context(self.pixmap)
                if self.bottom_bar.on_mouse_move_event(cr, event.x, event.y):
                    widget.queue_draw_area(0, self.bottom_bar_y, self.width, self.bottom_bar_height)
                    widget.queue_draw_area(self.width/2-25, self.bottom_bar_y-6, 51, 6)
            if not (self.last_gx == -1 and self.last_gy == -1):
                self.erase_cursor(widget, self.last_gx, self.last_gy)
		(lx, ly) = (self.last_gx, self.last_gy)
                (self.last_gx, self.last_gy) = (-1, -1)
		if self.show_aim:
		    self.update_aim_lines_move(lx, ly, -1, -1)
        return True
    
    def update_scale_boxes(self):
	self.queue_draw_area(Global.scale_box_x, self.canvas_y, self.scale_block_width*6+self.scale_block_div*7, self.scale_block_height+self.scale_block_div-2)

    def update_key_presses(self):
	for i in range(self.ghei):
	    if self.show_keyon[i] != self.main.csa.keyon[i]:
		self.show_keyon[i] = self.main.csa.keyon[i]
		self.queue_draw_area(0, self.canvas_y+i*self.unit_div_height+2, self.width, self.unit_height-2)
		
    def draw_key_presses(self, cr):
	cr.set_source_rgba(0.4, 0.4, 0.4, 0.3)
	for i in range(self.ghei):
	    if self.show_keyon[i] != 0:
		cr.rectangle(0, self.canvas_y+i*self.unit_div_height+2, self.width, self.unit_height-2)
		cr.fill()
		
    def set_aim(self, flag):
	if self.show_aim == flag:
	    return
	self.show_aim = flag
	#if self.last_gx == -1 or self.last_gy == -1:
	#    return 
	self.update_aim_lines()
	
    def update_aim_lines_move(self, lx, ly, nx, ny):
	i = ly
	if i != -1:
	    self.queue_draw_area(0, self.canvas_y+i*self.unit_div_height+2, self.width, self.unit_height-2)
	i = lx
	if i != -1:
	    self.queue_draw_area(i*self.unit_width, self.canvas_y, self.unit_width, self.canvas_height)			
	i = ny
	if i != -1:
	    self.queue_draw_area(0, self.canvas_y+i*self.unit_div_height+2, self.width, self.unit_height-2)
	i = nx
	if i != -1:
	    self.queue_draw_area(i*self.unit_width, self.canvas_y, self.unit_width, self.canvas_height)			
	    
    def update_aim_lines(self):
	i = self.last_gy
	if i != -1:
	    self.queue_draw_area(0, self.canvas_y+i*self.unit_div_height+2, self.width, self.unit_height-2)
	i = self.last_gx
	if i != -1:
	    self.queue_draw_area(i*self.unit_width, self.canvas_y, self.unit_width, self.canvas_height)		
	
    def draw_aim_lines(self, cr):
	if not self.show_aim:
	    return 
	if self.last_gx == -1 or self.last_gy == -1:
	    return 
	i = self.last_gy
	cr.set_antialias(cairo.ANTIALIAS_NONE)
	cr.set_source_rgba(0.4, 0.4, 0.4, 0.3)
	cr.rectangle(0, self.canvas_y+i*self.unit_div_height+2, self.width, self.unit_height-2)
	cr.fill()	
	i = self.last_gx
	cr.rectangle(i*self.unit_width+2, self.canvas_y, self.unit_width-4, self.canvas_height)
	cr.fill()		
		
    def draw_scale_boxes(self, cr):
        #cr = cairo.Context(self.pixmap)
        if self.is_scale_bar_visible:
            cr.set_source_rgb(0.16, 0.16, 0.16)
            cr.rectangle(Global.scale_box_x, self.canvas_y, self.scale_block_width*6+self.scale_block_div*7, self.scale_block_height+self.scale_block_div-2)
            cr.fill()
            for i in range(6):
                self.draw_scale_box(cr, i)
        else:
            cr.set_source_surface(self.score_pixmap)
            cr.rectangle(Global.scale_box_x, self.canvas_y, self.scale_block_width*6+self.scale_block_div*7, self.scale_block_height+self.scale_block_div-2)
            cr.paint()        
        
    def draw_scale_box(self, cr, i):
        cr.set_source_rgb(0.4, 0.4, 0.4)
        x0 = Global.scale_box_x+(i+1)*self.scale_block_div+i*self.scale_block_width
        y0 = self.canvas_y
        self.create_curvy_rectangle(cr, x0, y0, self.scale_block_width, self.scale_block_height, 12, True, True)
        cr.fill()
        ys = self.main.score.get_scale_ys(i)
        l = len(ys)
        uw = 1.0 * (self.scale_block_width - 6 - 6) / (l-1)
        if self.main.score.scale_mode == i:
            cr.set_source_rgb(1, 1, 1)
        else:
            cr.set_source_rgb(0.16, 0.16, 0.16)
        for j in range(l):
            if ys[j] != -1:
                cr.rectangle(uw*j+x0+3, y0+ys[j]*6, 6, 6)
                cr.fill()
        #print self.hover_scale_box
        if self.hover_scale_box == (i+1):
            cr.set_source_rgba(1, 1, 1, 0.5)
            self.create_curvy_rectangle(cr, x0, y0, self.scale_block_width, self.scale_block_height, 12, True, True)
            cr.fill()
	    
    def record_keyboard_press(self, i):
	if self.last_highlight_gx < 0 or self.last_highlight_gx >= self.gwid:
	    return
	if self.bottom_bar.is_recording and not self.is_scale_bar_visible:
	    if self.main.score.add_grid(self.bottom_bar.active_instrument, self.last_highlight_gx, i):
		self.do_canvas_update_job(self)

    def record_keyboard_release(self, i):
	if self.last_highlight_gx < 0 or self.last_highlight_gx >= self.gwid:
	    return
	if self.bottom_bar.is_recording and not self.is_scale_bar_visible:
	    if self.main.score.cut_grid(self.bottom_bar.active_instrument, self.last_highlight_gx, i):
		self.do_canvas_update_job(self)	    
		
    def draw_highlight(self, gx):
        if gx == self.last_highlight_gx:
            return
        if not self.last_highlight_gx == -1:
            gxa = (self.last_highlight_gx / 4) * 4
            gxb = (self.last_highlight_gx / 4) * 4 + 3                    
            cr = cairo.Context(self.pixmap)
            cr.set_antialias(cairo.ANTIALIAS_NONE)
            cr.rectangle(gxa*self.unit_width, self.canvas_y+1, (gxb-gxa+1)*self.unit_width, self.canvas_height-1)
            cr.clip()
            cr.set_source_surface(self.score_pixmap, 0, 0)
            cr.paint()        
	    cr.set_antialias(cairo.ANTIALIAS_DEFAULT)
	    if self.gwid/2 - 2 <= gxb and gxa <= self.gwid/2 + 1:
		self.bottom_bar.draw_center(cr)
            self.queue_draw_area((int)(self.unit_width*gxa), (int)(self.canvas_y+1), 
                                 (int)(ceil((gxb-gxa+1)*self.unit_width)), (int)(ceil(self.canvas_height)-1))
        if not gx == -1:
            gxa = (gx / 4) * 4
            gxb = (gx / 4) * 4 + 3        
            cr = cairo.Context(self.pixmap)
            cr.set_antialias(cairo.ANTIALIAS_NONE)
            cr.set_source_rgba(1, 1, 1, 0.7)
            self.create_curvy_rectangle(cr, gx*self.unit_width, self.canvas_y+2, self.unit_width, self.canvas_height-2, 6, False, False)
            cr.fill()        
	    cr.set_antialias(cairo.ANTIALIAS_DEFAULT)
	    if self.gwid/2 - 2 <= gxb and gxa <= self.gwid/2 + 1:
		self.bottom_bar.draw_center(cr)
            self.queue_draw_area((int)(self.unit_width*gxa), (int)(self.canvas_y+1), 
                                 (int)(ceil((gxb-gxa+1)*self.unit_width)), (int)(ceil(self.canvas_height)-1))
            self.last_highlight_gx = gx
	    
	    if self.bottom_bar.is_recording and not self.is_scale_bar_visible:
		added = False
		for i in range(self.ghei):
		    if self.main.csa.keyon[i] != 0:
			if self.main.score.add_grid(self.bottom_bar.active_instrument, gx, i):
			    added = True
		if added:
		    self.do_canvas_update_job(self)			
        #if self.is_scale_bar_visible:
            #self.draw_scale_boxes()
   
    # determine if the input location is within the score_area
    # if not, return (-1, -1)
    # if  so, return grid index (gx, gy)       
    def draw_cursor(self, widget, gx, gy):
        gxa = (gx / 4) * 4
        gxb = (gx / 4) * 4 + 3        
        cr = cairo.Context(self.pixmap)
        cr.set_antialias(cairo.ANTIALIAS_NONE)
        if self.bottom_bar.active_tool_index == 0 or self.bottom_bar.active_tool_index == 2 or self.bottom_bar.active_tool_index == 3:
            ins = self.bottom_bar.active_instrument
            cr.set_source_rgba((1+Global.get_color_red_float(ins))/2, (1+Global.get_color_green_float(ins))/2, (1+Global.get_color_blue_float(ins))/2, 0.7)
	    self.create_curvy_rectangle(cr, gx*self.unit_width, self.canvas_y+gy*self.unit_div_height+2, self.unit_width, self.unit_height-2, 6, False, False)
	    cr.fill()	    
        elif self.bottom_bar.active_tool_index == 1: # eraser
            cr.set_source_rgba(1, 1, 1, 0.7)
	    self.create_curvy_rectangle(cr, gx*self.unit_width, self.canvas_y+gy*self.unit_div_height+2, self.unit_width, self.unit_height-2, 6, False, False)
	    cr.fill()
	elif self.bottom_bar.active_tool_index == 4: # cut	    
	    if self.get_cut_ins_grid(gx, gy) == -1:
		return		    
	    cr.set_source_rgba(0.16, 0.16, 0.16)
	    cr.rectangle((gx+1)*self.unit_width-2, self.canvas_y+gy*self.unit_div_height+3, 2, self.unit_height-3)
	    cr.fill()
        widget.queue_draw_area((int)(self.unit_width*gxa), (int)(self.canvas_y+self.unit_div_height*gy+1), (int)(ceil((gxb-gxa+1)*self.unit_width)), (int)(ceil(self.unit_height)-1))
        
    def erase_cursor(self, widget, gx, gy):
        if gx == -1 and gy == -1:
            return
        gxa = (gx / 4) * 4
        gxb = (gx / 4) * 4 + 3        
        cr = cairo.Context(self.pixmap)
        cr.set_antialias(cairo.ANTIALIAS_NONE)
        cr.rectangle(gxa*self.unit_width, self.canvas_y+gy*self.unit_div_height+1, (gxb-gxa+1)*self.unit_width, self.unit_height-1)
        cr.clip()
        cr.set_source_surface(self.score_pixmap, 0, 0)
        cr.paint()
	cr.set_antialias(cairo.ANTIALIAS_DEFAULT)
	if gy == self.ghei-1 and (self.gwid/2 - 2 <= gxb and gxa <= self.gwid/2 + 1):
	    self.bottom_bar.draw_center(cr)
        widget.queue_draw_area((int)(self.unit_width*gxa), (int)(self.canvas_y+self.unit_div_height*gy+1),(int)(ceil((gxb-gxa+1)*self.unit_width)), (int)(ceil(self.unit_height)-1))
        
    def draw_grid(self, cr, gx, gy):
        seq = range(8)  # the sequence of instrument to draw
        seq.reverse()
        seq.remove(self.bottom_bar.active_instrument)
        seq.append(self.bottom_bar.active_instrument)
        for ins in seq:
            #print "[" + str(ins) + "][" + str(gx) + "][" + str(gy) + "]"	    
	    if self.main.score.note_map[ins][gx][gy] != 0:
		self.draw_grid_single_ins(cr, gx, gy, ins)
                
    def draw_note_single_ins(self, cr, gx, l, gy, ins):
        vol = self.main.score.note_map[ins][gx][gy]
        if vol >= 128:
            t = pow(1.0*vol/128, 0.82)
            cr.set_source_rgba(Global.get_color_red_float(ins)/t, Global.get_color_green_float(ins)/t, Global.get_color_blue_float(ins)/t, 0.7)
        else:
            t = pow(1.0*vol/128, 1.18)
            cr.set_source_rgba(1 + t*(Global.get_color_red_float(ins)-1), 1 + t*(Global.get_color_green_float(ins)-1), 1 + t*(Global.get_color_blue_float(ins)-1), 0.7)
        cr.set_line_width(1)
        self.create_curvy_rectangle(cr, gx*self.unit_width, self.canvas_y+gy*self.unit_div_height+2, self.unit_width*l, self.unit_height-2, 6, True, True)
        cr.fill()        
        
    def draw_grid_single_ins(self, cr, gx, gy, ins):
        curvy_on_left = (gx == 0 or self.main.score.note_map[ins][gx-1][gy] == 0 or self.main.score.cut[ins][gx-1][gy] == 1)
        curvy_on_right = (gx == self.gwid - 1 or self.main.score.note_map[ins][gx+1][gy] == 0 or self.main.score.cut[ins][gx][gy] == 1)
        vol = self.main.score.note_map[ins][gx][gy]
        if vol >= 128:
            t = pow(1.0*vol/128, 0.82)
            cr.set_source_rgba(Global.get_color_red_float(ins)/t, Global.get_color_green_float(ins)/t, Global.get_color_blue_float(ins)/t, 0.7)
        else:
            t = pow(1.0*vol/128, 1.18)
            cr.set_source_rgba(1 + t*(Global.get_color_red_float(ins)-1), 1 + t*(Global.get_color_green_float(ins)-1), 1 + t*(Global.get_color_blue_float(ins)-1), 0.7)
        cr.set_line_width(1)
        self.create_curvy_rectangle(cr, gx*self.unit_width, self.canvas_y+gy*self.unit_div_height+2, self.unit_width, self.unit_height-2, 6, curvy_on_left, curvy_on_right)
        cr.fill()
	
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
	tip = Global.get_label_from_name(tip)
	cr = cairo.Context(self.pixmap) 
	self.set_font(cr)
	cr.set_font_size(24)
	ex = cr.text_extents(str(tip))
	if self.show_tooltip != 'play':
	    b = [cx-ex[2]/2-18, self.bottom_bar_y + 18 - 52, ex[2]+36, 52]
	else:
	    b = [cx-300, self.bottom_bar_y - 76, 600, 76]
	if b[0] < 0: # check left bound
	    b[0] = 0
	if b[0]+b[2] >= self.width:  # check right bound
	    b[0] = self.width - b[2]
	return b
	
    def draw_tooltip(self, cr):	
	b = self.tooltip_bound
	cr.set_source_rgb(0, 0, 0)
	cr.rectangle(b[0], b[1], b[2], b[3])
	cr.fill()
	
	cr.set_source_rgb(1, 1, 1)  # set up font
	self.set_font(cr)
	cr.set_font_size(24)
	
	if self.show_tooltip != 'play':
	    tip = Global.get_label_from_name(self.show_tooltip)
	    ex = cr.text_extents(str(tip))
	    cr.move_to(b[0]+b[2]/2-ex[2]/2, b[1]+b[3]-15)
	    cr.show_text(str(tip))	    	
	else:
	    ex = cr.text_extents(str('Play/Stop'))
	    cr.move_to(b[0]+b[2]/2-ex[2]/2, b[1]+b[3]-28)
  	    cr.show_text(str('Play/Stop'))	    		    
	    
	    cr.set_font_size(20)     
	    ex = cr.text_extents(str('speed up: drag to right'))
	    cr.move_to(b[0]+b[2]/2+72, b[1]+b[3]-40)
	    cr.show_text(str('speed up: drag to right'))	    
	    
	    cr.move_to(b[0]+b[2]/2+72, b[1]+b[3]-28)     # draw arrow
	    cr.line_to(b[0]+b[2]/2+300-24, b[1]+b[3]-28)
	    cr.stroke()
	    cr.move_to(b[0]+b[2]/2+300-24, b[1]+b[3]-28)
	    cr.line_to(b[0]+b[2]/2+300-24-8, b[1]+b[3]-28-3)
	    cr.stroke()
	    cr.move_to(b[0]+b[2]/2+300-24, b[1]+b[3]-28)
  	    cr.line_to(b[0]+b[2]/2+300-24-8, b[1]+b[3]-28+3)	    
	    cr.stroke()
	    
	    cr.set_font_size(20)     
	    ex = cr.text_extents(str('slow down: drag to left'))
	    cr.move_to(b[0]+b[2]/2-72-ex[2], b[1]+b[3]-40)
	    cr.show_text(str('slow down: drag to left'))	    	    

	    cr.move_to(b[0]+b[2]/2-72, b[1]+b[3]-28)
	    cr.line_to(b[0]+b[2]/2-300+24, b[1]+b[3]-28)
	    cr.stroke()
	    cr.move_to(b[0]+b[2]/2-300+24, b[1]+b[3]-28)
	    cr.line_to(b[0]+b[2]/2-300+24+8, b[1]+b[3]-28-3)
	    cr.stroke()
	    cr.move_to(b[0]+b[2]/2-300+24, b[1]+b[3]-28)
	    cr.line_to(b[0]+b[2]/2-300+24+8, b[1]+b[3]-28+3)
	    cr.stroke()
        
    def draw_change_scale(self, widget):
        self.prepare_canvas_pixmap()        
        self.draw_score(widget)
        
        #cr = cairo.Context(self.pixmap)
        #cr.set_antialias(cairo.ANTIALIAS_NONE)        
        
        #for j in range(self.ghei):
            #g = self.get_gradient(j)
            #cr.set_source_rgb(g, g, g)

            #i = 0
            #while i < self.gwid:
                #du = 1
                #if self.is_grid_blank(i, j):
                    #while i+du < self.gwid and self.is_grid_blank(i+du, j):
                        #du = du + 1                        
                    #cr.rectangle(i*self.unit_width, self.canvas_y+j*self.unit_div_height+2, du*self.unit_width, self.unit_height-2)
                    #cr.fill()
                    #widget.queue_draw_area(i*self.unit_width, self.canvas_y+j*self.unit_div_height+2, du*self.unit_width, self.unit_height-2)
                #i = i + du

        #self.bottom_bar.draw_center(cr) # draw play button
        
    def save_thumb(self, filename):
	width = self.main.home_view.cell_width
	height = self.main.home_view.cell_height
	unit_w = 1.0*width/self.gwid
	unit_h = 1.0*height/self.ghei
	scoremap = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
	scr = cairo.Context(scoremap)
	scr.rectangle(0, 0, width, height)
	scr.set_source_rgb(0.88, 0.88, 0.88)
	scr.fill()
	for ins in range(8):
	    for j in range(self.ghei):
		for i in range(self.gwid):
		    if self.main.score.note_map[ins][i][j] != 0 and (i == 0 or self.main.score.note_map[ins][i-1][j] == 0 or self.main.score.cut[ins][i-1][j] == 1):
			du = 1
			while self.main.score.cut[ins][i+du-1][j] == 0 and i+du < self.gwid and self.main.score.note_map[ins][i+du][j] != 0:
			    du = du + 1
			vol = self.main.score.note_map[ins][i][j]
			if vol >= 128:
			    t = pow(1.0*vol/128, 0.82)
			    scr.set_source_rgba(Global.get_color_red_float(ins)/t, Global.get_color_green_float(ins)/t, Global.get_color_blue_float(ins)/t, 0.7)
			else:
			    t = pow(1.0*vol/128, 1.18)
			    scr.set_source_rgba(1 + t*(Global.get_color_red_float(ins)-1), 1 + t*(Global.get_color_green_float(ins)-1), 1 + t*(Global.get_color_blue_float(ins)-1), 0.7)
			self.create_curvy_rectangle(scr, unit_w*i, unit_h*j, unit_w*du, unit_h, 2, True, True)
			scr.fill()

	pixmap = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
	cr = cairo.Context(pixmap)
	self.create_curvy_rectangle(cr, 0, 0, width, height, 10, True, True)
	cr.clip()
	cr.set_source_surface(scoremap, 0, 0)
	cr.paint()
	pixmap.write_to_png(str(filename))

    def draw_score(self, widget, one_ins = -1): # update the entire canvas
        cr = cairo.Context(self.pixmap)
        cr.set_antialias(cairo.ANTIALIAS_NONE)
        
        scr = cairo.Context(self.score_pixmap)  # draw background
        
        if one_ins == -1:
            #scr.rectangle(0, self.canvas_y, self.width, self.canvas_height)
            #scr.clip()
            scr.set_source_surface(self.canvas_pixmap, 0, 0)
            scr.paint()
        
        seq = range(8)  # the sequence of instrument to draw
        seq.reverse()
        seq.remove(self.bottom_bar.active_instrument)
        seq.append(self.bottom_bar.active_instrument)        
        
        for j in range(self.ghei):
            for ins in seq:
                if one_ins != -1 and ins != one_ins:
                    continue
		if one_ins == -1:
		    for i in range(self.gwid):
			if self.main.score.note_map[ins][i][j] != 0 and (i == 0 or self.main.score.note_map[ins][i-1][j] == 0 or self.main.score.cut[ins][i-1][j] == 1):
			    du = 1
			    while self.main.score.cut[ins][i+du-1][j] == 0 and i+du < self.gwid and self.main.score.note_map[ins][i+du][j] != 0:
			        du = du + 1
			    self.draw_note_single_ins(scr, i, du, j, ins)
		else:		    
		    for i in range(self.gwid):
			if self.main.score.note_map[ins][i][j] != 0:
			    f = False
			    for k in range(7):
				if self.main.score.note_map[seq[k]][i][j] != 0:
				    f = True
				    break
			    if f:
				self.draw_grid_single_ins(scr, i, j, ins)				                    

        self.bottom_bar.draw_center(scr) # draw play button
        
        #cr.rectangle(0, self.canvas_y, self.width, self.canvas_height)
        #cr.clip()
        cr.set_source_surface(self.score_pixmap, 0, 0)
        cr.paint()        
        
        #self.bottom_bar.draw_center(cr) # draw play button
            
        widget.queue_draw_area(0, 0, self.width, self.height)
                    
    #def update_draw_slider(self):  # on show, or on animate
        #cr = cairo.Context(self.pixmap)
        #self.bottom_bar.draw(cr)
        #self.queue_draw_area(self.width/2-25, self.bottom_bar_y-6, 51, 6)
        #self.queue_draw_area(0, self.bottom_bar_y, self.width, self.bottom_bar_height)
        
    def redraw(self):
        if self.is_configured:
            self.prepare_canvas_pixmap()
            self.draw_score(self)        
    
    def refresh_view(self):
        self.queue_draw_area(0, 0, self.width, self.height)
        
    def update_instruments(self, ins):
        self.bottom_bar.instruments = ins
	self.main.score.instruments = ins
        self.prepare_canvas_pixmap()        
    
    def do_canvas_update_job(self, widget):
        while len(self.main.score.update_jobs) != 0:
            job = self.main.score.update_jobs[0]
            self.do_one_canvas_update_job(widget, job)
            self.main.score.update_jobs.remove(job)
            
    def do_one_canvas_update_job(self, widget, job):
        [gxa, gxb, gy] = job
        gxa = (gxa / 4) * 4
        gxb = (gxb / 4) * 4 + 3
        cr = cairo.Context(self.pixmap)
        cr.set_antialias(cairo.ANTIALIAS_NONE)
        scr = cairo.Context(self.score_pixmap)
        #scr.set_antialias(cairo.ANTIALIAS_NONE)
        scr.rectangle(gxa*self.unit_width, self.canvas_y+gy*self.unit_div_height+1, (gxb-gxa+1)*self.unit_width, self.unit_height-1)
        scr.clip()
        scr.set_source_surface(self.canvas_pixmap, 0, 0)
        scr.paint()
        for i in range(gxb-gxa+1):
            self.draw_grid(scr, gxa+i, gy)
        cr.rectangle(gxa*self.unit_width, self.canvas_y+gy*self.unit_div_height+1, (gxb-gxa+1)*self.unit_width, self.unit_height-1)
        cr.clip()
        cr.set_source_surface(self.score_pixmap, 0, 0)
        cr.paint()        
	if self.bottom_bar.active_tool_index == 5 and gxa <= self.last_gx and self.last_gx <= gxb and self.last_gy == gy:
	    self.draw_cursor(widget, self.last_gx, self.last_gy)
        if gy == self.ghei-1 and not (gxb < self.gwid/2 - 3 and gxa >= self.gwid/2 + 3): # draw play button
            self.bottom_bar.draw_center(cr)
            
        widget.queue_draw_area((int)(self.unit_width*gxa), (int)(self.canvas_y+self.unit_div_height*gy+1), 
                               (int)(ceil((gxb-gxa+1)*self.unit_width)), (int)(ceil(self.unit_height)-1))
	
    def update_canvas_tag(self):
	#if not self.show_keymap and not self.show_pitchmap:
	#    return	
	self.queue_draw_area(0, (int)(self.canvas_y+1), (int)(ceil(4*self.unit_width)), (int)(ceil(self.canvas_height)-1))
	
    def draw_canvas_tag(self, cr):
	if not self.show_keymap and not self.show_pitchmap:
	    return	
	if self.show_keymap:
	    cr.set_font_size(16)
	elif self.show_pitchmap:
	    cr.set_font_size(12)	    
	self.set_font(cr)
	
	for i in range(self.ghei):	    
	    cr.move_to(6, self.canvas_y + self.unit_div_height * (0.6+i))
	    if self.show_keymap and self.show_keyon[i] == 1:
		cr.set_source_rgb(0, 0, 0)
	    else:
		cr.set_source_rgb(0.4, 0.4, 0.4)
	    if self.show_keymap:
		cr.show_text(Global.key_map[i])
	    elif self.show_pitchmap:
		cr.show_text(self.main.score.get_map_name(i))
		
    def draw_time_grid_line(self, cr):
	cr.set_source_rgb(1, 1, 1)  # canvas grid line
	cr.set_line_width(self.grid_line_width)
	
	i = self.show_time_grid_line	
	while i < self.width:
	    if i % 8 == 0:
		cr.set_line_width(1.8)
	    else:
		cr.set_line_width(0.6)
	    x = (i+1)*self.unit_width-2
	    cr.move_to(x, self.canvas_y+2)
	    if i == self.gwid/2:
		cr.line_to(x, self.canvas_y+self.canvas_height-13)
	    else:
		cr.line_to(x, self.canvas_y+self.canvas_height-2)
	    cr.stroke()                        
	    i = i + self.show_time_grid_line	    
	    
    def prepare_canvas_pixmap(self):
        cr = cairo.Context(self.canvas_pixmap)
        for i in range(self.ghei):
            g = self.get_gradient(i)
            cr.set_source_rgb(g, g, g)
            cr.rectangle(0, self.canvas_y + self.unit_div_height * i, self.unit_width*self.gwid, self.unit_div_height)
            cr.fill()
	    
        cr.set_source_rgb(1, 1, 1)  # canvas grid line
        cr.set_line_width(self.grid_line_width)
        
        for i in range(self.ghei - 1):
            cr.move_to(0, self.canvas_y + self.unit_div_height * (i+1))
            cr.line_to(self.unit_width*self.gwid, self.canvas_y + self.unit_div_height * (i+1))
            cr.stroke()                
            
        if self.platform != "sugar-xo":
            cr.set_source_rgb(0.16, 0.16, 0.16)
            cr.rectangle(0, self.top_bar_y, self.width, self.top_bar_height)
            cr.fill()         
            
        self.bottom_bar.draw(cr)
            
    def scale_view(self):
        self.hover_scale_box = -1
        self.is_scale_bar_visible = not self.is_scale_bar_visible
        self.update_scale_boxes()
        if self.is_scale_bar_visible:   # switch on
            self.old_scale = self.main.score.scale_mode
        else:                           # switch off
            if self.old_scale != self.main.score.scale_mode:
                self.draw_change_scale(self)	    
        
    def is_grid_blank(self, gx, gy):
        for ins in range(self.bottom_bar.n_ins):
            if self.main.score.note_map[ins][gx][gy] != 0:
                return False
        return True
    
    def get_cut_ins_grid(self, gx, gy):
	ins = self.bottom_bar.active_instrument
	if self.main.score.note_map[ins][gx][gy] != 0 and gx < self.gwid-1 and self.main.score.note_map[ins][gx+1][gy] != 0:
	    return ins
	for ins in range(8):
	    if self.main.score.note_map[ins][gx][gy] != 0 and gx < self.gwid-1 and self.main.score.note_map[ins][gx+1][gy] != 0:
		return ins
	return -1	
        
    def get_gradient(self, row):
        level = 0.10
        return 1.0 - level * (self.main.score.get_map_gradient(row)+3) / 12
    
    def toolbar_switch(self):
        self.toolbar_expanded = not self.toolbar_expanded
        
    def change_tempo(self, d):
        cr = cairo.Context(self.pixmap)
        if self.bottom_bar.change_tempo(cr, d):
            self.queue_draw_area(0, self.bottom_bar_y, self.width, self.bottom_bar_height)
            self.queue_draw_area(self.width/2-25, self.bottom_bar_y-6, 51, 6)    
            
    def shift_pitch(self, d): # d = -1, or 1	
        if -12 <= (self.main.score.score_shift + d) and (self.main.score.score_shift + d) <= 12:
            self.main.score.score_shift = self.main.score.score_shift + d
        else:
	    return
	self.main.csa.make_shift_pitch_sound()
	
    def update_looping(self, f):
	if self.bottom_bar.is_looping == f:
	    return
	self.bottom_bar.is_looping = f
	cr = cairo.Context(self.pixmap)
	self.bottom_bar.draw_toolset(cr)
	self.queue_draw_area(0, self.bottom_bar_y, self.width, self.bottom_bar_height)	
	
    def update_playall(self, f):
	if self.bottom_bar.play_all == f:
	    return
	self.bottom_bar.play_all = f
	cr = cairo.Context(self.pixmap)
	self.bottom_bar.draw_toolset(cr)
	self.queue_draw_area(0, self.bottom_bar_y, self.width, self.bottom_bar_height)
        
    def select_scale(self, i):
        if self.main.score.scale_mode != i:
            self.main.score.scale_mode = i
            self.main.csa.play_scale(i)
            self.hover_scale_box = -1
            self.update_scale_boxes()
        
    def select_instrument(self, i):
        cr = cairo.Context(self.pixmap)
        update = self.bottom_bar.to_select_instrument(cr, i)
        if update == 1:
            self.queue_draw_area(0, self.bottom_bar_y, self.width, self.bottom_bar_height)
        elif update == 2:
            self.draw_score(self, self.bottom_bar.active_instrument)
            self.bottom_bar.draw_instruments(cr)
            self.queue_draw_area(0, self.bottom_bar_y, self.width, self.bottom_bar_height)                
                          
    def start_playing(self):
        if not self.main.csa.play_music():
            return
        if self.bottom_bar.set_play(True):
            cr = cairo.Context(self.pixmap)
            self.bottom_bar.draw_center(cr)
            self.queue_draw_area(0, self.bottom_bar_y, self.width, self.bottom_bar_height)
    
    def stop_playing(self):
        self.main.csa.stop_music()
        if self.bottom_bar.set_play(False):
            cr = cairo.Context(self.pixmap)
            self.bottom_bar.draw_center(cr)            
            self.queue_draw_area(0, self.bottom_bar_y, self.width, self.bottom_bar_height)
                        
    def within_score(self, x, y):
        if x < 0 or y < self.canvas_y or x >= self.width or y >= self.canvas_y+self.canvas_height:
            return -1, -1
        return self.xy2gridxy(x, y)
    
    def on_scale_box(self, mx, my):
        if not self.is_scale_bar_visible:
            return -1
        if my < self.canvas_y or my >= self.canvas_y + self.scale_block_height + self.scale_block_div-2:
            return -1
        if mx < Global.scale_box_x or mx >= Global.scale_box_x+self.scale_block_width*6+self.scale_block_div*7:
            return -1
        for i in range(6):
            x0 = Global.scale_box_x+(i+1)*self.scale_block_div+i*self.scale_block_width
            y0 = self.canvas_y        
            if x0 <= mx and mx < x0+self.scale_block_width and y0 <= my and my < y0+self.scale_block_height:
                return i+1
        return 0
    
    def on_canvas(self, x, y):
        return x >= 0 and y >= self.canvas_y and x < self.width and y < self.canvas_y+self.canvas_height            

    # xy2gridxy():: call by within_score
    #            or call directly for drag_selection, accept (gx, gy) even out of canvas
    #               return grid index (gx, gy)
    def xy2gridxy(self, x, y):
        gx = (int)((x)/self.unit_width)
        gy = (int)((y-self.canvas_y)/self.unit_div_height)
        return gx, gy
   
    def create_curvy_rectangle(self, cr, x0, y0, w, h, r, curvy_on_left, curvy_on_right):
        x1 = x0 + w
        y1 = y0 + h
        #print "(" + str(x0) + ", " + str(y0) + ", " + str(w) + ", " + str(h) + ")"
        #cr.rectangle(x0, y0, w, h)
        
        if curvy_on_left and curvy_on_right:
	    x1 = x1 - 1
            cr.arc(x0+r, y0+r, r, pi, 1.5*pi)
            cr.line_to(x1-r, y0)
            cr.arc(x1-r, y0+r, r, 1.5*pi, 2*pi)
            cr.line_to(x1, y1-r)
            cr.arc(x1-r, y1-r, r, 0, 0.5*pi)
            cr.line_to(x0+r, y1)
            cr.arc(x0+r, y1-r, r, 0.5*pi, 1.0*pi)
            cr.close_path()       
        elif curvy_on_left and not curvy_on_right:
            cr.arc(x0+r, y0+r, r, pi, 1.5*pi)
            cr.line_to(x1, y0)
            cr.line_to(x1, y1)
            cr.line_to(x0+r, y1)
            cr.arc(x0+r, y1-r, r, 0.5*pi, 1.0*pi)
            cr.close_path()
        elif not curvy_on_left and curvy_on_right:
	    x1 = x1 - 1
            cr.move_to(x0, y0)
            cr.line_to(x1-r, y0)
            cr.arc(x1-r, y0+r, r, 1.5*pi, 2*pi)
            cr.line_to(x1, y1-r)
            cr.arc(x1-r, y1-r, r, 0, 0.5*pi)
            cr.line_to(x0, y1)
            cr.line_to(x0, y0)
        else:
            cr.rectangle(x0, y0, w, h)
	    
    def set_font(self, cr):
	if self.platform == 'sugar-xo':
	    cr.set_font_face(self.font)
	else:
	    cr.select_font_face(self.font, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)