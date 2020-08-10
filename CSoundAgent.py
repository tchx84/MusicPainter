_showDebugMsg = False

#import gobject
import Global
from gi.repository import GObject

#hasCSound = False
hasCSound = True
if hasCSound:
    from common import Config
    from common.Util.CSoundNote import CSoundNote
    from common.Util.NoteDB import Note
    from common.Util import NoteDB                
    import common.Util.InstrumentDB as InstrumentDB
    
class CSoundAgent():
    def __init__(self, main, csound, gwid, ghei):
        self.main = main
        self.csound = csound
	self.last_note = -1
	self.lid = -1
	self.slid = -1
	self.gwid = gwid
	self.ghei = ghei
	self.play_src = 'canvas'
	self.play_state = 'stop'
	self.scale_play_state = 'stop'
	
	self.keyon = [0 for i in range(ghei)]
	
	self.available_track = [1, 2, 3, 4, 5, 6, 7, 8] # I don't know why, but only the first 9 tracks work normally
	self.track_map = {}
	
	if hasCSound:
	    self.db = self.main.instrumentDB
	
	self.global_vol = 0.5
	self.tempo = 120
	self.grid_tdiv = 6     # one grid = half beat = 6 ticks
	
	self.nid = 4000
	
	self.init_ins_pitch_shift()	
        
