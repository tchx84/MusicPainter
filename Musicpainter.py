from gi.repository import Gdk
from gi.repository import Gtk
from gi.repository import GObject
import time
import cairo
from gi.repository import Pango
import random
from random import randrange

from Network import *
from CSoundAgent import *
from CanvasView import *
from DetailView import *
from HomeView import *
from HomeSubView import *
from InstrumentView import *
from PaintScore import *

grid_width = 64
grid_height = 19

platform = "windows"

class Musicpainter:
    def main(self):
	self.platform = platform
	self.username = 'wuhsi_1001'
	toplevel_window = Gtk.Window(Gtk.WindowType.TOPLEVEL)
	if not Gdk.Screen.get_default().get_height() >= 900:
	    toplevel_window.maximize()
	self.init(toplevel_window)
	Gtk.main()
	
    def initSugar(self, toplevel_window, name):
	self.platform = "sugar-xo" #called from MusicpainterActivity, set platform to sugar
	self.username = name
	self.activity = toplevel_window
	self.init(toplevel_window)	
	
    def init(self, toplevel_window):
	self.window = toplevel_window
	
	self.init_network()
	self.init_csound()
	self.init_data()
	self.init_ui()		
		
#	self.score.read_score('test.txt')

    def init_network(self):
	self.network = Network(self) # will attempt login here
	
    def init_csound(self):
	if self.platform == "windows":
	    self.hasCSound = False
	    self.csa = CSoundAgent(self, None, grid_width, grid_height)
	else:
	    import common.Config as Config
	    from common.Generation.GenerationConstants import GenerationConstants
	    from common.Util.NoteDB  import Note
	    from common.Util import NoteDB
	    from common.Util.CSoundNote import CSoundNote
	    from common.Util.CSoundClient import new_csound_client
	    from common.Util import InstrumentDB
	    import Musicpainter_Orchestra
	    self.instrumentDB = InstrumentDB.getRef()
	    self.csound = new_csound_client()
	    time.sleep(0.01)
	    for i in range(21):
		self.csound.setTrackVolume(100, i)
	    self.load_instruments()
	    self.csound.setTempo(90)	    
	    
	    self.noteDB = NoteDB.NoteDB()
	    first_page = self.noteDB.addPage(-1, NoteDB.Page(4, self.instrument_list))   	    
	    self.hasCSound = True	    
	    self.csa = CSoundAgent(self, self.csound, grid_width, grid_height)

    def isPercussion_name(self, name):
	    for ins in Global.drum_kit:
		name = Global.get_name_from_label(name)
		ins_name = Global.get_name_from_label(ins)
		if ins_name == name:
		    return True
	    return False	
	
    def load_instruments(self):
	self.instrument_list = []
	for c in Global.instrument_category:
	    for ins in Global.instrument_list[c]:
		ins_name = Global.get_name_from_label(ins)
		if self.isPercussion_name(ins_name):
		    self.instrument_list.append(self.csound.load_drumkit(ins_name))
		else:
		    self.instrument_list.append(self.csound.load_instrument(ins_name))
    
    def init_dir(self):
	if not os.path.exists(Global.score_folder_local):
	    os.makedirs(Global.score_folder_local)	
        if not os.path.exists(Global.score_folder_download):
	    os.makedirs(Global.score_folder_download)	
        if not os.path.exists(Global.cache_folder):
	    os.makedirs(Global.cache_folder)		
		    
    def init_data(self):
	self.init_dir()
	
	self.score = PaintScore(grid_width, grid_height, self.platform, self)
	self.key_lock = False
	self.toolbar_expanded = False
	self.current_view = "home"	
	return

    def init_ui(self):
	if self.platform == "windows":
	    self.width = 1200
	    if Gdk.Screen.get_default().get_height() >= 900:
		self.height = 900
	    else:		
		self.height = 720
	else:
	    self.width = Gdk.Screen.get_default().get_width()
	    self.height = Gdk.Screen.get_default().get_height()
	
	self.window.set_title("Music Painter")
	self.window.set_name ("Music Painter") # for xo
	self.window.set_resizable(True)	

	self.window.connect("destroy", self.destroy)
	self.window.connect("delete_event", self.delete_event)		
	self.window.connect("key_press_event", self.key_press_event)
	self.window.connect("key_release_event", self.key_release_event)
	
	#self.window.modify_bg(Gtk.STATE_NORMAL, Gdk.Color(10200, 10200, 10200))
	#self.window.modify_bg(Gtk.StateType.NORMAL, Gdk.Color(10200, 10200, 10200))
	
	self.font = Global.init_font(self.platform)
	
	self.prepare_canvas_view()
	self.prepare_detail_view()
	self.prepare_home_view()	
	self.prepare_instrument_view()
	
	if self.platform == "sugar-xo":
	    if self.network.status == 'no_network':
	        self.current_layout = self.home_sub_layout
	    else:
		self.current_layout = self.home_layout
	else:
	    if self.network.status == 'no_network':
	        self.current_layout = self.home_sub_layout
	    else:
		self.current_layout = self.home_layout
	    
	if self.platform == "windows":
	    self.window.add(self.current_layout)
	elif self.platform == "sugar-xo":
	    self.window.set_title("Musicpainter - " + self.username)
	    self.window.set_canvas(self.current_layout)
	self.window.show_all()
	
    def switch_view(self, layout):
	if self.platform == "windows":
	    self.window.remove(self.current_layout)
	self.current_layout = layout
	if self.platform == "sugar-xo":
	    self.window.set_canvas(self.current_layout)	    
	elif self.platform == "windows":
	    self.window.add(self.current_layout)
	self.window.show_all()	
    
    def go_home(self):
	if self.current_view == "home" and (self.current_layout == self.home_layout or self.network.status == 'no_network'):
	    return
	
	if self.network.status == 'no_network':
	    self.home_sub_view.refresh_list()
	    self.switch_view(self.home_sub_layout)	
	    self.home_sub_view.refresh_view()
	else:
	    self.home_view.refresh_list()
	    self.switch_view(self.home_layout)
	    self.home_view.refresh_view()	
	
	self.current_view = "home"	
	
	if self.platform == "sugar-xo" and self.toolbar_expanded:
	    self.activity.activity_btn.set_expanded(False)
	    self.toolbar_expanded = False
	
    def get_current_view(self):
	if self.current_view == "canvas" and self.canvas_view.bottom_bar.is_recording:
	    return "keyboard"
	elif self.current_view == "detail":
	    if self.detail_view.has_list:
		return "home"
	    elif self.canvas_view.bottom_bar.is_recording:
		return "keyboard"
	    else:
		return "canvas"
	else:
	    return self.current_view
	
    def init_view(self, view):
	if view == 'canvas':
	    self.init_canvas_view()
	elif view == 'keyboard':
	    self.init_keyboard_view()
	elif view == 'instruments':
	    self.init_instrument_view()
	
    def to_instrument_view(self):
	if self.current_view == "instruments":
	    return
	self.switch_view(self.instrument_layout)
	self.instrument_view.update_instruments(self.canvas_view.bottom_bar.instruments)
	self.instrument_view.refresh_view()
	self.current_view = "instruments"
	
    def init_instrument_view(self):
	self.switch_view(self.instrument_layout)
	self.current_view = "instruments"
	
    def init_canvas_view(self):
	self.switch_view(self.canvas_layout)
	self.current_view = "canvas"
	    
    def init_keyboard_view(self):
	self.canvas_view.bottom_bar.is_recording = True
	self.canvas_view.bottom_bar.last_looping = self.canvas_view.bottom_bar.is_looping
	self.canvas_view.bottom_bar.last_play_all = self.canvas_view.bottom_bar.play_all	
	self.canvas_view.show_keymap = True
	self.canvas_view.show_pitchmap = False	
	self.switch_view(self.canvas_layout)
	self.current_view = "canvas"
	
    def to_canvas_view(self, filename = ''):
	update = False
	if self.canvas_view.bottom_bar.is_recording:
	    self.canvas_view.bottom_bar.is_recording = False
	    self.canvas_view.update_looping(self.canvas_view.bottom_bar.last_looping)
	    self.canvas_view.update_playall(self.canvas_view.bottom_bar.last_play_all)
	    self.canvas_view.show_keymap = False
	    #self.canvas_view.show_pitchmap = False
	    update = True
	if self.current_view == "canvas":
	    if update:
		self.canvas_view.update_canvas_tag()
