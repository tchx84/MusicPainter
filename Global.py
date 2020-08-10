import ctypes
import cairo
from gi.repository import Gdk

red = Gdk.Color(255*255, 106*255, 107*255)  # FF6A6B
orange = Gdk.Color(248*255, 172*255, 76*255)  # F8AC4C
yellow = Gdk.Color(255*255, 255*255, 65*255)  # FFFF41
grass = Gdk.Color(186*255, 251*255, 63*255)  # BAFB3F
green = Gdk.Color(108*255, 214*255, 109*255)  # 6CD66D
teal = Gdk.Color(64*255, 255*255, 255*255)  # 40FFFF
blue = Gdk.Color(42*255, 110*255, 167*255)  # 2A6EA7
purple = Gdk.Color(181*255, 90*255, 255*255)  # B55AFF 

server_ip = 'http://musicpainter-olpc.appspot.com' 
#server_ip = 'http://localhost:8080' 

#score_folder = 'music/'
score_folder_local = 'music/'
score_folder_download = 'download/'
cache_folder = 'cache/'

colors = [red, orange, yellow, grass, green, teal, blue, purple]

home_tag_offset_y = {'Popular': 2, 'New': -4, 'Mine': -4}
home_img_offset_y = {'Popular': 0, 'New': 0, 'Mine': -4}

file_img = {'save': 'icons/file_save.png', 'saveas': 'icons/file_save_as.png', 'upload': 'icons/file_upload.png', 'new': 'icons/file_new.png', 'delete': 'icons/file_delete.png'}

home_img = {'Popular': 'icons/home_favorite_46.png', 'New': 'icons/home_new_54.png', 'Mine': 'icons/home_mine_40x50.png', 'favorite': 'icons/heart_28x24.png', 'play': 'icons/play_24.png'}
home_img_size = {'Popular': [46, 46], 'New': [54, 54], 'Mine': [40, 50]}

detail_img = {'edit': 'icons/pen.png', 'favorite': 'icons/heart_38x34.png', 'play': 'icons/play_38x34.png', 'rewind': 'icons/rewind.png', 'forward': 'icons/forward.png', 'favorited': 'icons/heart_38x34r.png', 'avatar': 'icons/avatar.png', 'delete': 'icons/trash.png', 'upload': 'icons/file_upload.png'}
detail_icons = {'edit', 'delete', 'favorite', 'play', 'rewind', 'forward'}
#detail_icons = {'edit', 'delete', 'upload', 'favorite', 'play', 'rewind', 'forward'}
#detail_icons = {'edit', 'delete', 'upload', 'rewind', 'forward'}


instrument_imgs_sm = {'piano': 'images/44/piano44.png', 'banjo': 'images/44/banjo44.png', 'flute': 'images/44/flute44.png', 'clarinette': 'images/44/clarinet44.png', 
                      'flugel': 'images/44/flugel44.png', 'trumpet' :'images/44/trumpet44.png', 'tuba' :'images/44/tuba44.png', 'jazzrock' :'images/44/jazzrock44.png', 
                      'african': 'images/44/african44.png', 'arabic': 'images/44/arabic44.png', 'electronic': 'images/44/electronic44.png', 
                      'southamerican': 'images/44/southamerican44.png', 'nepali': 'images/44/nepail44.png', 'clavinet': 'images/44/clavinet44.png', 
                      'harmonium': 'images/44/harmonium44.png', 'rhodes': 'images/44/rhodes44.png', 'harpsichord': 'images/44/harpsichord44.png', 
                      'au_pipes': 'images/44/aupipes44.png', 'didjeridu': 'images/44/didgeridoo44.png', 'foghorn': 'images/44/foghorn44.png', 
                      'harmonica': 'images/44/harmonica44.png', 'ocarina': 'images/44/ocarina44.png', 'saxo': 'images/44/saxophone44.png', 
                      'saxsoprano': 'images/44/saxsoprano44.png', 'shenai': 'images/44/shenai44.png', 'ukulele': 'images/44/ukelele44.png', 'guit': 'images/44/guit44.png', 
                      'guit2': 'images/44/guit2_44.png', 'guitmute': 'images/44/guitmute44.png', 'guitshort': 'images/44/guitshort44.png', 'koto': 'images/44/koto44.png', 
                      'basse': 'images/44/basse44.png', 'acguit': 'images/44/acguit44.png', 'mando': 'images/44/mandolin44.png',  'sitar': 'images/44/sitar44.png', 
                      'violin': 'images/44/violin44.png', 'cello': 'images/44/cello44.png', 'sarangi': 'images/44/sarangi44.png', 'chimes': 'images/44/chimes44.png', 
                      'fingercymbals': 'images/44/fingercymbals44.png', 'kalimba': 'images/44/kalimba44.png', 'marimba': 'images/44/marimba44.png', 'triangle': 'images/44/triangle44.png'}