# ##############################     csound     ##############################	
	
    def time2tick(self, time):
	if not hasCSound:
	    return 0
	
	tick_duration = 60.0/self.tempo/Config.TICKS_PER_BEAT
	return time/tick_duration
    
    def tick2time(self, tick):
	if not hasCSound:
	    return 0
	
	tick_duration = 60.0/self.tempo/Config.TICKS_PER_BEAT
	return tick_duration*tick

    def send_loop_note(self, inst, pitch, time, duration, vol, lid):
	if not hasCSound:
	    return		
	
	#generate a CSoundNote: (onset_time (ticks), pitch (MIDI #), vol, pan, duration (ticks), track_id, inst_id)
	pitch = self.shift_pitch(inst, pitch)
	csnote = CSoundNote(time, pitch, vol * self.global_vol, 0.5, duration, 0, inst)
	if inst < 5: # sustain piano sound for 0.15 sec
	    csnote.duration = duration + self.time2tick(0.36)
	#elif inst == 141:
	#    csnote.duration = -1
	csnote.decay = self.time2tick(0.75) # apply a decay for all instruments
	
	#wrap it in a Note before adding to the loop Note(page_id, track_id, note_id, csnote)	
	n = Note(0, csnote.trackId, self.get_nid(), csnote)
	self.csound.loopPlay(n, 1, loopId = lid)

    def send_note(self, inst, pitch, duration, vol, gy = -1):
	if not hasCSound:
	    return
	
	if gy == -1:
	    tid = 0
	else:
	    tid = self.get_available_track()
	    self.track_map[gy] = tid
	pitch = self.shift_pitch(inst, pitch)
	csnote = CSoundNote(0, pitch, vol * self.global_vol, 0.5, duration, tid, inst)
	csnote.decay = 0.5
	self.csound.play(csnote, 1) # sec per tick = 1, so the unit for duration/decay becomes sec
	
    def send_note_off(self, inst, gy):
	tid = self.query_pitch_and_recycle_tid(gy)

    def send_tied_note_on(self, inst, pitch, vol):  # tied note generates a pair of note_on/off event, in note_on, duration = -1 (open note)
	if not hasCSound:
	    return
		
	tid = self.get_available_track()
	self.track_map[pitch] = tid
	#print "pitch(" + str(pitch) + ") on track " + str(tid)
	pitch = self.shift_pitch(inst, pitch)
	
	csnote = CSoundNote(0, pitch, vol * self.global_vol, 0.5, -1, tid, inst)
	csnote.tied = True
	csnote.mode = "mini"
	
	self.csound.play(csnote, 1)

    def send_tied_note_off(self, inst, pitch, duration, decay, vol):
	if not hasCSound:
	    return
	
	tid = self.query_pitch_and_recycle_tid(pitch)
	if tid == -1:
	    return
	#print "pitch(" + str(pitch) + ") removed from track " + str(tid)
	pitch = self.shift_pitch(inst, pitch)
	
	csnote = CSoundNote(0, pitch, vol * self.global_vol, 0.5, duration, tid, inst)
	csnote.decay = decay
	csnote.tied = False
	csnote.mode = "mini"
	
	self.csound.play(csnote, 1)
	
    def query_pitch_and_recycle_tid(self, p):
	try:
	    tid = self.track_map[p]
	    self.track_map.pop(p, None)
	    self.available_track.insert(0, tid)	
	except:
	    #print 'tid has been recycled earlier.'
	    return -1
	return tid
    
    def get_available_track(self):
	return self.available_track.pop()
    
    def turnoff_existing_keys(self):	
	if not hasCSound:
	    return
	
	inst = self.main.canvas_view.bottom_bar.active_instrument
	if not self.isPercussion_color(inst):
	    for pitch in self.track_map.keys():
		if self.isKeyboard_color(inst):
		    self.send_tied_note_off(self.getInstrumentId_color(inst), pitch, 0.36, 0.5, 0.5)
		else:
		    self.send_tied_note_off(self.getInstrumentId_color(inst), pitch, 0.12, 0.5, 0.5)		
		    
	for i in range(self.ghei):
	    self.keyon[i] = 0
	
    def init_ins_pitch_shift(self):
	if not hasCSound:
	    return 0	
	self.shift_map = []
	iid = self.getInstrumentId_name('guit2')
	self.shift_map.append([iid, -4])
	iid = self.getInstrumentId_name('guitmute')
	self.shift_map.append([iid, 8])
	iid = self.getInstrumentId_name('guitshort')
	self.shift_map.append([iid, -4])
	iid = self.getInstrumentId_name('au_pipes')
	self.shift_map.append([iid, -2])
	iid = self.getInstrumentId_name('sarangi')
	self.shift_map.append([iid, 4])
	iid = self.getInstrumentId_name('basse')
        self.shift_map.append([iid, -12])	
	iid = self.getInstrumentId_name('fingercymbals')
        self.shift_map.append([iid, -19])	
	iid = self.getInstrumentId_name('triangle')
        self.shift_map.append([iid, -24])	
	iid = self.getInstrumentId_name('chimes')
        self.shift_map.append([iid, -24])	
	
    def shift_pitch(self, ins, pitch):
	for i in range(len(self.shift_map)):
	    if self.shift_map[i][0] == ins:
		return pitch + self.shift_map[i][1]
	return pitch
	    
    def getInstrumentId_name(self, name):
	if not hasCSound:
            return 0
	name = Global.get_name_from_label(name)
	return self.db.getInstrumentByName(name).instrumentId
	
    def getInstrumentId_color(self, id):
	if not hasCSound:
            return 0
	if self.play_src == 'canvas':
	    name = self.main.canvas_view.bottom_bar.instruments[id]
	else:
	    name = self.main.detail_view.score.instruments[id]
	return self.getInstrumentId_name(name)
    
    def isPercussion_color(self, id):
	if self.play_src == 'canvas':
	    name = self.main.canvas_view.bottom_bar.instruments[id]
	else:
	    name = self.main.detail_view.score.instruments[id]
	return self.isPercussion_name(name)
    
    def isPercussion_name(self, name):
	for ins in Global.drum_kit:
	    name = Global.get_name_from_label(name)
	    ins_name = Global.get_name_from_label(ins)
	    if ins_name == name:
		return True
	return False	
    
    def is_non_hangable_color(self, id):
	name = self.main.canvas_view.bottom_bar.instruments[id]
	for ins in Global.nonhangable_list:
	    ins_name = Global.get_name_from_label(ins)
	    if ins_name == name:
		return True
	return False	
    
    def isKeyboard_color(self, id):
	if not hasCSound:
            return False
	name = self.main.canvas_view.bottom_bar.instruments[id]
	for ins in Global.instrument_list['Keyboard']:
	    ins_name = Global.get_name_from_label(ins)
	    if ins_name == name:
		return True
	return False		

