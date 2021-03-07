import tkinter as tk

TITLE = 'AutoOED'

REFRESH_RATE = 100 # ms

GEOMETRY_MAX_WIDTH = 1280
GEOMETRY_WIDTH_RATIO = 0.8
GEOMETRY_HEIGHT_RATIO = 0.5

WIDTH = None
HEIGHT = None

PADX = 10
PADY = 10
COMBOBOX_WIDTH = 10
ENTRY_WIDTH = 5
TEXT_WIDTH = 10
TEXT_HEIGHT = 10
LOGO_WIDTH = 250
LOGO_HEIGHT = 100

def set_resolution():
    global WIDTH, HEIGHT, PADX, PADY

    root = tk.Tk()
    screen_width, screen_height = root.winfo_screenwidth(), root.winfo_screenheight()
    root.destroy()

    if screen_width * GEOMETRY_WIDTH_RATIO > GEOMETRY_MAX_WIDTH:
        WIDTH = GEOMETRY_MAX_WIDTH
    else:
        WIDTH = screen_width * GEOMETRY_WIDTH_RATIO
        
    HEIGHT = WIDTH * GEOMETRY_HEIGHT_RATIO
    if HEIGHT > screen_height:
        HEIGHT = screen_height
    WIDTH, HEIGHT = int(WIDTH), int(HEIGHT)

    if WIDTH < GEOMETRY_MAX_WIDTH or HEIGHT < WIDTH * GEOMETRY_HEIGHT_RATIO:
        PADX = 5
        PADY = 5

set_resolution()