#		self.canvas_view.redraw()
	self.switch_view(self.canvas_layout)
	if filename != '':
	    self.score.clear_score()
	if self.current_view == "instruments":
	    self.canvas_view.update_instruments(self.instrument_view.instruments)
	if update:
	    self.canvas_view.redraw()
	else:
	    self.canvas_view.refresh_view()
	self.current_view = "canvas"
	if self.platform == 'sugar-xo' and filename != '':
	    self.activity.set_active_btn('canvas')
	if filename == 'NEW_PAGE': # to create sugar journal entry
	    self.score.new_score()
	elif filename != '':
	    self.score.read_score(filename)
	    self.canvas_view.redraw()
	
    def to_keyboard_mode(self):
	update = False
	if not self.canvas_view.bottom_bar.is_recording:
	    self.canvas_view.bottom_bar.is_recording = True
	    self.canvas_view.bottom_bar.last_looping = self.canvas_view.bottom_bar.is_looping
	    self.canvas_view.bottom_bar.last_play_all = self.canvas_view.bottom_bar.play_all	
	    self.canvas_view.update_playall(True)
	    self.canvas_view.update_looping(True)
	    self.canvas_view.show_keymap = True
	    self.canvas_view.show_pitchmap = False
	    update = True
	if self.current_view == "canvas":
	    if update:
		self.canvas_view.update_canvas_tag()
