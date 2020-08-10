from gi.repository import Gtk
from gi.repository import GObject
#import gtk
import cairo
from math import *
from Musicpainter import *
import Global
from random import randrange

class BToolbar():
    def __init__(self, width, height, y, main):
        self.width = width
        self.height = height
        self.y = y
        self.main = main
                       
        self.n_ins = 8
        self.circle_r = 55
        self.circle_sh = 44
        self.toolset_div = 67
        #self.toolset_div = 58
        self.init_random_instruments()
        #self.instruments = ['piano', 'banjo', 'flute', 'clarinette', 'flugel', 'trumpet', 'tuba', 'jazzrock']
        #self.instruments = ['koto', 'rhodes', 'sarangi', 'african', 'arabic', 'electronic', 'southamerican', 'nepali']
        #self.instruments = ['guit', 'guit2', 'guitmute', 'guitshort', 'basse', 'piano', 'jazzrock', 'electronic']
        
        self.tools = ['write', 'eraser', 'forte', 'piano', 'cut', 'loop', 'section']
        #self.tools = ['write', 'eraser', 'forte', 'piano', 'select', 'cut', 'loop', 'section']
        
        self.tempo_r = 0.5
        self.is_playing = False
        self.is_looping = False
        self.is_recording = False
        self.play_all = False
        self.last_play_all = False
        self.last_looping = False
        self.active_tool_index = 0
        self.active_instrument = 0
        
        self.hover_tool_index = -1
        self.hover_instrument = -1
        self.hover_center = -1
        self.hover_tempo_slider = -1
        
        self.clickPending = "off"
        self.threshold = 300 # tap < 300 ms
        self.tooltip_threshold = 640 
        self.move_threshold = 50
        
        self.tooltip_target = 'none'
        self.tooltip_state = -1
        self.tooltip_cx = -1
        
    def get_one_instrument(self):
        n = len(Global.instrument_all_list)
        ins = Global.instrument_all_list[randrange(n)]
        for eins in self.instruments:        
            if eins == ins:
                return self.get_one_instrument()
        return ins
        
    def init_random_instruments(self):
        self.instruments = []
        for i in range(self.n_ins):
            self.instruments.append(self.get_one_instrument())

    def on_mouse_down_event(self, cr, mx, my):  # call after ensuring the cursor in bound
        self.handle_tooltip()
        i = self.on_instrument(mx, my)
        if i != -1:
            return self.to_select_instrument(cr, i)
        i = self.on_toolset(mx, my)
        if i != -1:
            if i == 5:
                self.is_looping = not self.is_looping
                self.draw_toolset(cr)
                return 1
            elif i == 6:
                if self.is_recording:
                    return 0
                self.play_all = not self.play_all
                self.draw_toolset(cr)
                return 1
            else:
                if self.active_tool_index != i:
                    self.active_tool_index = i
                    self.draw_toolset(cr)  
                    return 1
                return 0
        i = self.on_center_button(mx, my)
        if i == 1:
            self.clickTimer = GObject.timeout_add(self.threshold, self.clickTimeout)
            self.clickPending = "wait"
            self.init_tempo_r = self.tempo_r
            (self.drag_x, self.drag_y) = (mx, my)
            return 0
        return 0
    
    def to_select_instrument(self, cr, i):
        if self.active_instrument != i:
            self.main.csa.turnoff_existing_keys()
        if self.main.hasCSound:
            self.main.csa.note_on(i+1, 60+self.main.score.score_shift, 1)          
        if self.active_instrument != i:                
            self.active_instrument = i
            self.draw_instruments(cr)
            if self.active_tool_index != 0:
                self.active_tool_index = 0
                self.draw_toolset(cr)                      
            return 2
        elif self.active_tool_index != 0:
            self.active_tool_index = 0
            self.draw_toolset(cr)                
            return 1
        return 0
    
    def clickTimeout(self):        
        GObject.source_remove(self.clickTimer)
        self.clickPending = "timeout"
    
    def on_mouse_up_event(self, cr, mx, my):
        update = 0        
        self.handle_tooltip()
        if self.clickPending != "off":
            GObject.source_remove(self.clickTimer)
        if self.clickPending == "wait":   # tap
            if self.is_playing:
                self.main.csa.stop_music()
                self.set_play(False)
                self.draw_center(cr)
                update = 1
            else:
                if self.main.csa.play_music():
                    self.set_play(True)
                    self.draw_center(cr)
                    update = 1
        self.clickPending = "off"
        return update
    
    def on_mouse_move_event(self, cr, mx, my):  # call after ensuring the cursor in bound
        update = False
        if self.clickPending != "off":
            if abs(mx - self.drag_x) > self.move_threshold:
                self.clickPending = "move"
            r = self.init_tempo_r + (mx - self.drag_x) / 600
            return self.set_tempo(cr, r)
        i1 = self.on_instrument(mx, my)
        if i1 != self.hover_instrument:
            self.hover_instrument = i1
            self.draw_instruments(cr)
            update = True                        
        i2 = self.on_toolset(mx, my)
        if i2 != self.hover_tool_index:
            self.hover_tool_index = i2
            self.draw_toolset(cr)        
            update = True
        i3 = self.on_center_button(mx, my)
        if i3 != self.hover_center:
            self.hover_center = i3
            self.draw_center(cr)        
            update = True
        if self.clickPending == 'off':
            self.handle_tooltip_move(i1, i2, i3)
        return update
    
    def handle_tooltip(self):
        if self.tooltip_state == 'wait':
            GObject.source_remove(self.tooltip_timer)
        if self.tooltip_state != 'none':
            self.tooltip_state = 'none'        
            self.tooltip_target = ''
            self.main.canvas_view.update_tooltip('none', self.tooltip_cx)            
    
    def handle_tooltip_move(self, i1, i2, i3):                
        if i1 != -1 and self.tooltip_target != self.instruments[i1]:
            self.tooltip_target = self.instruments[i1]
            self.tooltip_cx = 678+i1*60+26
            if self.tooltip_state == 'none':
                self.tooltip_state = 'wait'
                self.tooltip_timer = GObject.timeout_add(self.tooltip_threshold, self.tooltip_show)
            elif self.tooltip_state == 'wait':
                GObject.source_remove(self.tooltip_timer)
                self.tooltip_timer = GObject.timeout_add(self.tooltip_threshold, self.tooltip_show)                
            elif self.tooltip_state == 'show':
                self.main.canvas_view.update_tooltip(self.tooltip_target, self.tooltip_cx)
        elif i2 != -1 and self.tooltip_target != Global.toolset_tooltip[i2]:
            self.tooltip_target = Global.toolset_tooltip[i2]
            self.tooltip_cx = 48+i2*self.toolset_div+23
            if self.tooltip_state == 'none':
                self.tooltip_state = 'wait'
                self.tooltip_timer = GObject.timeout_add(self.tooltip_threshold, self.tooltip_show)            
            elif self.tooltip_state == 'wait':
                GObject.source_remove(self.tooltip_timer)
                self.tooltip_timer = GObject.timeout_add(self.tooltip_threshold, self.tooltip_show)
            elif self.tooltip_state == 'show':
                self.main.canvas_view.update_tooltip(self.tooltip_target, self.tooltip_cx)
        elif i3 != -1 and self.tooltip_target != 'play':
            self.tooltip_target = 'play'
            self.tooltip_cx = self.width/2
            if self.tooltip_state == 'none':
                self.tooltip_state = 'wait'            
                self.tooltip_timer = GObject.timeout_add(self.tooltip_threshold, self.tooltip_show)                        
            elif self.tooltip_state == 'wait':
                GObject.source_remove(self.tooltip_timer)
                self.tooltip_timer = GObject.timeout_add(self.tooltip_threshold, self.tooltip_show)                        
            elif self.tooltip_state == 'show':
                self.main.canvas_view.update_tooltip(self.tooltip_target, self.tooltip_cx)
        elif i1 == -1 and i2 == -1 and i3 == -1:
            self.handle_tooltip()
                
    def tooltip_show(self):        
        GObject.source_remove(self.tooltip_timer)
        self.tooltip_state = 'show'
        self.main.canvas_view.update_tooltip(self.tooltip_target, self.tooltip_cx)
    
    def on_toolset(self, mx, my):
        for i in range(len(Global.toolset_icons)):
            if 48+self.toolset_div*i <= mx and self.y+24 <= my and mx < 48+i*self.toolset_div+46 and my < self.y+24+44:
                return i                    
        return -1
    
    def on_instrument(self, mx, my):
        for i in range(self.n_ins):
            if 678+i*60 <= mx and self.y+21 <= my and mx < 678+i*60+52 and my < self.y+21+52:
                return i
        return -1    
    
    def on_center_button(self, mx, my):
        r = self.circle_r - 31 # -12 - 10 - 9 = -31
        d = sqrt((self.width / 2 - mx) * (self.width / 2 - mx) + (self.y + self.circle_sh - my) * (self.y + self.circle_sh - my))
        if d <= self.circle_r - 6:
            return 1
        return -1
    
    def is_inbound(self, mx, my):
        return self.y <= my and my < self.y + self.height;
    
    def leave(self, cr):
        self.handle_tooltip()
        update = False
        if self.hover_instrument != -1:
            self.hover_instrument = -1
            self.draw_instruments(cr)
            update = True
        if self.hover_tool_index != -1:
            self.hover_tool_index = -1
            self.draw_toolset(cr)
            update = True
        if self.hover_center != -1:
            self.hover_center = -1
            self.draw_center(cr)
            update = True
        return update
        
    def draw(self, cr):  
        self.draw_background(cr)
        self.draw_toolset(cr)        
        self.draw_center(cr, True)
        self.draw_instruments(cr)
        
    def draw_background(self, cr):
        cr.set_line_width(1)   
        cr.set_source_rgb(0.16, 0.16, 0.16)
        cr.rectangle(0, self.y, self.width, self.height)
        cr.fill() 
        
    def draw_toolset(self, cr):
        cr.set_source_rgb(0.3984, 0.3984, 0.3984)
        self.create_curvy_rectangle(cr, 34, self.y+18, 490, 58, 20)
        cr.fill()
        
        for i in range(len(Global.toolset_icons)):
            if (i < 5 and i == self.active_tool_index) or (i == 5 and self.is_looping) or (i == 6 and self.play_all):
                if i == self.hover_tool_index:
                    cr.set_source_rgba(1, 1, 1, 0.5)
                else:
                    cr.set_source_rgb(1, 1, 1)
            else:
                if i == self.hover_tool_index:
                    cr.set_source_rgba(0.16, 0.16, 0.16, 0.5)
                else:
                    cr.set_source_rgb(0.16, 0.16, 0.16)
            if i == 0:
                cr.mask_surface(cairo.ImageSurface.create_from_png(Global.toolset_icons[i]), 33+self.toolset_div*i+4, self.y+8+1)
            elif i == 1:
                cr.mask_surface(cairo.ImageSurface.create_from_png(Global.toolset_icons[i]), 33+self.toolset_div*i-1, self.y+8+3)
            else:
                cr.mask_surface(cairo.ImageSurface.create_from_png(Global.toolset_icons[i]), 33+self.toolset_div*i, self.y+8)
            cr.fill()                                                       
    
    def draw_instruments(self, cr):
        for i in range(self.n_ins):