instrument_imgs_med = {'piano': 'images/75/piano75.png', 'banjo': 'images/75/banjo75.png', 'flute': 'images/75/flute75.png', 'clarinette': 'images/75/clarinet75.png', 
                      'flugel': 'images/75/flugel75.png', 'trumpet' :'images/75/trumpet75.png', 'tuba' :'images/75/tuba75.png', 'jazzrock' :'images/75/jazzrock75.png', 
                      'african': 'images/75/african75.png', 'arabic': 'images/75/arabic75.png', 'electronic': 'images/75/electronic75.png', 
                      'southamerican': 'images/75/southamerican75.png', 'nepali': 'images/75/nepail75.png', 'clavinet': 'images/75/clavinet75.png', 
                      'harmonium': 'images/75/harmonium75.png', 'rhodes': 'images/75/rhodes75.png', 'harpsichord': 'images/75/harpsichord75.png', 
                      'au_pipes': 'images/75/aupipes75.png', 'didjeridu': 'images/75/didgeridoo75.png', 'foghorn': 'images/75/foghorn75.png', 
                      'harmonica': 'images/75/harmonica75.png', 'ocarina': 'images/75/ocarina75.png', 'saxo': 'images/75/saxophone75.png', 
                      'saxsoprano': 'images/75/saxsoprano75.png', 'shenai': 'images/75/shenai75.png', 'ukulele': 'images/75/ukelele75.png', 'guit': 'images/75/guit75.png', 
                      'guit2': 'images/75/guit2_75.png', 'guitmute': 'images/75/guitmute75.png', 'guitshort': 'images/75/guitshort75.png', 'koto': 'images/75/koto75.png', 
                      'basse': 'images/75/basse75.png', 'acguit': 'images/75/acguit75.png', 'mando': 'images/75/mandolin75.png',  'sitar': 'images/75/sitar75.png', 
                      'violin': 'images/75/violin75.png', 'cello': 'images/75/cello75.png', 'sarangi': 'images/75/sarangi75.png', 'chimes': 'images/75/chimes75.png', 
                      'fingercymbals': 'images/75/fingercymbals75.png', 'kalimba': 'images/75/kalimba75.png', 'marimba': 'images/75/marimba75.png', 'triangle': 'images/75/triangle75.png'}

instrument_imgs_lg = {'piano': 'images/100/piano100.png', 'banjo': 'images/100/banjo100.png', 'flute': 'images/100/flute100.png', 'clarinette': 'images/100/clarinet100.png', 
                      'flugel': 'images/100/flugel100.png', 'trumpet' :'images/100/trumpet100.png', 'tuba' :'images/100/tuba100.png', 'jazzrock' :'images/100/jazzrock100.png', 
                      'african': 'images/100/african100.png', 'arabic': 'images/100/arabic100.png', 'electronic': 'images/100/electronic100.png', 
                      'southamerican': 'images/100/southamerican100.png', 'nepali': 'images/100/nepail100.png', 'clavinet': 'images/100/clavinet100.png', 
                      'harmonium': 'images/100/harmonium100.png', 'rhodes': 'images/100/rhodes100.png', 'harpsichord': 'images/100/harpsichord100.png', 
                      'au_pipes': 'images/100/aupipes100.png', 'didjeridu': 'images/100/didgeridoo100.png', 'foghorn': 'images/100/foghorn100.png', 
                      'harmonica': 'images/100/harmonica100.png', 'ocarina': 'images/100/ocarina100.png', 'saxo': 'images/100/saxophone100.png', 
                      'saxsoprano': 'images/100/saxsoprano100.png', 'shenai': 'images/100/shenai100.png', 'ukulele': 'images/100/ukelele100.png', 'guit': 'images/100/guit100.png', 
                      'guit2': 'images/100/guit2_100.png', 'guitmute': 'images/100/guitmute100.png', 'guitshort': 'images/100/guitshort100.png', 'koto': 'images/100/koto100.png', 
                      'basse': 'images/100/basse100.png', 'acguit': 'images/100/acguit100.png', 'mando': 'images/100/mandolin100.png',  'sitar': 'images/100/sitar100.png', 
                      'violin': 'images/100/violin100.png', 'cello': 'images/100/cello100.png', 'sarangi': 'images/100/sarangi100.png', 'chimes': 'images/100/chimes100.png', 
                      'fingercymbals': 'images/100/fingercymbals100.png', 'kalimba': 'images/100/kalimba100.png', 'marimba': 'images/100/marimba100.png', 'triangle': 'images/100/triangle100.png'}

