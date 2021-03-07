TITLE = 'AutoOED'

REFRESH_RATE = 100 # ms

GEOMETRY_MAX_WIDTH = 1280
GEOMETRY_WIDTH_RATIO = 0.8
GEOMETRY_HEIGHT_RATIO = 0.5

def set_resolution(root):
    screen_width, screen_height = root.winfo_screenwidth(), root.winfo_screenheight()
    if screen_width * GEOMETRY_WIDTH_RATIO > GEOMETRY_MAX_WIDTH:
        width = GEOMETRY_MAX_WIDTH
    else:
        width = screen_width * GEOMETRY_WIDTH_RATIO
    height = GEOMETRY_HEIGHT_RATIO * width
    root.geometry(f'{int(width)}x{int(height)}')

PADX = 10
PADY = 10
COMBOBOX_WIDTH = 10
ENTRY_WIDTH = 5
TEXT_WIDTH = 10
TEXT_HEIGHT = 10
LOGO_WIDTH = 250
LOGO_HEIGHT = 100