#            if i == self.active_instrument:
            #cr.set_source_rgb(Global.colors[i].red_float, Global.colors[i].green_float, Global.colors[i].blue_float)
            cr.set_source_rgb(Global.get_color_red_float(i), Global.get_color_green_float(i), Global.get_color_blue_float(i))
#            else:
#                cr.set_source_rgb(0.4, 0.4, 0.4)
            self.create_curvy_rectangle(cr, 678+i*60, self.y+21, 52, 52, 4)
            cr.fill()            
            if i == self.active_instrument:
                cr.set_source_rgb(1, 1, 1)
                cr.set_line_width(2)
                self.create_curvy_rectangle(cr, 678+i*60+1, self.y+21+1, 50, 50, 4)
                cr.stroke()
            if i == self.active_instrument:
                cr.set_source_rgb(1, 1, 1)
            else:
                cr.set_source_rgb(0.16, 0.16, 0.16)
#                cr.set_source_rgb(0.32, 0.32, 0.32)
            label = self.instruments[i]
            img = Global.get_img_sm_label(label)                        
            cr.mask_surface(cairo.ImageSurface.create_from_png(img), 678+i*60 + 4, self.y+21 + 4)
            cr.fill()            
            if i == self.hover_instrument:
                cr.set_source_rgba(1, 1, 1, 0.5)
                self.create_curvy_rectangle(cr, 678+i*60, self.y+21, 52, 52, 4)
                cr.fill()
        
    def draw_center(self, cr, from_draw = False):  
        r = self.circle_r        # draw a circle first
        cr.set_source_rgb(0.3984, 0.3984, 0.3984)   #
        cr.arc(self.width / 2, self.y + self.circle_sh, r, 0, 2 * pi)
        cr.fill()
        
        lw = 10                 # draw the ring
        beg = 0.80*pi  #0.75*pi
        end = 2.20*pi  #2.25*pi
        area = 1.4*pi  #1.5*pi
        cr.set_line_width(lw)
        cr.set_source_rgb(1, 1, 1)
        cr.arc(self.width / 2, self.y + self.circle_sh, r - 12 - lw/2, beg, beg + area*self.tempo_r)
        cr.stroke()   
        cr.set_source_rgb(0.157, 0.157, 0.157)
        cr.arc(self.width / 2, self.y + self.circle_sh, r - 12 - lw/2, beg + area*self.tempo_r, end)
        cr.stroke()
        
        if self.hover_center >= 2:
            h = (self.hover_center - 2)
            if h < self.tempo_r:
                cr.set_source_rgba(0.5, 0.5, 0.5, 0.7)
                cr.arc(self.width / 2, self.y + self.circle_sh, r - 12 - lw/2, beg, beg + area*h)
                cr.stroke()
            else:
                cr.set_source_rgba(0.5, 0.5, 0.5, 0.7)
                cr.arc(self.width / 2, self.y + self.circle_sh, r - 12 - lw/2, beg, beg + area*self.tempo_r)
                cr.stroke()                
                cr.set_source_rgba(1, 1, 1, 0.8)
                cr.arc(self.width / 2, self.y + self.circle_sh, r - 12 - lw/2, beg + area*self.tempo_r, beg + area*h)
                cr.stroke()                                
        cr.set_source_rgb(0.157, 0.157, 0.157)
        cr.arc(self.width / 2, self.y + self.circle_sh, r - 12 - lw - 9, 0, 2 * pi)
        cr.fill()        
        
        r2 = self.circle_r - 12
        r1 = r2 - 10
        d = area/4
        cr.set_source_rgb(0.3984, 0.3984, 0.3984)
        for i in range(3):
            cr.set_line_width(0.25)            
            cr.move_to(self.width / 2 + r1 * cos(beg+(i+1)*d), self.y + self.circle_sh + r1 * sin(beg+(i+1)*d))
            cr.line_to(self.width / 2 + r2 * cos(beg+(i+1)*d), self.y + self.circle_sh + r2 * sin(beg+(i+1)*d))
            cr.stroke()            
        
        if self.is_playing:
            self.draw_stop_button(cr)        
        else:
            self.draw_play_button(cr)   
            
        if self.hover_center == 1:
            cr.set_source_rgba(1, 1, 1, 0.5)
            cr.arc(self.width / 2, self.y + self.circle_sh, r - 12 - lw - 9, 0, 2 * pi)
            cr.fill()                    
            
        cr.set_source_rgb(1, 1, 1)
        img_t = cairo.ImageSurface.create_from_png(Global.tempo_icons['turtle'])
        cr.mask_surface(img_t, self.width / 2 - 34, self.y + self.circle_sh+22)
        cr.fill()
        
        img_r = cairo.ImageSurface.create_from_png(Global.tempo_icons['rabbit'])
        cr.mask_surface(img_r, self.width / 2 + 11, self.y + self.circle_sh+21)
        cr.fill()
            
    def draw_play_button(self, cr):
        cr.set_source_rgb(1, 1, 1)
        cr.move_to(self.width/2-12+1, self.y+self.circle_sh-19+1+5)
        cr.line_to(self.width/2-12+1, self.y+self.circle_sh+8-1+5)
        cr.line_to(self.width/2+17-1, self.y+self.circle_sh-3-1+5)
        cr.close_path()
        cr.fill()        
        
    def draw_stop_button(self, cr):
        r = 18
        cr.set_source_rgb(1, 1, 1)
        cr.rectangle(self.width / 2 - r / 2, self.y + self.circle_sh - r / 2, r, r)
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
        #cr.line_to(x1+r, y1)
        cr.close_path()        
            
    def set_play(self, p):
        if self.is_playing != p:
            self.is_playing = p
            return True
        return False
    
    def set_tempo(self, cr, r):
        if r > 1:
            r = 1
        if r < 0:
            r = 0
        if r == self.tempo_r:
            return False
        if int(r*100) == int(self.tempo_r):
            return False
        self.tempo_r = 0.01*int(r*100)
        self.main.csa.setTempo()
        self.draw_center(cr)
        return True
        
    def change_tempo(self, cr, d):
        return self.set_tempo(cr, self.tempo_r+d)