'''
Parameters of the GUI.
'''

import tkinter as tk


# refresh rate
REFRESH_RATE = 100 # ms

# window resolution
MAX_WIDTH = 1280
WIDTH_RATIO = 0.8
HEIGHT_RATIO = 0.6
WIDTH = None
HEIGHT = None

# widget resolution
PADX = 10
PADY = 10
COMBOBOX_WIDTH = 10
ENTRY_WIDTH = 5
TEXT_WIDTH = 10
TEXT_HEIGHT = 10

# logo resolution
LOGO_WIDTH = 250
LOGO_HEIGHT = 100

# figure resolution
FIGURE_DPI = 100

# adapt resolution to screen
def set_resolution():
    global WIDTH, HEIGHT, PADX, PADY, FIGURE_DPI

    # detect screen resolution
    root = tk.Tk()
    screen_width, screen_height = root.winfo_screenwidth(), root.winfo_screenheight()
    root.destroy()

    # set window width
    if screen_width * WIDTH_RATIO > MAX_WIDTH:
        WIDTH = MAX_WIDTH
    else:
        WIDTH = screen_width * WIDTH_RATIO
        
    # set window height
    HEIGHT = WIDTH * HEIGHT_RATIO
    if HEIGHT > screen_height:
        HEIGHT = screen_height
    WIDTH, HEIGHT = int(WIDTH), int(HEIGHT)

    # if small window
    if WIDTH < MAX_WIDTH or HEIGHT < WIDTH * HEIGHT_RATIO:

        # set window resolution
        PADX = 5
        PADY = 5

        # set figure resolution
        FIGURE_DPI = 90

set_resolution()