# ##############################     sound-making function     ##############################

    def knote_on(self, inst, note):  # keyboard note on	
	if self.isPercussion_color(inst-1):
	    self.send_note(self.getInstrumentId_color(inst-1), self.main.score.drum_map(note), -1, 0.5, note)
	else:
	    self.send_tied_note_on(self.getInstrumentId_color(inst-1), note, 0.5)

    def knote_off(self, inst, note):  # keyboard note on
	if self.isPercussion_color(inst-1):
	    self.send_note_off(inst-1, note)
	elif self.isKeyboard_color(inst-1):
	    self.send_tied_note_off(self.getInstrumentId_color(inst-1), note, 0.36, 0.5, 0.5)
	else:
	    self.send_tied_note_off(self.getInstrumentId_color(inst-1), note, 0.12, 0.5, 0.5)

    def note_sample(self, inst_name):
	if inst_name == '':
	    return
	iid = self.getInstrumentId_name(inst_name)
	if self.isPercussion_name(inst_name):
	    self.send_note(iid, self.main.score.drum_random(), -1, 1)
	else:
	    self.send_note(iid, 60+self.main.score.score_shift, 0.8, 0.5)

    def note_on(self, inst, note, toolbar_sound = 0, v = 0.5):  # mouse note on
	if toolbar_sound == 0:  # NOT toolbar sound
	    if self.isPercussion_color(inst-1):
		self.send_note(self.getInstrumentId_color(inst-1), self.main.score.drum_map(note), -1, v)
	    else:
		self.last_tied_note_vol = v
		self.send_tied_note_on(self.getInstrumentId_color(inst-1), note, v)	    
	else:
	    if self.isPercussion_color(inst-1):
		self.send_note(self.getInstrumentId_color(inst-1), self.main.score.drum_random(), -1, v)
	    else:
		self.send_note(self.getInstrumentId_color(inst-1), note, 0.8, v)

    def note_off(self, inst, note):   # mouse note off
	if self.isPercussion_color(inst-1):
	    return
	elif self.isKeyboard_color(inst-1):
	    self.send_tied_note_off(self.getInstrumentId_color(inst-1), note, 0.36, 0.5, self.last_tied_note_vol)
	else:
	    self.send_tied_note_off(self.getInstrumentId_color(inst-1), note, 0.12, 0.5, self.last_tied_note_vol)

    def drag_on_vol(self, colorsel, gy, v):
	if self.isPercussion_color(colorsel):
	    note = gy
	else:
	    note = self.main.score.get_map_pitch(gy)
	if self.last_note != -1:
	    self.note_off(colorsel+1, self.last_note)
	self.last_note = note
	self.note_on(colorsel+1, note, 0, self.floor3(v))

    def keyboard_change_instrument(self, prev_color):
	for i in range(self.ngrid_v):
	    if self.isPercussion_color(prev_color):
		note = i
	    else:
		note = self.main.score.get_map_pitch(i)
	    if self.keyon[i] == 1:
		self.knote_off(colorsel+1, note, i)
		self.keyon[i] = 0    
        
    def keyboard_press(self, colorsel, gy):
#        print "note on: " + str(colorsel+1) + "," + str(gy)
        if self.keyon[gy] == 1:
            return
        if self.isPercussion_color(colorsel):
            note = gy
        else:
            note = self.main.score.get_map_pitch(gy)
        self.knote_on(colorsel+1, note)
	if self.play_state == 'play':
	    self.main.canvas_view.record_keyboard_press(gy)
        self.keyon[gy] = 1
	self.main.canvas_view.update_key_presses()
        
    def keyboard_release(self, colorsel, gy):