toolset_tooltip = ['Pencil', 'Eraser', 'Strengthen note', 'Lighten note', 'Split', 'Loop', 'Play all']

toolset_icons = ['icons/write.png', 'icons/erase.png', 'icons/forte.png', 'icons/piano.png', 'icons/cut.png', 'icons/loop.png', 'icons/section.png']
#toolset_icons = ['icons/write.png', 'icons/erase.png', 'icons/forte.png', 'icons/piano.png', 'icons/select.png', 'icons/cut.png', 'icons/loop.png', 'icons/section.png']

tempo_icons = {'turtle': 'icons/turtle_24x20.png', 'rabbit': 'icons/rabbit_24x20.png'}

array_png = 'icons/arrow.png'

instrument_view_hint_1 = ['Select', 'your instruments', 'by dragging onto', 'the colours below.']
instrument_view_hint_2 = ['Remove', 'your instruments', 'by dragging out of', 'the colours below.']

instrument_category = ['Keyboard', 'Percussion', 'Wind Instruments', 'String Instruments']
#instrument_category_x = [264, 428, 580, 904]
instrument_category_x = [228, 364, 590, 908]

scale_box_x = 325

instrument_all_list = ['piano', 'harpsichord', 'clavinet', 'harmonium', 'rhodes', 
                       'flute', 'clarinette', 'trumpet', 'flugel', 'tuba', 'saxo', 'saxsoprano', 'harmonica', 'au_pipes', 'ocarina', 'didjeridu', 'shenai', 'foghorn', 
                       'koto', 'violin', 'cello', 'sarangi', 'banjo', 'sitar', 'mando', 'ukulele', 'acguit', 'guit', 'guitmute', 'guitshort', 'basse', 'guit2', 
                       'african', 'arabic', 'nepali', 'electronic', 'jazzrock', 'southamerican', 'fingercymbals', 'kalimba', 'marimba']

instrument_list = {'Keyboard': ['piano', 'harpsichord', 'clavinet', 'harmonium', 'rhodes'], 
                   'Percussion': ['african kit', 'arabic kit', 'nepali', 'electronic kit', 'jazz/rock kit', 's american kit', 'fingercymbals', 'kalimba', 'marimba'], 
                   'Wind Instruments': ['flute', 'clarinette', 'trumpet', 'flugel', 'tuba', 'saxophone', 'saxsoprano', 'harmonica', 'au pipes', 'ocarina', 'didjeridu', 'shenai', 'foghorn'], 
                   'String Instruments': ['koto', 'violin', 'cello', 'sarangi', 'banjo', 'sitar', 'mandolin', 'ukulele', 'guitar', 'electric guitar', 'e-guitar mute', 'e-guitar short', 'electric bass', 'rock guitar']}

instrument_label_to_name = {'jazz/rock kit':'jazzrock', 'african kit':'african', 'arabic kit':'arabic', 'electronic kit': 'electronic', 
                            's american kit':'southamerican', 'au pipes': 'au_pipes', 'guitar':'acguit', 'e-guitar mute': 'guitmute', 'e-guitar short': 'guitshort', 
                            'electric guitar':'guit', 'rock guitar':'guit2', 'electric bass': 'basse', 'saxophone': 'saxo', 'mandolin':'mando'}

instrument_name_to_label = {'piano':'Piano', 'harpsichord':'Harpsichord', 'clavinet':'Clavinet', 'harmonium':'Harmonium', 'rhodes':'Rhodes', 
                       'flute':'Flute', 'clarinette':'Clarinette', 'trumpet':'Trumpet', 'flugel':'Flugel', 'tuba':'Tuba', 'saxo':'Saxophone', 'saxsoprano':'Soprano saxophone', 'harmonica':'Harmonica', 'au_pipes':'Au pipes', 'ocarina':'Ocarina', 'didjeridu':'Didjeridu', 'shenai':'Shenai', 'foghorn':'Foghorn', 
                       'koto':'Koto', 'violin':'Violin', 'cello':'Cello', 'sarangi':'Sarangi', 'banjo':'Banjo', 'sitar':'Sitar', 'mando':'Mandolin', 'ukulele':'Ukulele', 'acguit':'Acoustic Guitar', 'guit':'Electric guitar', 'guitmute':'E-guitar mute', 'guitshort':'E-guitar short', 'basse':'Electric bass', 'guit2':'Rock guitar', 
                       'african':'African kit', 'arabic':'Arabic kit', 'nepali':'Nepali kit', 'electronic':'Electronic kit', 'jazzrock':'Jazz/rock kit', 'southamerican':'South-American kit', 'fingercymbals':'Fingercymbals', 'kalimba':'Kalimba', 'marimba':'Marimba'}