#		self.canvas_view.redraw()
	    return
	self.switch_view(self.canvas_layout)
	if self.current_view == "instruments":
	    self.canvas_view.update_instruments(self.instrument_view.instruments)
	if update:
	    self.canvas_view.redraw()
	else:
	    self.canvas_view.refresh_view()
	self.current_view = "canvas"
	
    def to_detail_mode_from_sugar(self):
	self.toolbar_expanded = not self.toolbar_expanded
	#if self.toolbar_expanded:
	#    print "to detail mode, toolbar expanded: true"
	#else:
	#    print "to detail mode, toolbar expanded: false"
	if self.toolbar_expanded:
	    self.last_view = self.current_view
	    self.detail_view.score = self.score
	    self.detail_view.score.instruments = self.canvas_view.bottom_bar.instruments;
	    self.detail_view.hasList = False
	    self.switch_view(self.detail_layout)
	    self.detail_view.set_toolbar_expanded(True)
	    self.current_view = "detail"
	    return False
	else:
	    if self.platform == "sugar-xo":
	        self.activity.activity_btn.set_expanded(False)	    
	    self.detail_view.set_toolbar_expanded(False)
	    if self.last_view == 'canvas':
		self.to_canvas_view()
		return True
	    elif self.last_view == 'instrument':
		self.to_instrument_view()
		return False
	    elif self.last_view == 'home':
		self.go_home()
		return False
	    elif self.last_view == 'keyboard':
		self.to_keyboard_mode()
		return True
		
    def to_detail_mode_from_home(self, filename, slist, sid, category):	
	self.switch_view(self.detail_layout)
	
	self.detail_view.set_toolbar_expanded(self.toolbar_expanded)
	self.detail_view.init_score(filename, slist, sid, category)
	self.detail_view.redraw()
	self.current_view = "detail"	
	
    def to_homesub_mode_from_home(self, category):
	self.home_sub_view.set_category(category)
	self.switch_view(self.home_sub_layout)
		
    def choose_scale(self):
	if not self.current_view == "canvas":
	    return	
	self.canvas_view.scale_view()	
	
    def toolbar_switch(self):
	self.toolbar_expanded = not self.toolbar_expanded
	if self.toolbar_expanded:
	    print "toolbar expanded: true"
	else:
	    print "toolbar expanded: false"
	    
	#self.canvas_view.toolbar_switch()
	#self.instrument_view.toolbar_switch()
	#self.home_view.toolbar_switch()
	
    def prepare_home_view(self):
	self.home_view = HomeView(self.width, self.height, self.platform, self)
	self.home_layout = Gtk.Fixed()
	self.home_layout.put(self.home_view, 0, 0)
	
	self.home_sub_view = HomeSubView(self.width, self.height, self.platform, self)
	self.home_sub_layout = Gtk.Fixed()
	self.home_sub_layout.put(self.home_sub_view, 0, 0)
	
    def prepare_canvas_view(self):
	self.canvas_view = CanvasView(self.width, self.height, grid_width, grid_height, self.platform, self)
	self.canvas_layout = Gtk.Fixed()
        self.canvas_layout.put(self.canvas_view, 0, 0)
	
    def prepare_detail_view(self):
	self.detail_view = DetailView(self.width, self.height, grid_width, grid_height, self.platform, self)
	self.detail_layout = Gtk.Fixed()
	self.detail_layout.put(self.detail_view, 0, 0)

    def prepare_instrument_view(self):
	self.instrument_view = InstrumentView(self.width, self.height, self.platform, self)
	self.instrument_layout = Gtk.Fixed()
        self.instrument_layout.put(self.instrument_view, 0, 0)
    
    def destroy(self, widget, data=None):
	self.home_view.save_cache()
	#self.logout(self.logout_finished)
	Gtk.main_quit()
    
    def delete_event(self, widget, event, data=None):
	#self.logout(self.logout_finished)
	Gtk.main_quit()	

    def key_press_event(self, widget, event):
	if self.toolbar_expanded and not event.state & Gdk.ModifierType.CONTROL_MASK:
	    return
        if self.key_lock == 1:
            return
        keyname = Gdk.keyval_name(event.keyval)
	#print keyname + "," + str(event.state)
        if event.state & Gdk.ModifierType.CONTROL_MASK:
            self.press_ctrl = 1
	    if keyname == '1':
 	        self.to_detail_mode_from_sugar()
	    elif keyname == '2':
	        self.go_home()
            elif keyname == '3':
		self.to_canvas_view()
	    elif keyname == '4':
		self.to_keyboard_mode()		
	    elif keyname == '5':
		self.to_instrument_view()
	    elif keyname == '6' and self.current_layout == self.canvas_layout:
		self.choose_scale()
	    elif keyname == 'l' or keyname == 'L':
		if self.canvas_view.show_time_grid_line == 0:
		    self.canvas_view.show_time_grid_line = 8
		elif self.canvas_view.show_time_grid_line == 8:
		    self.canvas_view.show_time_grid_line = 4
		elif self.canvas_view.show_time_grid_line == 4:
		    self.canvas_view.show_time_grid_line = 2
		elif self.canvas_view.show_time_grid_line == 2:
		    self.canvas_view.show_time_grid_line = 1
		else:
		    self.canvas_view.show_time_grid_line = 0
		self.canvas_view.refresh_view()
	    elif keyname == 'p' or keyname == 'P':
		self.canvas_view.show_pitchmap = not self.canvas_view.show_pitchmap
		self.canvas_view.refresh_view()
	    elif keyname == 'k' or keyname == 'K':
		self.canvas_view.show_keymap = not self.canvas_view.show_keymap
		self.canvas_view.refresh_view()	    
	    elif keyname == 's' or keyname == 'S':
		name = Global.score_folder_local + str(randrange(100))
		self.score.write_score(name + ".mp")
		self.canvas_view.save_thumb(name + ".png")		
            elif keyname == 'Control_L':
                self.canvas_view.set_aim(True)
            return
	if self.current_layout == self.canvas_layout:
	    if not self.canvas_view.is_scale_bar_visible:		
		if keyname == 'z' or keyname == 'Z':
		    self.csa.keyboard_press(self.canvas_view.bottom_bar.active_instrument, 18)
		elif keyname == 'x' or keyname == 'X':
		    self.csa.keyboard_press(self.canvas_view.bottom_bar.active_instrument, 17)
		elif keyname == 'c' or keyname == 'C':
		    self.csa.keyboard_press(self.canvas_view.bottom_bar.active_instrument, 16)		    
		elif keyname == 'v' or keyname == 'V':
		    self.csa.keyboard_press(self.canvas_view.bottom_bar.active_instrument, 15)		    
		elif keyname == 'b' or keyname == 'B':
		    self.csa.keyboard_press(self.canvas_view.bottom_bar.active_instrument, 14)		    
		elif keyname == 'n' or keyname == 'N':
		    self.csa.keyboard_press(self.canvas_view.bottom_bar.active_instrument, 13)		    
		elif keyname == 'm' or keyname == 'M':
		    self.csa.keyboard_press(self.canvas_view.bottom_bar.active_instrument, 12)		    
		elif keyname == 'comma':
		    self.csa.keyboard_press(self.canvas_view.bottom_bar.active_instrument, 11)		    
		elif keyname == 'a' or keyname == 'A':
		    self.csa.keyboard_press(self.canvas_view.bottom_bar.active_instrument, 11)		    
		elif keyname == 'period':
		    self.csa.keyboard_press(self.canvas_view.bottom_bar.active_instrument, 10)		    
		elif keyname == 's' or keyname == 'S':
		    self.csa.keyboard_press(self.canvas_view.bottom_bar.active_instrument, 10)		    
		elif keyname == 'd' or keyname == 'D':
		    self.csa.keyboard_press(self.canvas_view.bottom_bar.active_instrument, 9)		    
		elif keyname == 'f' or keyname == 'F':
		    self.csa.keyboard_press(self.canvas_view.bottom_bar.active_instrument, 8)
		elif keyname == 'g' or keyname == 'G':
		    self.csa.keyboard_press(self.canvas_view.bottom_bar.active_instrument, 7)		    
		elif keyname == 'h' or keyname == 'H':
		    self.csa.keyboard_press(self.canvas_view.bottom_bar.active_instrument, 6)		    
		elif keyname == 'j' or keyname == 'J':
		    self.csa.keyboard_press(self.canvas_view.bottom_bar.active_instrument, 5)		    
		elif keyname == 'k' or keyname == 'K':
		    self.csa.keyboard_press(self.canvas_view.bottom_bar.active_instrument, 4)		    
		elif keyname == 'q' or keyname == 'Q':
		    self.csa.keyboard_press(self.canvas_view.bottom_bar.active_instrument, 4)		    
		elif keyname == 'l' or keyname == 'L':
		    self.csa.keyboard_press(self.canvas_view.bottom_bar.active_instrument, 3)		    
		elif keyname == 'w' or keyname == 'W':
		    self.csa.keyboard_press(self.canvas_view.bottom_bar.active_instrument, 3)		    
		elif keyname == 'e' or keyname == 'E':
		    self.csa.keyboard_press(self.canvas_view.bottom_bar.active_instrument, 2)		    
		elif keyname == 'r' or keyname == 'R':
		    self.csa.keyboard_press(self.canvas_view.bottom_bar.active_instrument, 1)		    
		elif keyname == 't' or keyname == 'T':
		    self.csa.keyboard_press(self.canvas_view.bottom_bar.active_instrument, 0)	
		elif keyname == '1':
		    self.canvas_view.select_instrument(0)
		elif keyname == '2':
		    self.canvas_view.select_instrument(1)		    
		elif keyname == '3':
		    self.canvas_view.select_instrument(2)		    
		elif keyname == '4':
		    self.canvas_view.select_instrument(3)		    
		elif keyname == '5':
		    self.canvas_view.select_instrument(4)		    
		elif keyname == '6':
		    self.canvas_view.select_instrument(5)		    
		elif keyname == '7':
		    self.canvas_view.select_instrument(6)		    
		elif keyname == '8':
		    self.canvas_view.select_instrument(7)
		elif keyname == 'space':
		    if self.csa.play_state == 'play':
			self.canvas_view.stop_playing()
	   	    elif self.csa.play_state == 'stop':
			self.canvas_view.start_playing()
		elif keyname == 'Left':
		    self.canvas_view.change_tempo(-0.05)
		elif keyname == 'Right':
		    self.canvas_view.change_tempo(0.05)
		elif keyname == 'Up':
		    self.canvas_view.shift_pitch(1)
		    self.canvas_view.update_canvas_tag()
		elif keyname == 'Down':
		    self.canvas_view.shift_pitch(-1)
		    self.canvas_view.update_canvas_tag()
		elif keyname == 'Control_L':
 		    self.canvas_view.set_aim(True)
		#else: 
		#    print keyname		    
	    else: # scale box is visible
		if keyname == '1':
		    self.canvas_view.select_scale(0)		
		elif keyname == '2':
		    self.canvas_view.select_scale(1) 
		elif keyname == '3':
		    self.canvas_view.select_scale(2) 
		elif keyname == '4':
		    self.canvas_view.select_scale(3) 
		elif keyname == '5':
		    self.canvas_view.select_scale(4) 
		elif keyname == '6':
		    self.canvas_view.select_scale(5) 
		elif keyname == 'Left' and self.score.scale_mode != 0:
		    self.canvas_view.select_scale(self.score.scale_mode-1) 		    
		elif keyname == 'Right' and self.score.scale_mode != 5:
		    self.canvas_view.select_scale(self.score.scale_mode+1) 		    		
        if self.current_layout == self.detail_layout:
	    if keyname == 'Left':
		self.detail_view.rewind()
	    elif keyname == 'Right':
		self.detail_view.forward()
	    elif keyname == 'space':
		if self.csa.play_state == 'play':
		    self.canvas_view.stop_playing()
		elif self.csa.play_state == 'stop':
		    self.canvas_view.start_playing()

    def key_release_event(self, widget, event):
        if self.key_lock == 1 or self.toolbar_expanded:
            return
	if not (event.state & Gdk.ModifierType.CONTROL_MASK):
	    self.press_ctrl = 0
        keyname = Gdk.keyval_name(event.keyval)
	if keyname == 'Control_L':
	    self.canvas_view.set_aim(False)	
	if self.current_layout == self.canvas_layout:
	    if not self.canvas_view.is_scale_bar_visible:
		#if Gdk.ModifierType.CONTROL_MASK:
		    #print keyname + "," + str(event.state)		
		if keyname == 'z' or keyname == 'Z':
		    self.csa.keyboard_release(self.canvas_view.bottom_bar.active_instrument, 18)
		elif keyname == 'x' or keyname == 'X':
		    self.csa.keyboard_release(self.canvas_view.bottom_bar.active_instrument, 17)
		elif keyname == 'c' or keyname == 'C':
		    self.csa.keyboard_release(self.canvas_view.bottom_bar.active_instrument, 16)		    
		elif keyname == 'v' or keyname == 'V':
		    self.csa.keyboard_release(self.canvas_view.bottom_bar.active_instrument, 15)		    
		elif keyname == 'b' or keyname == 'B':
		    self.csa.keyboard_release(self.canvas_view.bottom_bar.active_instrument, 14)		    
		elif keyname == 'n' or keyname == 'N':
		    self.csa.keyboard_release(self.canvas_view.bottom_bar.active_instrument, 13)		    
		elif keyname == 'm' or keyname == 'M':
		    self.csa.keyboard_release(self.canvas_view.bottom_bar.active_instrument, 12)		    
		elif keyname == 'comma':
		    self.csa.keyboard_release(self.canvas_view.bottom_bar.active_instrument, 11)		    
		elif keyname == 'a' or keyname == 'A':
		    self.csa.keyboard_release(self.canvas_view.bottom_bar.active_instrument, 11)		    
		elif keyname == 'period':
		    self.csa.keyboard_release(self.canvas_view.bottom_bar.active_instrument, 10)		    
		elif keyname == 's' or keyname == 'S':
		    self.csa.keyboard_release(self.canvas_view.bottom_bar.active_instrument, 10)		    
		elif keyname == 'd' or keyname == 'D':
		    self.csa.keyboard_release(self.canvas_view.bottom_bar.active_instrument, 9)		    
		elif keyname == 'f' or keyname == 'F':
		    self.csa.keyboard_release(self.canvas_view.bottom_bar.active_instrument, 8)
		elif keyname == 'g' or keyname == 'G':
		    self.csa.keyboard_release(self.canvas_view.bottom_bar.active_instrument, 7)		    
		elif keyname == 'h' or keyname == 'H':
		    self.csa.keyboard_release(self.canvas_view.bottom_bar.active_instrument, 6)		    
		elif keyname == 'j' or keyname == 'J':
		    self.csa.keyboard_release(self.canvas_view.bottom_bar.active_instrument, 5)		    
		elif keyname == 'k' or keyname == 'K':
		    self.csa.keyboard_release(self.canvas_view.bottom_bar.active_instrument, 4)		    
		elif keyname == 'q' or keyname == 'Q':
		    self.csa.keyboard_release(self.canvas_view.bottom_bar.active_instrument, 4)		    
		elif keyname == 'l' or keyname == 'L':
		    self.csa.keyboard_release(self.canvas_view.bottom_bar.active_instrument, 3)		    
		elif keyname == 'w' or keyname == 'W':
		    self.csa.keyboard_release(self.canvas_view.bottom_bar.active_instrument, 3)		    
		elif keyname == 'e' or keyname == 'E':
		    self.csa.keyboard_release(self.canvas_view.bottom_bar.active_instrument, 2)		    
		elif keyname == 'r' or keyname == 'R':
		    self.csa.keyboard_release(self.canvas_view.bottom_bar.active_instrument, 1)		    
		elif keyname == 't' or keyname == 'T':
		    self.csa.keyboard_release(self.canvas_view.bottom_bar.active_instrument, 0)	
		    
if __name__ == "__main__":
    musicpainter = Musicpainter()
    musicpainter.main()   