#        print "note off: " + str(colorsel+1) + "," + str(gy)
        if self.isPercussion_color(colorsel):
            note = gy
        else:
            note = self.main.score.get_map_pitch(gy)
        self.knote_off(colorsel+1, note)
	if self.play_state == 'play':
	    self.main.canvas_view.record_keyboard_release(gy)
        self.keyon[gy] = 0
	self.main.canvas_view.update_key_presses()

    def drag_on(self, toolsel, colorsel, gy):
        if toolsel != 0:
            return
        if self.isPercussion_color(colorsel):
            note = gy
        else:
            note = self.main.score.get_map_pitch(gy)
        if note != self.last_note:  # to be fix, note != 0
            if self.last_note !=-1 :
                self.note_off(colorsel+1, self.last_note)
            self.last_note = note
            self.note_on(colorsel+1, note)

    def drag_off(self, toolsel, colorsel):
        if not (toolsel == 0 or toolsel == 2 or toolsel == 3):
            return
        if self.last_note !=-1 :
            self.note_off(colorsel+1, self.last_note)
            self.last_note = -1
	    
    def make_shift_pitch_sound(self):
	if not hasCSound:
	    return
	
	if self.play_state == 'stop':
	    self.note_sample('piano')
	elif self.play_state == 'play':
	    tick = self.csound.loopGetTick(self.lid)
	    self.play_music(tick)	    
	    
    def play_scale(self, mode):
	if not hasCSound:
	    return
	if self.play_state == "play":
	    tick = self.csound.loopGetTick(self.lid)
	    self.play_music(tick)
	    return
	csound = self.csound
	if self.slid != -1:
	    csound.loopDestroy(self.slid)
	self.slid = csound.loopCreate()
	seq = self.main.score.get_scale_pitches(mode)
	
	#self.grid_tdiv = 6     # one grid = half beat = 6 ticks
	bpm = self.getTempo()
	#60.0 / bpm               # beat period in sec
		
	unit = int(3*bpm/60)
	for i in range(len(seq)):	    
	    self.send_loop_note(self.getInstrumentId_name('clarinette'), seq[i], 1.0*i*unit, 1.0*unit+3, 0.84, self.slid)
	self.scale_loop_duration = 1.0*(i+1)*unit
	self.send_loop_note(self.getInstrumentId_name('clarinette'), 60, 1.0*(i+1)*unit, 1.0*unit, 0, self.slid)
	csound.loopSetNumTicks(int((i+2)*unit), self.slid)
	
	csound.loopSetTick(0, self.slid)
        csound.loopStart(self.slid)	
	
        self.scalePlaybackTimer = GObject.timeout_add(int(1000*self.tick2time(unit/4)), self.scaleTimeUpdate)
	self.scale_play_state = 'play'
	
    def stop_scale(self):
	if not hasCSound:
	    return
		
	if self.slid != -1:
	    self.csound.loopDestroy(self.slid)
	    self.slid = -1
	    GObject.source_remove(self.scalePlaybackTimer)
	self.scale_play_state = 'stop'
	    
    def scaleTimeUpdate(self):
	if self.csound.loopGetTick(self.slid) >= self.scale_loop_duration:
	    self.stop_scale()
	return True
	    
    def play_music(self, start_tick = 0, src = 'canvas'):
	if not hasCSound:
	    return False
	
	self.play_src = src
	if self.scale_play_state == 'play':
	    self.stop_scale()
	    
	csound = self.csound
	if src == 'canvas':
	    score = self.main.score
	elif src == 'detail':
	    score = self.main.detail_view.score
	
	if self.lid != -1:
	    csound.loopDestroy(self.lid)
	self.lid = csound.loopCreate()

        (events, st, et) = self.score2events(score.note_map, score.cut, 0, src)
	#(events, st, et) = self.score2events(self.sel, self.scut)
	
	end_tick = 0
	if st != -1:            
	    for i in range(len(events)):
		if events[i][0] == 'african':
		    self.send_loop_note(self.getInstrumentId_name(events[i][0]), score.drum_map(events[i][4]), events[i][1], -1, events[i][3], self.lid)
		elif self.isPercussion_color(events[i][0]-1):
		    self.send_loop_note(self.getInstrumentId_color(events[i][0]-1), score.drum_map(events[i][4]), events[i][1], -1, events[i][3], self.lid)
		else:                        
		    self.send_loop_note(self.getInstrumentId_color(events[i][0]-1), score.get_map_pitch(events[i][4]), events[i][1], events[i][2], events[i][3], self.lid)
	    self.play_state = "play"
	    self.score_start_tick = st
	    self.loop_duration = et
	else:
	    self.play_state = "stop"
	    return False
	
	if src == 'canvas' and self.main.canvas_view.bottom_bar.play_all:
	    self.loop_duration = int(self.gwid * self.grid_tdiv)
		
	if src == 'canvas':
	    self.setTempo()
	elif src == 'detail':
	    self.setTempo(score.tempo_r)
	
	if src == 'canvas' and self.main.canvas_view.bottom_bar.is_looping:	    
	    csound.loopSetNumTicks(int(self.loop_duration), self.lid)
	else:                                                                                                   
	    self.send_loop_note(3, 60, self.loop_duration + 2 * self.grid_tdiv, 2 * self.grid_tdiv, 0, self.lid)  # add a dummy note, so we have time to stop the loop
	    csound.loopSetNumTicks(int(self.loop_duration + 4 * self.grid_tdiv), self.lid)
	    
	csound.loopSetTick(start_tick, self.lid)
	csound.loopStart(self.lid)
	
	# self.self.grid_tdiv 
	self.interval = int(1000*self.tick2time(self.grid_tdiv/4))
	self.playbackTimer = GObject.timeout_add(self.interval, self.timeUpdate)
	
	return True

    def stop_music(self):
	if not hasCSound:
	    return	
	
	if self.play_state == "play":
	    if self.play_src == 'canvas':
		self.main.canvas_view.draw_highlight(-1)
	    elif self.play_src == 'detail':
		self.main.detail_view.draw_highlight(-1)
        self.play_state = "stop"
	#self.main.toolbar.update()
	
	if self.lid != -1:
	    self.csound.loopDestroy(self.lid)
	    self.lid = -1
	    GObject.source_remove(self.playbackTimer)
	self.interval = -1
	
    def setTempo(self, sval = -1):
	if not hasCSound:
	    return	
		
	self.tempo = self.getTempo(sval)
	self.csound.setTempo(self.tempo)
	    	
    def getTempo(self, sval = -1):
	if sval == -1:
	    sval = self.main.canvas_view.bottom_bar.tempo_r
	if sval <= 0.5:
	    return 30 + sval * 180
	else:
	    return 120 + (sval - 0.5) * 360	
	
    def timeUpdate(self):
	if self.csound.loopGetTick(self.lid) >= self.loop_duration:
	   #print "timeUpdate, to restart loop"
	    if self.play_src == 'canvas':
		if not self.main.canvas_view.bottom_bar.is_looping:
		    self.stop_music()
		    self.main.canvas_view.stop_playing()
		elif self.main.score.is_edited_during_loop == 'ready':
		    #print "is edited, to re-play"
		    self.stop_music()
		    self.play_music()
		    self.main.score.is_edited_during_loop = 'off'
	    elif self.play_src == 'detail':
		self.stop_music()
	elif self.play_state == "play":
	    gx = int(1.0 * (self.csound.loopGetTick(self.lid)+self.score_start_tick)/self.grid_tdiv)	
	    if self.play_src == 'canvas':
		self.main.canvas_view.draw_highlight(gx)
		if self.main.score.is_edited_during_loop == 'on':
		    self.send_loop_note(3, 60, self.loop_duration + 2 * self.grid_tdiv, 2 * self.grid_tdiv, 0, self.lid)  # add a dummy note, so we have time to stop the loop
		    self.csound.loopSetNumTicks(int(self.loop_duration + 4 * self.grid_tdiv), self.lid)
		    self.main.score.is_edited_during_loop = 'ready'
	    elif self.play_src == 'detail':
		self.main.detail_view.draw_highlight(gx)
	return True
	
    def score2events(self, score, cut, div = 0, src = 'canvas'):
        if div == 0:
            div = self.grid_tdiv
        events = list()

        if src == 'canvas' and self.main.canvas_view.bottom_bar.play_all:
            first_note_time = 0
        else:
            first_note_time = -1
        end_note_time = -1

        for i in range(self.gwid):
            for j in range(self.ghei):
                for k in range(8):
                    if score[k][i][j] != 0 and (i == 0 or score[k][i-1][j] == 0 or cut[k][i-1][j] == 1):
                        if first_note_time == -1:
                            first_note_time = div*i
                        len = 1
                        while i+len < self.gwid and score[k][i+len][j] != 0 and cut[k][i+len-1][j] == 0:
                            len = len + 1
                        st = div*i - first_note_time
                        du = div*len
                        if end_note_time == -1 or end_note_time < st+du:
                            end_note_time = st+du			
                        event = [k+1, self.floor3(st), self.floor3(du), self.floor3(1.0*score[k][i][j]/256), j]
                        events.append(event)		
            if src == 'canvas' and self.main.canvas_view.bottom_bar.is_recording:
                if self.main.canvas_view.bottom_bar.tempo_r >= 0.75:
                    p = 8
		elif self.main.canvas_view.bottom_bar.tempo_r >= 0.25:
		    p = 4
                else: #if self.main.canvas_view.bottom_bar.tempo_r >= 0.1:
                    p = 2
                if i % p != 0:
                    continue
                st = div*i - first_note_time
                du = -1
                if end_note_time == -1 or end_note_time < st+du:
                    end_note_time = st+du
                event = ['african', self.floor3(st), self.floor3(du), 0.5, 6]
                events.append(event)

        return (events, first_note_time, end_note_time)		
	
    def floor3(self, v):
        return 1.0 * (int) ((v + 0.0005) * 1000) / 1000

    def get_nid(self):  # return nid while implementing the id
	self.nid = self.nid + 1
	return self.nid - 1
    