nonhangable_list = ['jazzrock', 'african', 'arabic', 'electronic', 'southamerican', 'nepali', 'guitmute', 'guitshort']

drum_kit = ['african kit', 'arabic kit', 's american kit', 'jazz/rock kit', 'electronic kit', 'nepali']

key_map = ['t', 'r', 'e', 'w', 'k', 'j', 'h', 'g', 'f', 'd', 's', 'a', 'm', 'n', 'b', 'v', 'c', 'x', 'z']

map_sharp = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
map_flat = ['C','Db','D','Eb','E','F','Gb','G','Ab','A','Bb','B']

root_map = [map_sharp, map_flat, map_sharp, map_flat, map_sharp, map_flat, map_sharp, map_sharp, map_flat, map_sharp, map_flat, map_sharp]

def get_color_red_float(i):
    return float(1.0*colors[i].red/65535)

def get_color_green_float(i):
    return float(1.0*colors[i].green/65535)

def get_color_blue_float(i):
    return float(1.0*colors[i].blue/65535)

def get_name_from_label(label):
    try:
        return instrument_label_to_name[label]
    except:
        return label
    
def get_label_from_name(name):
    try:
        return instrument_name_to_label[name]
    except:
        return name

def get_img_lg_label(label):
    name = get_name_from_label(label)
    try:
        return instrument_imgs_lg[name]
    except:
        return instrument_imgs_lg['piano']
    
def get_img_sm_label(label):
    name = get_name_from_label(label)
    try:
        return instrument_imgs_sm[name]
    except:
        return instrument_imgs_sm['piano']
    
def get_img_med_label(label):
    name = get_name_from_label(label)
    try:
        return instrument_imgs_med[name]
    except:
        return instrument_imgs_med['piano']
    
def init_font(platform):
    if platform == 'sugar-xo':
        font_face = create_cairo_font_face_for_file ("font/VAG Rounded LT Light.ttf", 0)
    else:
        font_face = 'lucida sans unicode'
        #font_face = 'VAG Rounded Light'
    return font_face
        
_initialized = False
def create_cairo_font_face_for_file (filename, faceindex=0, loadoptions=0):
    global _initialized
    global _freetype_so
    global _cairo_so
    global _ft_lib
    global _surface

    CAIRO_STATUS_SUCCESS = 0
    FT_Err_Ok = 0

    if not _initialized:

        # find shared objects
        _freetype_so = ctypes.CDLL ("libfreetype.so.6")
        _cairo_so = ctypes.CDLL ("libcairo.so.2")

        _cairo_so.cairo_ft_font_face_create_for_ft_face.restype = ctypes.c_void_p
        _cairo_so.cairo_ft_font_face_create_for_ft_face.argtypes = [ ctypes.c_void_p, ctypes.c_int ]
        _cairo_so.cairo_set_font_face.argtypes = [ ctypes.c_void_p, ctypes.c_void_p ]
        _cairo_so.cairo_font_face_status.argtypes = [ ctypes.c_void_p ]
        _cairo_so.cairo_status.argtypes = [ ctypes.c_void_p ]

        # initialize freetype
        _ft_lib = ctypes.c_void_p ()
        if FT_Err_Ok != _freetype_so.FT_Init_FreeType (ctypes.byref (_ft_lib)):
            raise "Error initialising FreeType library."

        class PycairoContext(ctypes.Structure):
            _fields_ = [("PyObject_HEAD", ctypes.c_byte * object.__basicsize__),
                ("ctx", ctypes.c_void_p),
                ("base", ctypes.c_void_p)]

        _surface = cairo.ImageSurface (cairo.FORMAT_A8, 0, 0)

        _initialized = True

    # create freetype face
    ft_face = ctypes.c_void_p()
    cairo_ctx = cairo.Context (_surface)
    cairo_t = PycairoContext.from_address(id(cairo_ctx)).ctx

    if FT_Err_Ok != _freetype_so.FT_New_Face (_ft_lib, filename, faceindex, ctypes.byref(ft_face)):
        raise Exception("Error creating FreeType font face for " + filename)

    # create cairo font face for freetype face
    cr_face = _cairo_so.cairo_ft_font_face_create_for_ft_face (ft_face, loadoptions)
    if CAIRO_STATUS_SUCCESS != _cairo_so.cairo_font_face_status (cr_face):
        raise Exception("Error creating cairo font face for " + filename)

    _cairo_so.cairo_set_font_face (cairo_t, cr_face)
    if CAIRO_STATUS_SUCCESS != _cairo_so.cairo_status (cairo_t):
        raise Exception("Error creating cairo font face for " + filename)

    face = cairo_ctx.get_font_face ()

    return face