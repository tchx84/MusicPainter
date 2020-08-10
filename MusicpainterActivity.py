from gi.repository import Gtk
from sugar3.presence import presenceservice
from sugar3.graphics.toolbarbox import ToolbarBox, ToolbarButton
from sugar3.activity import activity
from sugar3.graphics.toolbutton import ToolButton
from sugar3.activity.widgets import ActivityToolbarButton
from sugar3.graphics.radiotoolbutton import RadioToolButton
from sugar3.graphics.toggletoolbutton import ToggleToolButton
from sugar3.activity.widgets import StopButton
from sugar3.datastore import datastore
import dbus

DS_DBUS_SERVICE = 'org.laptop.sugar.DataStore'
DS_DBUS_INTERFACE = 'org.laptop.sugar.DataStore'
DS_DBUS_PATH = '/org/laptop/sugar/DataStore'

import Global
import Musicpainter

class MusicpainterActivity(activity.Activity):
    def __init__(self, handle):
	
	self.to_read = ''
	self.btn_added = False
	
        activity.Activity.__init__(self, handle)
	self.max_participants = 1
	
        self.connect('destroy', self._cleanup_cb)

        #load the sugar toolbar
        self.toolbar_box = ToolbarBox()
	
	self.activity_btn = ActivityToolbarButton(self)
	self.activity_btn.connect('clicked', self.to_detail_mode)
	
	self.new_file_btn = ToolButton('file_new')
	self.new_file_btn.set_tooltip('New')
	self.new_file_btn.connect('clicked', self.new_file)
	
	self.save_file_btn = ToolButton('file_save')
	self.save_file_btn.set_tooltip('Save')
	self.save_file_btn.connect('clicked', self.save_file)
	
	self.save_file_as_btn = ToolButton('file_save_as')
	self.save_file_as_btn.set_tooltip('Save As')	
	self.save_file_as_btn.connect('clicked', self.save_file_as)

	self.share_file_btn = ToolButton('file_upload')
	self.share_file_btn.set_tooltip('Share')	
	self.share_file_btn.connect('clicked', self.share_file)
	
	separator = Gtk.SeparatorToolItem()
	separator.show()
	
	toolbar = self.activity_btn.props.page
	self.title_box = toolbar.get_nth_item(0)
	self.desc_btn = toolbar.get_nth_item(1)
	toolbar.insert(separator, 2)
	toolbar.insert(self.new_file_btn, -1)
	toolbar.insert(self.save_file_btn, -1)
	toolbar.insert(self.save_file_as_btn, -1)	
	toolbar.insert(self.share_file_btn, -1)
	
	self.toolbar_box.toolbar.insert(self.activity_btn, 0)
	
	self.toolbar_box.toolbar.insert(Gtk.SeparatorToolItem(), 1)

	self.home_btn = RadioToolButton()
	self.home_btn.set_tooltip('Home')
	self.home_btn.props.icon_name = 'toolbox_home'
	self.home_btn.props.group = self.home_btn
	self.home_btn.connect('clicked', self.go_home)
	self.toolbar_box.toolbar.insert(self.home_btn, 2)

	self.canvas_mode_btn = RadioToolButton()
	self.canvas_mode_btn.set_tooltip('Canvas')
	self.canvas_mode_btn.props.icon_name = 'toolbox_canvas'
	self.canvas_mode_btn.props.group = self.home_btn
	self.canvas_mode_btn.connect('clicked', self.to_canvas_mode)
	self.toolbar_box.toolbar.insert(self.canvas_mode_btn, 3)
	
	self.keyboard_mode_btn = RadioToolButton()
	self.keyboard_mode_btn.set_tooltip('Keyboard')
	self.keyboard_mode_btn.props.icon_name = 'toolbox_keyboard'
	self.keyboard_mode_btn.props.group = self.home_btn
	self.keyboard_mode_btn.connect('clicked', self.to_keyboard_mode)
	self.toolbar_box.toolbar.insert(self.keyboard_mode_btn, 4)

	self.configure_ins_btn = RadioToolButton()
	self.configure_ins_btn.set_tooltip('Select instruments')
	self.configure_ins_btn.props.icon_name = 'toolbox_instrument'
	self.configure_ins_btn.props.group = self.home_btn
	self.configure_ins_btn.connect('clicked', self.configure_ins)
	self.toolbar_box.toolbar.insert(self.configure_ins_btn, 5)

        self.seperator = Gtk.SeparatorToolItem()
        #self.toolbar_box.toolbar.insert(self.seperator, 6)
	
	self.configure_scale_btn = ToggleToolButton()
	self.configure_scale_btn.set_tooltip('Select scale')
	self.configure_scale_btn.props.icon_name = 'toolbox_scale'
	self.configure_scale_btn.connect('toggled', self.choose_scale)
	#self.toolbar_box.toolbar.insert(self.configure_scale_btn, 7)
		
	separator = Gtk.SeparatorToolItem()
	separator.props.draw = False
	separator.set_expand(True)
	self.toolbar_box.toolbar.insert(separator, -1)
	
	stop_button = StopButton(self)
	stop_button.props.accelerator = '<Ctrl><Shift>Q'
	self.toolbar_box.toolbar.insert(stop_button, -1)
	stop_button.show()	
	
	self.set_toolbar_box(self.toolbar_box)
	self.toolbar_box.show_all()

        #self.set_toolbox(toolbox)
        
        #activity_toolbar = toolbox.get_activity_toolbar()
        #activity_toolbar.remove(activity_toolbar.share)
        #activity_toolbar.share = None
        #activity_toolbar.keep.connect('clicked', self._keep_cb)
        #activity_toolbar.stop.can_focus = True
        #activity_toolbar.keep.can_focus = True

        #toolbox.show()
        #activity_toolbar.keep.grab_focus()
        
        self.gamename = 'Musicpainter'
        self.set_title("Music Painter")
        
        ## connect to the in/out events 
        #self.connect('notify::active', self.onActive)
        #self.connect('focus_in_event', self._focus_in)
        #self.connect('focus_out_event', self._focus_out)

	self.musicpainter = Musicpainter.Musicpainter()
        presenceService = presenceservice.get_instance()
        xoOwner = presenceService.get_owner() # get my name
        self.musicpainter.initSugar(self, xoOwner.props.nick)
	if not (self.to_read == '' or self.uid == ''):
	    #try:
	    print "Read journal uid: (" + self.uid + "), filename: " + self.to_read
	    self.musicpainter.score.read_journal(self.to_read, self.uid)
	    #except:
		#print "Exception caught when reading journal."
	    #try:
	    print "Init view: " + self.metadata['view']
	    self.musicpainter.init_view(self.metadata['view'])		
	    self.init_view_sugar(self.metadata['view'])		
	    #except:
		#print "No initial view."		
	else:		
	    self.musicpainter.score.new_score()  	# init a canvas	
	    #self.musicpainter.init_view('canvas')		
	    #self.init_view_sugar('canvas') 
	    
	    self.musicpainter.init_view('home')
	    self.init_view_sugar('home')
	    
	#self.create_journal()	    
	
	#bus = dbus.SessionBus()
	#remote_object = bus.get_object(DS_DBUS_SERVICE, DS_DBUS_PATH)
	#_datastore = dbus.Interface(remote_object, DS_DBUS_INTERFACE)
	#_datastore.connect_to_signal('Created', self.datastore_created_cb)
	#_datastore.connect_to_signal('Updated', self.datastore_updated_cb)
	#_datastore.connect_to_signal('Deleted', self.datastore_deleted_cb)	
	
    def new_file(self, widget):
	self.musicpainter.score.new_score()
	self.to_canvas_mode(widget)
	self.activity_btn.set_expanded(False)
	self.toolbar_changed(widget)
        
    def msg_box_callback(self):
	self.to_canvas_mode(self.w)
	#self.activity_btn.set_expanded(False)
	#self.toolbar_changed(self.w)	
	
    def upload_callback(self):
	self.musicpainter.detail_view.show_message_box("Upload successful! ")
	        
    def save_file(self, widget):
	if self.musicpainter.current_view != 'detail':	    
	    self.to_detail_mode(widget)
	    self.musicpainter.detail_view.set_toolbar_expanded(self.musicpainter.toolbar_expanded)
	if self.musicpainter.score.save_score():
	    self.w = widget
	    self.musicpainter.detail_view.show_message_box("Save successful!")

    def save_file_as(self, widget):
	if self.musicpainter.current_view != 'detail':
	    self.to_detail_mode(widget)
	    self.musicpainter.detail_view.set_toolbar_expanded(self.musicpainter.toolbar_expanded)
	if self.musicpainter.score.save_score_as():
	    self.w = widget
	    self.musicpainter.detail_view.show_message_box("Save successful!")
	
    def share_file(self, widget):	
	if self.musicpainter.current_view != 'detail':
	    self.to_detail_mode(widget)
	    self.musicpainter.detail_view.set_toolbar_expanded(self.musicpainter.toolbar_expanded)
	if not self.musicpainter.score.upload_eligible():
	    self.w = widget
	    self.musicpainter.detail_view.show_message_box("Please make changes before upload. ")
	else:
	    self.w = widget
	    self.musicpainter.score.save_score()
	    self.musicpainter.network.upload_music(self.musicpainter.score.uid + ".png")
	
    def toolbar_changed(self, widget):
	#print "activity.toolbar_changed()"
	self.musicpainter.toolbar_switch()
    
    def go_home(self, widget):
	self.musicpainter.go_home()	
	self.hide_scale_btn()

	if self.musicpainter.toolbar_expanded:
	    self.activity_btn.set_expanded(False)
	    self.toolbar_changed(widget)	
	    
    def to_detail_mode(self, widget):
	if self.musicpainter.to_detail_mode_from_sugar():
	    self.show_scale_btn()
	else:
	    self.hide_scale_btn()
	
    def to_canvas_mode(self, widget):
	self.musicpainter.to_canvas_view()
	self.show_scale_btn()
	    
	if self.musicpainter.toolbar_expanded:
	    self.activity_btn.set_expanded(False)
	    self.toolbar_changed(widget)

    def to_keyboard_mode(self, widget):
	self.musicpainter.to_keyboard_mode()
	self.show_scale_btn()

	if self.musicpainter.toolbar_expanded:
	    self.activity_btn.set_expanded(False)
	    self.toolbar_changed(widget)
	
    def configure_ins(self, widget):
	self.musicpainter.to_instrument_view()
	self.hide_scale_btn()

	if self.musicpainter.toolbar_expanded:
	    self.activity_btn.set_expanded(False)
	    self.toolbar_changed(widget)
	    
    def choose_scale(self, widget):
	self.musicpainter.choose_scale()
	
    def hide_scale_btn(self):
	if self.btn_added:
	    self.seperator.set_visible(False)
	    self.configure_scale_btn.set_visible(False)
	
    def show_scale_btn(self):
	if not self.btn_added:
	    self.toolbar_box.toolbar.insert(self.seperator, 6)
	    self.toolbar_box.toolbar.insert(self.configure_scale_btn, 7)
	    self.toolbar_box.show_all()
	    self.btn_added = True
	else:
	    self.seperator.set_visible(True)
	    self.configure_scale_btn.set_visible(True)

    def set_active_btn(self, mode):
	if mode == 'canvas':
	    self.canvas_mode_btn.set_active(True)
	elif mode == 'keyboard':
	    self.keyboard_mode_btn.set_active(True)
	elif mode == 'instruments':
	    self.configure_ins_btn.set_active(True)
	    
    def set_scale(self, flag):
	self.configure_scale_btn.set_active(flag)
	    
    def hide_scale_btn(self):
	self.seperator.set_visible(False)
	self.configure_scale_btn.set_visible(False)	
	
    def _keep_cb(self, data=None):
        #print "to keep()"
        #self.musicpainter.canvas.save_file()
        return

    def _cleanup_cb(self, data=None):
        return

    def _focus_in(self, event, data=None):
        return

    def _focus_out(self, event, data=None):
        return

    def onActive(self, widget = None, event = None):
        #if widget.props.active == False:
        #    print "MusicpainterActivity.onActive: to disconnect"
        #    self.musicpainter.deactivate()
        ##else:
        #    #print "MusicpainterActivity.onActive: to re-connect"
        #    #self.musicpainter.reactivate()
	return

    def read_file(self, file_path):
        #'''Read file from Sugar Journal.'''
        #print "read file: " + file_path + " pending" 
        self.to_read = file_path
	self.uid = self.metadata['uid']	
	#print self.metadata.keys()
	return
    
    #def create_journal(self):
	#file_path = 'temp.mpn'
	#journal_entry = datastore.create()
	#try:
	    #print "new entry uid after create: " + str(journal_entry.metadata['uid'])
	#except:
	    #print "no uid"
	#journal_entry.metadata['title'] = 'create journal test'
	#journal_entry.file_path = file_path
	#self.musicpainter.score.write_journal(file_path)
	#datastore.write(journal_entry)
	#os.remove(file_path)
	#print "journal created"
	#try:
	    #print "new entry uid: " + str(journal_entry.metadata['uid'])
	#except:
	    #print "no uid"
	    
    #def create_journal(self):
	#print 'create_journal()'
	#journal_entry = datastore.create()
	#journal_entry.metadata['activity'] = self.get_bundle_id()
	#journal_entry.metadata['mime_type'] = 'application/x-musicpainter'	
	#datastore.write(journal_entry)
	    
    def update_uid(self, uid): # actually, this is meant to screw up the original id
	#self.metadata['uid'] = uid
	self._jobject.object_id = uid
	
    def update_title(self, title):
	self.metadata['title'] = title
	self.title_box.entry.set_text(title)
	
    def get_description(self):
	try:
	    return self.metadata['description']
        except:
	    return

    def write_file(self, file_path):
        #'''Save file on Sugar Journal. '''
        print "write journal: " + file_path
	#print "uid = " + self.metadata['uid']
	#if self._jobject.object_id == None or self.metadata['uid'] == None:
	    #print 'no uid yet'
	uid = self.musicpainter.score.uid
            #uid = self.metadata['uid']
        #else:
            
	    #print "wait for uid"
	    #return
	self.musicpainter.score.title = self.metadata['title']
	try:
	    self.musicpainter.score.description = self.metadata['description']
	except:
	    print "no description"
        self.musicpainter.score.write_journal(file_path, uid)  
	#self.musicpainter.score.write_journal(file_path, self._jobject.object_id)  
        self.metadata['activity'] = self.get_bundle_id()
        self.metadata['mime_type'] = 'activity-musicpainter'
	self.metadata['view'] = self.musicpainter.get_current_view()
	    
    def init_view_sugar(self, view):
	if view == 'canvas':
	    self.toolbar_box.toolbar.insert(self.seperator, 6)
	    self.toolbar_box.toolbar.insert(self.configure_scale_btn, 7)
	    self.toolbar_box.show_all()
	    self.btn_added = True
	elif view == 'keyboard':
	    self.toolbar_box.toolbar.insert(self.seperator, 6)
	    self.toolbar_box.toolbar.insert(self.configure_scale_btn, 7)
	    self.toolbar_box.show_all()
	    self.btn_added = True
	self.set_active_btn(view)
	    	
    #def datastore_created_cb(self, uid):
	#print "datastore_created_cb, uid = " + uid

    
