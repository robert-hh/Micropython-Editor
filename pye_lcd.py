#
# Wrapper for Micropython standard console IO
#
import sys

class IO_DEVICE:
    def __init__(self, Editor):
        self.init_display();
        self.init_terminal();

        Editor.KEYMAP['\x08'] = 0x08
        
        import busio, board
        self.uart = busio.UART(board.TX, board.RX, baudrate=115200,
                               timeout=0.1, receiver_buffer_size=64)
            
        try:
            from micropython import kbd_intr
            kbd_intr(-1)
        except ImportError:
            pass

    def init_display(self):
        import fontio, displayio, terminalio, board
        from adafruit_st7789 import ST7789
        displayio.release_displays()

        spi = board.SPI()
        tft_cs = board.D12 # arbitrary, pin not used for my display
        tft_dc = board.D2
        tft_backlight = board.D4
        tft_reset=board.D3

        while not spi.try_lock():
            pass
        spi.unlock()

        display_bus = displayio.FourWire(
            spi,
            command=tft_dc,
            chip_select=tft_cs,
            reset=tft_reset,
            baudrate=24000000,
            polarity=1,
            phase=1,
        )

        self.xPixels = 240  # number of xPixels for the display
        self.yPixels = 240  # number of yPixels for the display

        self.display = ST7789(display_bus, width=self.xPixels, height=self.yPixels, 
                              rotation=0, rowstart=80, colstart=0)
        self.display.show(None)

    def init_terminal(self):
        from simpleTerminal import editorTerminal
        self.terminal = editorTerminal(self.display,
                                       displayXPixels=self.xPixels,
                                       displayYPixels=self.yPixels)

    def wr(self,s):
        self.terminal.write(s)

    def rd(self):
        while True:
            myInput = self.uart.read(1) # for using uart
            if myInput:
                return myInput.decode('utf-8')

    def rd_raw(self): ## just to have it implemented
        return self.rd()

    def deinit_tty(self):
        self.uart.deinit()  # clear out the UART
        self.display.show(None)  # remove the groups from the display
        try:
            from micropython import kbd_intr
            kbd_intr(3)
        except ImportError:
            pass

    def get_screen_size(self):
        return self.terminal.getScreenSize()
        
## test, if the Editor class is already present
if "pye_edit" not in globals().keys():
    from pye import pye_edit, Editor

def pye(*args, tab_size=4, undo=50):
    io_device = IO_DEVICE(Editor)
    ret = pye_edit(args, tab_size=tab_size, undo=undo, io_device=io_device)
    io_device.deinit_tty()
    return ret
