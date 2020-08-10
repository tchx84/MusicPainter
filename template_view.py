from gi.repository import Gtk
from gi.repository import Gdk

import cairo

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
            self.height = self.height - 75 - 10
        else:
            self.top_bar_height = 75
        
        self.y = self.top_bar_height
    
    def init_data(self):
        self.fix_button = 0
        self.toolbar_expanded = False
    
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
        
        if self.platform == "sugar-xo" and self.toolbar_expanded:
            cr.set_source_surface(self.pixmap, 0, -75)
        else:
            cr.set_source_surface(self.pixmap, 0, 0)
        cr.paint()
    
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
        
        return True
    
    def prepare_bg_pixmap(self):
        cr = cairo.Context(self.bg_pixmap)
        cr.rectangle(0, 0, self.width, self.height)
        cr.set_source_rgb(1, 1, 1)
        cr.fill()
        
        if self.platform != "sugar-xo":
            cr.set_source_rgb(0.16, 0.16, 0.16)
            cr.rectangle(0, self.top_bar_y, self.width, self.top_bar_height)
            cr.fill()               

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
    
    def on_mouse_up_event(self, widget, event):
        self.fix_button = 0
    
    def on_mouse_move_event(self, widget, event):
        x, y = event.x, event.y
        state = event.get_state()
        return True
        
    def toolbar_switch(self):
        self.toolbar_expanded = not self.toolbar_expanded        