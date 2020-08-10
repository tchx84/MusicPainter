from gi.repository import Gtk
from gi.repository import Gdk

from math import *
import cairo
import Global

class InstrumentView(Gtk.DrawingArea):
    
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
            self.ydiv = 104
            self.sel_y = 668
        elif self.platform == "windows" and self.height == 720:            
            self.top_bar_height = 0
            self.ydiv = 94
            self.sel_y = 588
        else:
            self.top_bar_height = 75
            self.ydiv = 104
            self.sel_y = 668
        
        self.y = self.top_bar_height
        self.xdiv = 96
        
        self.font = self.main.font   
    
    def init_data(self):
        self.fix_button = 0
        self.is_configured = False
        self.toolbar_expanded = False
        
        self.drag_state = 'none'        
        self.preview_sel_ins = -1
        self.preview_switch_ins = -1
        self.hover_sel_ins = -1 # selected instrument (bottom)
        self.hover_ins_list = [-1, -1] # instrument list (top)
        self.n_ins = 8

        self.instruments = self.main.canvas_view.bottom_bar.instruments
    
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
        
    def refresh_view(self):
        self.queue_draw_area(0, 0, self.width, self.height)
    
    def expose_event(self, widget, cr):
        
        if self.platform == "sugar-xo" and self.toolbar_expanded:
            cr.set_source_surface(self.pixmap, 0, -75)
        else:
            cr.set_source_surface(self.pixmap, 0, 0)
        cr.paint()
        
        if self.drag_state == 'ins_list' and self.preview_sel_ins == -1:
            self.draw_dragged_ins(cr, self.drag_item[0], self.drag_item[1], self.now_drag_x-self.start_drag_x, self.now_drag_y-self.start_drag_y)
        elif self.drag_state == 'sel_ins' and self.preview_sel_ins == 1:
            self.draw_dragged_ins2(cr, self.instruments[self.drag_item], self.now_drag_x-50, self.now_drag_y-50)
    
        return False
        
    def configure_event(self, widget, event):
        width = widget.get_allocation().width
        height = widget.get_allocation().height
       
        self.bg_pixmap = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height) # the background layer
        self.pixmap = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height) # all layers
        
        self.prepare_bg_pixmap()
       
        cr = cairo.Context(self.pixmap)        
        cr.set_source_surface(self.bg_pixmap, 0, 0)
        cr.paint()
        
        self.is_configured = True
        
        return True    
            
    def enter_notify_event(self, widget, event):
        return
    
    def leave_notify_event(self, widget, event):
        return

    def on_mouse_down_event(self, widget, event):
        self.fix_button = self.fix_button + 1
        if self.fix_button != 1:
            return True
        if event.button != 1:
            return True 
        sel_ins = self.on_selected_instrument(event.x, event.y)
        if sel_ins != -1 and self.instruments[sel_ins] != '':
            self.drag_state = 'sel_ins'
            self.drag_item = sel_ins
            (self.start_drag_x, self.start_drag_y) = (event.x, event.y)
            (self.last_drag_x, self.last_drag_y) = (event.x, event.y)
            (self.now_drag_x, self.now_drag_y) = (event.x, event.y)            
            self.main.csa.note_sample(self.instruments[sel_ins])
            return True
        on_ins_list = self.on_instrument_list(event.x, event.y)
        if on_ins_list != [-1, -1]:
            label = Global.instrument_list[Global.instrument_category[on_ins_list[0]]][on_ins_list[1]]
            name = Global.get_name_from_label(label)
            if self.is_selected_instrument(name) == -1:
                self.drag_state = 'ins_list'
                self.drag_item = on_ins_list
                (self.start_drag_x, self.start_drag_y) = (event.x, event.y)
                (self.last_drag_x, self.last_drag_y) = (event.x, event.y)
                (self.now_drag_x, self.now_drag_y) = (event.x, event.y)
                self.preview_sel_ins = -1 # borrow this variable here
            self.main.csa.note_sample(name)
        return True            
    
    def on_mouse_up_event(self, widget, event):
        x, y = event.x, event.y
        self.fix_button = 0
        if self.drag_state == 'ins_list':  # ####################################### when dragging an instrument from the list
            self.preview_sel_ins = -1            
            sel_ins = self.on_selected_instrument(x, y) 
            if sel_ins != -1:                                     # the instrument is dragged onto a color block, to switch instrument
                name = self.get_drag_ins_name()
                old_name = self.instruments[sel_ins]
                self.instruments[sel_ins] = name # switch instrument
                
                cr = cairo.Context(self.pixmap)                
                if old_name != "":
                    [t1, t2] = self.name_on_instrument_list(old_name) # remove the color off the old instrument
                    self.draw_ins_list_item(cr, t1, t2)
                    (x0, y0, x1, y1) = self.get_item_bound(t1, t2)
                    widget.queue_draw_area(x0, y0, x1-x0, y1-y0) 
                
                self.draw_bottom_ins(cr, sel_ins)                 # update the instrument block at the bottom
                (x0, y0, x1, y1) = self.get_sel_item_bound(sel_ins)                    
                widget.queue_draw_area(x0, y0, x1-x0, y1-y0)                  
                
                self.hover_ins_list = [-1, -1]                    # update the color on the new instrument
                [t1, t2] = self.name_on_instrument_list(name)
                self.draw_ins_list_item(cr, t1, t2)
                (x0, y0, x1, y1) = self.get_item_bound(t1, t2)
                widget.queue_draw_area(x0, y0, x1-x0, y1-y0)                                
            else:                                                # the instrument is not dragged onto a color block, update the hover status
                on_ins_list = self.on_instrument_list(x, y)
                if on_ins_list != self.hover_ins_list:
                    cr = cairo.Context(self.pixmap)
                    if self.hover_ins_list[0] != -1:
                        [t1, t2] = self.hover_ins_list
                        self.hover_ins_list = [-1, -1]
                        self.draw_ins_list_item(cr, t1, t2)
                        (x0, y0, x1, y1) = self.get_item_bound(t1, t2)
                        widget.queue_draw_area(x0, y0, x1-x0, y1-y0)
                    self.hover_ins_list = on_ins_list
                    if self.hover_ins_list[0] != -1:
                        self.draw_ins_list_item(cr, self.hover_ins_list[0], self.hover_ins_list[1])
                        (x0, y0, x1, y1) = self.get_item_bound(self.hover_ins_list[0], self.hover_ins_list[1])
                        widget.queue_draw_area(x0, y0, x1-x0, y1-y0)  
            
            (self.last_drag_x, self.last_drag_y) = (self.now_drag_x, self.now_drag_y)    # remove the dragged instrument
            (x0, y0, x1, y1) = self.get_item_bound(self.drag_item[0], self.drag_item[1])
            widget.queue_draw_area(x0+self.last_drag_x-self.start_drag_x, y0+self.last_drag_y-self.start_drag_y, 100, 100)                        
            self.drag_state = 'none' 
            
        elif self.drag_state == 'sel_ins': # ####################################### when dragging an instrument from the color blocks
            sel_ins = self.on_selected_instrument(x, y) 
            if sel_ins != -1 and sel_ins != self.drag_item:                      # the instrument is dragged onto a different color block, switch instruments
                old_name = self.instruments[sel_ins]
                self.instruments[sel_ins] = self.instruments[self.drag_item]
                self.instruments[self.drag_item] = old_name
                
                cr = cairo.Context(self.pixmap)                
                
                if old_name != "":
                    [t1, t2] = self.name_on_instrument_list(old_name) # update the color on the top
                    self.draw_ins_list_item(cr, t1, t2)
                    (x0, y0, x1, y1) = self.get_item_bound(t1, t2)
                    widget.queue_draw_area(x0, y0, x1-x0, y1-y0) 
                [t1, t2] = self.name_on_instrument_list(self.instruments[sel_ins]) 
                self.draw_ins_list_item(cr, t1, t2)
                (x0, y0, x1, y1) = self.get_item_bound(t1, t2)
                widget.queue_draw_area(x0, y0, x1-x0, y1-y0) 
                
                self.hover_sel_ins = -1
                self.draw_bottom_ins(cr, sel_ins)                 # update the instrument block at the bottom
                (x0, y0, x1, y1) = self.get_sel_item_bound(sel_ins)                    
                widget.queue_draw_area(x0, y0, x1-x0, y1-y0)                  
                self.draw_bottom_ins(cr, self.drag_item)                 
                (x0, y0, x1, y1) = self.get_sel_item_bound(self.drag_item)                    
                widget.queue_draw_area(x0, y0, x1-x0, y1-y0)  
            if sel_ins == -1:
                cr = cairo.Context(self.pixmap)                
                old_name = self.instruments[self.drag_item]
                self.instruments[self.drag_item] = ''                          # remove the instrument
                if old_name != "":
                    [t1, t2] = self.name_on_instrument_list(old_name) # update the color on the top
                    self.draw_ins_list_item(cr, t1, t2)
                    (x0, y0, x1, y1) = self.get_item_bound(t1, t2)
                    widget.queue_draw_area(x0, y0, x1-x0, y1-y0)                 
                
                self.draw_bottom_ins(cr, self.drag_item)                 
                (x0, y0, x1, y1) = self.get_sel_item_bound(self.drag_item)                    
                widget.queue_draw_area(x0, y0, x1-x0, y1-y0)                  
                
            (self.last_drag_x, self.last_drag_y) = (self.now_drag_x, self.now_drag_y) # remove the dragged instrument (cursor)
            widget.queue_draw_area(self.last_drag_x-50, self.last_drag_y-50, 100, 100)
            self.preview_sel_ins = -1
            self.drag_state = 'none'
    
    def on_mouse_move_event(self, widget, event):
        x, y = event.x, event.y
        state = event.get_state()
        if self.drag_state == 'ins_list':
            sel_ins = self.on_selected_instrument(x, y) 
            if sel_ins != self.preview_sel_ins: 
                cr = cairo.Context(self.pixmap)
                if self.preview_sel_ins != -1:                        # remove the previous preview
                    t = self.preview_sel_ins
                    self.preview_sel_ins = -1
                    self.draw_bottom_ins(cr, t)                 
                    (x0, y0, x1, y1) = self.get_sel_item_bound(t)                    
                    widget.queue_draw_area(x0, y0, x1-x0, y1-y0)                
                self.preview_sel_ins = sel_ins
                if self.preview_sel_ins != -1:                        # update the instrument block at the bottom
                    self.draw_bottom_ins(cr, self.preview_sel_ins)                 
                    (x0, y0, x1, y1) = self.get_sel_item_bound(self.preview_sel_ins)                    
                    widget.queue_draw_area(x0, y0, x1-x0, y1-y0) 
            #if sel_ins == -1:
            (self.last_drag_x, self.last_drag_y) = (self.now_drag_x, self.now_drag_y)
            (self.now_drag_x, self.now_drag_y) = (event.x, event.y)
            (x0, y0, x1, y1) = self.get_item_bound(self.drag_item[0], self.drag_item[1])
            widget.queue_draw_area(x0+self.last_drag_x-self.start_drag_x, y0+self.last_drag_y-self.start_drag_y, 100, 100)
            widget.queue_draw_area(x0+self.now_drag_x-self.start_drag_x, y0+self.now_drag_y-self.start_drag_y, 100, 100)
            return True
        elif self.drag_state == 'sel_ins':
            sel_ins = self.on_selected_instrument(event.x, event.y)
            if self.preview_switch_ins != -1 and sel_ins != self.preview_switch_ins:  # switch back
                cr = cairo.Context(self.pixmap)
                self.draw_bottom_ins(cr, self.preview_switch_ins)
                (x0, y0, x1, y1) = self.get_sel_item_bound(self.preview_switch_ins)                    
                widget.queue_draw_area(x0, y0, x1-x0, y1-y0)                                
                self.draw_bottom_ins(cr, self.drag_item)
                (x0, y0, x1, y1) = self.get_sel_item_bound(self.drag_item)                    
                widget.queue_draw_area(x0, y0, x1-x0, y1-y0)                                
                self.preview_switch_ins = -1
            if sel_ins != -1 and sel_ins != self.drag_item:                           # switch two selected instrument
                cr = cairo.Context(self.pixmap)
                self.draw_bottom_ins_temp(cr, sel_ins, self.instruments[self.drag_item])
                (x0, y0, x1, y1) = self.get_sel_item_bound(self.drag_item)                    
                widget.queue_draw_area(x0, y0, x1-x0, y1-y0)                
                self.draw_bottom_ins_temp(cr, self.drag_item, self.instruments[sel_ins])
                (x0, y0, x1, y1) = self.get_sel_item_bound(sel_ins)                    
                widget.queue_draw_area(x0, y0, x1-x0, y1-y0)     
                self.preview_switch_ins = sel_ins
            (self.last_drag_x, self.last_drag_y) = (self.now_drag_x, self.now_drag_y)
            (self.now_drag_x, self.now_drag_y) = (event.x, event.y)
            widget.queue_draw_area(self.last_drag_x-50, self.last_drag_y-50, 100, 100)
            if sel_ins == -1:
                self.preview_sel_ins = 1  # to draw cursor (ins)
                widget.queue_draw_area(self.now_drag_x-50, self.now_drag_y-50, 100, 100)
            else:
                self.preview_sel_ins = -1
        elif not state & Gdk.ModifierType.BUTTON1_MASK: # not on click
            sel_ins = self.on_selected_instrument(x, y)
            if sel_ins != self.hover_sel_ins:
                cr = cairo.Context(self.pixmap)
                if self.hover_sel_ins != -1:
                    t = self.hover_sel_ins
                    self.hover_sel_ins = -1
                    self.draw_bottom_ins(cr, t)
                    (x0, y0, x1, y1) = self.get_sel_item_bound(t)                    
                    widget.queue_draw_area(x0, y0, x1-x0, y1-y0)
                self.hover_sel_ins = sel_ins
                if self.hover_sel_ins != -1:
                    self.draw_bottom_ins(cr, self.hover_sel_ins)
                    (x0, y0, x1, y1) = self.get_sel_item_bound(self.hover_sel_ins)                    
                    widget.queue_draw_area(x0, y0, x1-x0, y1-y0)                    
            on_ins_list = self.on_instrument_list(x, y)
            if on_ins_list != self.hover_ins_list:
                cr = cairo.Context(self.pixmap)
                if self.hover_ins_list[0] != -1:
                    [t1, t2] = self.hover_ins_list
                    self.hover_ins_list = [-1, -1]
                    self.draw_ins_list_item(cr, t1, t2)
                    (x0, y0, x1, y1) = self.get_item_bound(t1, t2)
                    widget.queue_draw_area(x0, y0, x1-x0, y1-y0)
                self.hover_ins_list = on_ins_list
                if self.hover_ins_list[0] != -1:
                    self.draw_ins_list_item(cr, self.hover_ins_list[0], self.hover_ins_list[1])
                    (x0, y0, x1, y1) = self.get_item_bound(self.hover_ins_list[0], self.hover_ins_list[1])
                    widget.queue_draw_area(x0, y0, x1-x0, y1-y0)
        return True
        
    def toolbar_switch(self):
        self.toolbar_expanded = not self.toolbar_expanded        
        
    def on_selected_instrument(self, x, y):
        for i in range(self.n_ins):
            (x0, y0, x1, y1) = self.get_sel_item_bound(i)
            if x0 <= x and x < x1 and y0 <= y and y < y1:
                return i
        return -1     
    
    def name_on_instrument_list(self, name):
        for i in range(len(Global.instrument_category)):
            for j in range(len(Global.instrument_list[Global.instrument_category[i]])):
                label = Global.instrument_list[Global.instrument_category[i]][j]
                iname = Global.get_name_from_label(label)
                if iname == name:
                    return [i, j]
        return [-1, -1]        
    
    def on_instrument_list(self, x, y):
        for i in range(len(Global.instrument_category)):
            for j in range(len(Global.instrument_list[Global.instrument_category[i]])):
                (x0, y0, x1, y1) = self.get_item_bound(i, j)
                if x0 <= x and x < x1 and y0 <= y and y < y1:
                    return [i, j]
        return [-1, -1]
    
    def get_offset_on_instrument(self, x, y, i, j):
        (x0, y0, x1, y1) = self.get_item_bound(i, j)
        return (x-x0, y-y0)
    
    def get_sel_item_bound(self, i):
        return [29+i*146, self.y+self.sel_y, 29+i*146+123, self.y+791]
    
    def get_item_bound(self, i, j):
        m = j % 5
        d = int(j / 5)
        x0 = Global.instrument_category_x[i]-4 + self.xdiv*d
        y0 = self.y+78 + self.ydiv*m
        x1 = x0 + 95
        y1 = y0 + 100
        return [x0, y0, x1, y1]
    
    def is_selected_instrument(self, ins):
        for i in range(len(self.instruments)):
            if self.instruments[i] == ins:
                return i
        return -1
    
    def update_instruments(self, ins):
        self.instruments = ins
        if self.is_configured:
            self.prepare_bg_pixmap()
        
    def prepare_bg_pixmap(self):
        cr = cairo.Context(self.bg_pixmap)
        cr.rectangle(0, 0, self.width, self.height)
        cr.set_source_rgb(1, 1, 1)
        cr.fill()
        
        if self.platform != "sugar-xo":
            cr.set_source_rgb(0.16, 0.16, 0.16)
            cr.rectangle(0, 0, self.width, self.top_bar_height)
            cr.fill()        
        
        self.draw_left(cr)
        self.draw_instrument_list(cr)
        self.draw_bottom(cr)
        
    def draw_left(self, cr):
        cr.set_source_surface(cairo.ImageSurface.create_from_png(Global.array_png), 36, self.y+75)
        cr.paint()
                       
        for i in range(len(Global.instrument_view_hint_1)):
            if i == 0:
                self.set_font(cr)
                cr.set_font_size(18)
                
                cr.set_source_rgb(0.156, 0.156, 0.156)
            else:
                self.set_font(cr)
                cr.set_font_size(15)                
                cr.set_source_rgb(0.31, 0.31, 0.31)
            cr.move_to(39, self.y+193+21*i)
            cr.show_text(Global.instrument_view_hint_1[i])            
            cr.move_to(39, self.y+298+21*i)
            cr.show_text(Global.instrument_view_hint_2[i])
                
    def draw_instrument_list(self, cr):
        self.set_font(cr)
        for i in range(len(Global.instrument_category)):
            cr.set_font_size(22)
            cr.set_source_rgb(0.24, 0.24, 0.24)
            cr.move_to(Global.instrument_category_x[i], self.y+50)
            cr.show_text(Global.instrument_category[i])  
            
            for j in range(len(Global.instrument_list[Global.instrument_category[i]])):
                self.draw_ins_list_item(cr, i, j)
                
    def draw_dragged_ins2(self, cr, name, x, y):
        img = Global.get_img_lg_label(name)
        cr.set_source_rgba(0.72, 0.72, 0.72, 0.7)
        cr.mask_surface(cairo.ImageSurface.create_from_png(img), x, y)
        cr.fill()                
        
        cr.set_line_width(4)
        cr.set_source_rgba(1, 0, 0, 0.7)
        cr.move_to(x+38-10, y+38-10)
        cr.line_to(x+38+10, y+38+10)
        cr.stroke()
        cr.move_to(x+38-10, y+38+10)
        cr.line_to(x+38+10, y+38-10)        
        cr.stroke()
                
    def draw_dragged_ins(self, cr, i, j, sx, sy):
        #print str(i)+","+str(j)+","+str(sx)+","+str(sy)
        [x0, y0, x1, y1] = self.get_item_bound(i, j)
        name = self.get_drag_ins_name()
        img = Global.get_img_lg_label(name)
        cr.set_source_rgba(0.72, 0.72, 0.72, 0.7)
        cr.mask_surface(cairo.ImageSurface.create_from_png(img), x0+sx, y0+sy)
        cr.fill()        
        
    def draw_ins_list_item(self, cr, i, j): # i: category, j: item
        [x0, y0, x1, y1] = self.get_item_bound(i, j)
        cr.rectangle(x0, y0, x1-x0, y1-y0)
        cr.set_source_rgb(1, 1, 1)
        cr.fill()
        
        cr.set_font_size(12)
        m = j % 5
        d = int(j / 5)
        label = Global.instrument_list[Global.instrument_category[i]][j]
        name = Global.get_name_from_label(label)
        
        is_hover = (i == self.hover_ins_list[0] and j == self.hover_ins_list[1])
        is_selected = self.is_selected_instrument(name)
                       
        img = Global.get_img_med_label(label)
        if not img == 'None':
            self.set_rgba_ins_item_icon(cr, is_hover, is_selected)
            try:
                cr.mask_surface(cairo.ImageSurface.create_from_png(img), Global.instrument_category_x[i]-4 + self.xdiv*d, self.y+78 + self.ydiv*m)
                cr.fill()
            except:
                print img
        self.set_rgba_ins_item_label(cr, is_hover, is_selected)
        self.set_font(cr)
        cr.move_to(Global.instrument_category_x[i] + self.xdiv*d, self.y+78 + self.ydiv*m + 84)
        cr.show_text(label)        
    
    def draw_bottom(self, cr):
        for i in range(self.n_ins):
            self.draw_bottom_ins(cr, i)            
            
    def draw_bottom_ins_temp(self, cr, i, name):
        cr.set_source_rgb(Global.get_color_red_float(i), Global.get_color_green_float(i), Global.get_color_blue_float(i))
        self.create_curvy_rectangle(cr, 29+i*146, self.y+self.sel_y, 123, 123, 12)
        cr.fill()            
        
        if name != "":
            cr.set_source_rgb(0.16, 0.16, 0.16)
            img = Global.get_img_lg_label(name)        
            cr.mask_surface(cairo.ImageSurface.create_from_png(img), 29+i*146 + 12, self.y+self.sel_y + 12)
            cr.fill()    
        
        cr.set_source_rgba(1, 1, 1, 0.7)
        self.create_curvy_rectangle(cr, 29+i*146, self.y+self.sel_y, 123, 123, 12)
        cr.fill()                  
                
    def draw_bottom_ins(self, cr, i):
        cr.set_source_rgb(Global.get_color_red_float(i), Global.get_color_green_float(i), Global.get_color_blue_float(i))
        self.create_curvy_rectangle(cr, 29+i*146, self.y+self.sel_y, 123, 123, 12)
        cr.fill()            
                
        if self.preview_sel_ins == i and self.drag_state != 'sel_ins':
            label = self.get_drag_ins_name()
        else:            
            label = self.instruments[i]
        if label != "" and label != "none":
            cr.set_source_rgb(0.16, 0.16, 0.16)
            img = Global.get_img_lg_label(label)        
            cr.mask_surface(cairo.ImageSurface.create_from_png(img), 29+i*146 + 12, self.y+self.sel_y + 12)
            cr.fill()    
        
        if self.preview_sel_ins == i or self.hover_sel_ins == i:
            cr.set_source_rgba(1, 1, 1, 0.7)
            self.create_curvy_rectangle(cr, 29+i*146, self.y+self.sel_y, 123, 123, 12)
            cr.fill()         
            
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
        
    def set_rgba_ins_item_icon(self, cr, is_hover, is_selected):
        if is_selected == -1:
            if is_hover:
                cr.set_source_rgba(0.72, 0.72, 0.72, 0.7)
            else:
                cr.set_source_rgba(0.4, 0.4, 0.4, 0.7)
        else:
            if is_selected == 2:
                cr.set_source_rgb(0.9*Global.get_color_red_float(is_selected), 0.9*Global.get_color_green_float(is_selected), 0.9*Global.get_color_blue_float(is_selected))
            else:
                cr.set_source_rgb(Global.get_color_red_float(is_selected), Global.get_color_green_float(is_selected), Global.get_color_blue_float(is_selected))
                
    def set_rgba_ins_item_label(self, cr, is_hover, is_selected):
        if is_selected == -1:
            if is_hover:
                cr.set_source_rgba(0.72, 0.72, 0.72, 1)
            else:
                cr.set_source_rgba(0.64, 0.64, 0.64, 1)
        else:
            cr.set_source_rgb(0.6*Global.get_color_red_float(is_selected), 0.6*Global.get_color_green_float(is_selected), 0.6*Global.get_color_blue_float(is_selected)) 
            
    def get_drag_ins_name(self):
        if self.drag_item[0] == -1 or self.drag_item[1] == -1:
            return "none"
        label = Global.instrument_list[Global.instrument_category[self.drag_item[0]]][self.drag_item[1]] # the label of new instrument
        return Global.get_name_from_label(label)         
        
    def set_font(self, cr):
	if self.platform == 'sugar-xo':
	    cr.set_font_face(self.font)
	else:
	    cr.select_font_face(self.font, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)