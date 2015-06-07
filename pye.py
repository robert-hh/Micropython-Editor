##
## Very simple VT100 terminal text editor widget
## Copyright (c) 2015 Paul Sokolovsky
## Distributed under MIT License
## some code mangling by Robert Hammelrath, 2015, making it quite a little bit larger:
## - Ported the code to pyboard (still runs on Linux Python3 and on Linux Micropython)
##   It uses VCP_USB on Pyboard, but that may easyly be changed to UART
## - changed read keyboard function to comply with char-by-char input (on serial lines)
## - added support for TAB, BACKTAB, SAVE, DEL at end joining lines, Find, 
## - Goto Line, Yank (delete line into buffer), Zap (insert buffer)
## - moved main into a function with some optional parameters
## - Added a status line and single line prompts for Quit, Save, Find and Goto
##
import sys
##import re  ## needed for regex search
#ifdef LINUX
if sys.platform == "linux":
    import os
#endif
#ifdef PYBOARD
if sys.platform == "pyboard":
    import pyb
#endif
#ifdef DEFINES
#define KEY_UP      0x4001
#define KEY_DOWN    0x4002
#define KEY_LEFT    0x4003
#define KEY_RIGHT   0x4004
#define KEY_HOME    0x4005
#define KEY_END     0x4006
#define KEY_PGUP    0x4007
#define KEY_PGDN    0x4008
#define KEY_QUIT    0x4009
#define KEY_ENTER   0x400a
#define KEY_BACKSPACE 0x400b
#define KEY_DELETE  0x400c
#define KEY_WRITE   0x400d
#define KEY_TAB     0x400e
#define KEY_BACKTAB 0x400f
#define KEY_FIND    0x4010
#define KEY_GOTO    0x4011
#define KEY_FIRST   0x4012
#define KEY_LAST    0x4013
#define KEY_FIND_AGAIN 0x4014
#define KEY_YANK    0x4015
#define KEY_ZAP     0x4017
#define KEY_AITOGL  0x4018
#define KEY_REPLC   0x4019
#else
KEY_UP      = 0x4001
KEY_DOWN    = 0x4002
KEY_LEFT    = 0x4003
KEY_RIGHT   = 0x4004
KEY_HOME    = 0x4005
KEY_END     = 0x4006
KEY_PGUP    = 0x4007
KEY_PGDN    = 0x4008
KEY_QUIT    = 0x4009
KEY_ENTER   = 0x400a
KEY_BACKSPACE = 0x400b
KEY_DELETE  = 0x400c
KEY_WRITE   = 0x400d
KEY_FIND    = 0x4010
KEY_FIND_AGAIN = 0x4014
KEY_GOTO    = 0x4011
#ifndef BASIC
KEY_FIRST   = 0x4012
KEY_LAST    = 0x4013
KEY_YANK    = 0x4015
KEY_TAB     = 0x400e
KEY_BACKTAB = 0x400f
KEY_ZAP     = 0x4017
KEY_AITOGL  = 0x4018
KEY_REPLC   = 0x4019
#endif
#endif

class Editor:

    KEYMAP = { ## Gets lengthy
    b"\x1b[A" : KEY_UP,
    b"\x1b[B" : KEY_DOWN,
    b"\x1b[D" : KEY_LEFT,
    b"\x1b[C" : KEY_RIGHT,
    b"\x0b"   : KEY_UP,   ## Ctrl-K
    b"\x0a"   : KEY_DOWN, ## Ctrl-J
    b"\x08"   : KEY_LEFT, ## Ctrl-H
    b"\x0c"   : KEY_RIGHT,## Ctrl-L
    b"\x1b[H" : KEY_HOME, ## in Linux Terminal
    b"\x1bOH" : KEY_HOME, ## Picocom, Minicom
    b"\x1b[1~": KEY_HOME, ## Putty
    b"\x17"   : KEY_HOME, ## Ctrl W
    b"\x1b[F" : KEY_END,  ## Linux Terminal
    b"\x1bOF" : KEY_END,  ## Picocom, Minicom
    b"\x1b[4~": KEY_END,  ## Putty
    b"\x05"   : KEY_END,  ## Ctrl-E
    b"\x1b[5~": KEY_PGUP,
    b"\x0f"   : KEY_PGUP, ## Ctrl-O
    b"\x1b[6~": KEY_PGDN,
    b"\x10"   : KEY_PGDN, ## Ctrl-P
    b"\x11"   : KEY_QUIT, ## Ctrl-Q
    b"\x03"   : KEY_QUIT, ## Ctrl-C as well
    b"\r"     : KEY_ENTER,
    b"\x7f"   : KEY_BACKSPACE, ## Ctrl-? (127)
    b"\x1b[3~": KEY_DELETE,
    b"\x19"   : KEY_DELETE, ## Ctr-Y
    b"\x13"   : KEY_WRITE,  ## Ctrl-S
    b"\x06"   : KEY_FIND, ## Ctrl-F
    b"\x0e"   : KEY_FIND_AGAIN, ## Ctrl-N
    b"\x07"   : KEY_GOTO, ##  Ctrl-G
    b"\x14"   : KEY_FIRST, ## Ctrl-T
    b"\x1b[1;5H": KEY_FIRST,
    b"\x02"   : KEY_LAST,  ## Ctrl-B
    b"\x1b[1;5F": KEY_LAST,
    b"\x1b[3;5~": KEY_YANK,
    b"\x18"   : KEY_YANK, ## Ctrl-X
    b"\x09"   : KEY_TAB,
    b"\x1b[Z" : KEY_BACKTAB, ## Shift Tab
    b"\x15"   : KEY_BACKTAB, ## Ctrl-U
    b"\x16"   : KEY_ZAP, ## Ctrl-V
    b"\x01"   : KEY_AITOGL, ## Ctrl-A
    b"\x12"   : KEY_REPLC, ## Ctrl-R
    }

    def __init__(self, tab_size, status):
        self.top_line = 0
        self.cur_line = 0
        self.row = 0
        self.col = 0
        self.margin = 0
        self.k_buffer = b""
        self.tab_size = tab_size
        self.status = status
        self.autoindent = True
        self.changed = ' '
        self.message = ""
        self.find_pattern = ""
        self.replc_pattern = ""
        self.y_buffer = []
        self.lastkey = 0
#ifdef LINUX
    if sys.platform == "linux":

        @staticmethod
        def wr(s):
            ## TODO: When Python is 3.5, update this to use only bytes
            if isinstance(s, str):
                s = bytes(s, "utf-8")
            os.write(1, s)

        @staticmethod
        def rd():
           return os.read(0,1)
#endif
#ifdef PYBOARD
    if sys.platform == "pyboard":
    
        @staticmethod
        def wr(s):
            ns = 0
            while ns < len(s): # complicated but needed, since USB_VCP.write() has issues
                res = Editor.serialcomm.write(s[ns:])
                if res != None: 
                    ns += res

        @staticmethod
        def rd():
            while not Editor.serialcomm.any():
                pass
            return Editor.serialcomm.read(1)
#endif

    @staticmethod
    def cls():
        Editor.wr(b"\x1b[2J")

    @staticmethod
    def goto(row, col):
        ## TODO: When Python is 3.5, update this to use bytes
        Editor.wr("\x1b[%d;%dH" % (row + 1, col + 1))

    @staticmethod
    def clear_to_eol():
        Editor.wr(b"\x1b[0K")

    @staticmethod
    def cursor(onoff):
        if onoff:
            Editor.wr(b"\x1b[?25h")
        else:
            Editor.wr(b"\x1b[?25l")

    @staticmethod
    def hilite(onoff):
        if onoff:
            Editor.wr(b"\x1b[1m")
        else:
            Editor.wr(b"\x1b[0m")

    def c_or_f(self):  ## read from interface/keyboard one byte each and match against function keys
        if len(self.k_buffer) == 0:
            self.k_buffer += Editor.rd()  ## get one char to start with
        while True:
            for k in self.KEYMAP.keys():
                if self.k_buffer == k[:len(self.k_buffer)]:  ## content of buffer matches start of escape sequence
                    if self.k_buffer == k:
                        c = self.KEYMAP[self.k_buffer]
                        self.k_buffer = b""
                        return c ## found a function key
                    else:  ## start matches, but there must be more: get another char
                        break
            else:   ## nothing matched, return first char from buffer
                c = self.k_buffer[0]
                self.k_buffer = self.k_buffer[1:]
                return c
## something matched, get more
            self.k_buffer += Editor.rd()   ## get one more char

## check, if cursor beyond EOL, and correct. Return True if update_screen() was called
    def adjust_cursor_eol(self): 
        self.col = min(self.col, len(self.content[self.cur_line]) - self.margin) 
        if not (0 <= self.col < self.width): # Screen update required?
            return self.adjust_col(True) 

## Update col and screen if out of view. Return True if update_screen() was called
    def adjust_col(self, updt):
        ## If Updt is True, redraw
            if self.col >= self.width:
                self.margin = self.col + self.margin - (self.width - 1) + self.hstep
                self.col = self.width - 1 - self.hstep
                self.update_screen()
                return True
            elif self.col < 0:
                val = self.col + self.margin # Major difference to adjust_cursor_eol()
                self.margin = max(self.margin - self.width, 0)
                self.col = val - self.margin
                self.update_screen()
                return True
            else:
                if updt: self.update_line()
                return False

## If self.cur_line is already on screen, just set row accordinly
## Otherwise, update top_line and display the screen, but keep row
## Return True if update_screen() was called

    def adjust_row(self):
        ## Includes redraw
        if self.top_line <= self.cur_line < self.top_line + self.height: # Visible?
            self.row = self.cur_line - self.top_line
            return self.adjust_cursor_eol() # check for hor. shifts
        else:
            self.top_line = self.cur_line - self.row
            if self.top_line < 0:
                self.top_line = 0
                self.row = self.cur_line
            if not self.adjust_cursor_eol(): # check for hor. shifts
                self.update_screen() 
            return True

    def set_lines(self, lines, fname):
        self.content = lines
        self.total_lines = len(lines)
        self.fname = fname

    def update_screen(self):
        self.cursor(False)
        self.cls()
        self.cursor(False)
        i = self.top_line
        for c in range(self.height):
            self.goto(c, 0)
            if i == self.total_lines:
                self.clear_to_eol()
            else:
                self.show_line(self.content[i])
                i += 1
        self.cursor(True)

    def update_line(self):
        self.cursor(False)
        self.goto(self.row, 0)
        self.show_line(self.content[self.cur_line])
        self.cursor(True)

    def show_line(self, l):
        l = l[self.margin:]
        l = l[:self.width]
        self.wr(l.replace("\x09", "→"))
        if len(l) < self.width: self.clear_to_eol()

    def show_status(self):
        if self.status or self.message:
            self.cursor(False)
            self.goto(self.height, 0)
            self.hilite(True)
            self.wr("%c Ln: %d Col: %d  %s" % \
                    (self.changed, self.cur_line + 1, self.col + self.margin + 1, self.message))
            self.clear_to_eol()
            self.hilite(False)
            self.cursor(True)

    def clear_status(self):
        if (not self.status) and self.message:
            self.goto(self.height, 0)
            self.clear_to_eol()
        self.message = ''

    def spaces(self, line, pos = 0): ## count spaces
        if pos: ## left to the cursor
            return len(line[:pos]) - len(line[:pos].rstrip(" "))
        else: ## at line start
            return len(line) - len(line.lstrip(" "))

    def line_edit(self, prompt, default):  ## simple one: only 3 fcts
        self.goto(self.height, 0)
        self.hilite(True)
        self.wr(prompt)
        self.wr(default)
        self.clear_to_eol()
        res = default
        self.message = ' ' # Shows status after lineedit
        while True:
            key = self.c_or_f()  ## Get Char of Fct.
            if key == KEY_ENTER: ## Finis
                self.hilite(False)
                return res
            elif key == KEY_QUIT: ## Abort
                self.hilite(False)
                return None
            elif key in (KEY_BACKSPACE, KEY_DELETE): ## Backspace
                if (len(res) > 0):
                    res = res[:len(res)-1]
                    self.wr('\b \b')
            elif 0x20 <= key < 0x100: ## char to be added at the end
                res += chr(key)
                self.wr(chr(key))
            else:  ## ignore everything else
                pass

    def find_in_file(self, pattern, pos):
        self.find_pattern = pattern # remember it
        spos = pos + self.margin
        for line in range(self.cur_line, self.total_lines):
            match = self.content[line][spos:].lower().find(pattern)
            if match >= 0:
                break
            spos = 0
        else:
            self.message = pattern + " not found"
            return False
        self.col = match - self.margin
        self.cur_line = line
        self.adjust_col(False)
        self.adjust_row()
        return True

    def handle_cursor_keys(self, key): ## keys which move
        if key == KEY_DOWN:
            if self.cur_line + 1 < self.total_lines:
                self.cur_line += 1
                self.adjust_row()
        elif key == KEY_UP:
            if self.cur_line > 0:
                self.cur_line -= 1
                self.adjust_row()
        elif key == KEY_LEFT:
            self.col -= 1
            self.adjust_col(False)
        elif key == KEY_RIGHT:
            self.col += 1
            self.adjust_cursor_eol()
        elif key == KEY_HOME:
            ns = self.spaces(self.content[self.cur_line])
            if self.col + self.margin > ns:
                self.col = ns - self.margin
            else:    
                self.col = -self.margin
            self.adjust_col(False)
        elif key == KEY_END:
            self.col = len(self.content[self.cur_line]) - self.margin
            self.adjust_col(False)
        elif key == KEY_PGUP:
            self.cur_line -= self.height
            if self.cur_line < 0:
                self.cur_line = 0
            self.adjust_row()
        elif key == KEY_PGDN:
            self.cur_line += self.height
            if self.cur_line >= self.total_lines:
                self.cur_line = self.total_lines - 1
            self.adjust_row()
        elif key == KEY_FIND:
            pat = self.line_edit("Find: ", self.find_pattern)
            if pat:
                self.find_in_file(pat.lower(), self.col)
        elif key == KEY_FIND_AGAIN:
            self.find_in_file(self.find_pattern, self.col + 1)
            self.message = ' ' ## force status once
        elif key == KEY_GOTO: ## goto line
            line = self.line_edit("Goto Line: ", "")
            if line:
                self.cur_line = min(self.total_lines - 1, max(int(line) - 1, 0))
                self.adjust_row()
#ifndef BASIC
        elif key == KEY_FIRST: ## first line
            self.cur_line = 0
            self.adjust_row()
        elif key == KEY_LAST: ## last line
            self.cur_line = self.total_lines - 1
            self.adjust_row()
            self.message = ' ' ## force status once
        elif key == KEY_AITOGL: ## Toggle Autoindent
            self.autoindent = not self.autoindent
            self.message = "Autoindent %s" % self.autoindent
#endif
        else:
            return False
        return True

    def handle_buffer_keys(self, key): ## just one
            if key == KEY_WRITE:
                fname = self.line_edit("File Name: ", self.fname)
                if fname:
                    try:
                        with open(fname, "w") as f:
                            self.wr(" ..Saving..")
                            for l in self.content:
                                f.write(l + '\n')
                        self.changed = " "
                    except:
                        pass
            else:
                return False
            return True

    def handle_key(self, key): ## keys which change content
        l = self.content[self.cur_line]
        sc = self.changed
        self.changed = '*'
        if key == KEY_ENTER:
            self.content[self.cur_line] = l[:self.col + self.margin]
            if self.autoindent and self.col + self.margin > 0:
                ni = self.spaces(l, 0)
##                if self.content[self.cur_line].partition(":")[1] == ':':
##                   ni += self.tab_size
            else:
                ni = 0
            self.cur_line += 1
            self.content[self.cur_line:self.cur_line] = [' ' * ni + l[self.col + self.margin:]]
            self.total_lines += 1
            self.col = ni - self.margin
            if not self.adjust_row(): ## if not done there
                self.update_screen() ## do it here
        elif key == KEY_BACKSPACE:
            if self.col + self.margin:
                self.content[self.cur_line] = l[:self.col + self.margin - 1] + l[self.col + self.margin:]
                self.col -= 1
                self.adjust_col(True)
#ifndef BASIC
            elif self.cur_line: # at the start of a line, but not the first
                self.col = len(self.content[self.cur_line - 1])
                self.content[self.cur_line - 1] += l
                del self.content[self.cur_line]
                self.cur_line -= 1
                self.total_lines -= 1
                self.adjust_col(False)
                if not self.adjust_row(): ## if not done there
                    self.update_screen() ## do it here
#endif
            else:
                self.changed = sc
        elif key == KEY_DELETE:
            if (self.col + self.margin) < len(l):
                l = l[:self.col + self.margin] + l[self.col + self.margin + 1:]
                self.content[self.cur_line] = l
                self.update_line()
            elif (self.cur_line + 1) < self.total_lines: ## test for last line
                self.content[self.cur_line] = l + self.content.pop(self.cur_line + 1)
                self.total_lines -= 1
                self.update_screen()
            else:
                self.changed = sc
#ifndef BASIC
        elif key == KEY_YANK:  # delete line into buffer
            if key == self.lastkey: # yank series?
                self.y_buffer.append(l) # add line
            else:
                del self.y_buffer # set line
                self.y_buffer = [l]
            self.y_mode = True
            if self.total_lines > 1: ## not a single line
                del self.content[self.cur_line]
                self.total_lines -= 1
                if self.cur_line  >= self.total_lines: ## on last line move pointer
                    self.cur_line -= 1
            else: ## line is kept but wiped
                self.content[self.cur_line] = ''
            if not self.adjust_row(): ## if no update here
                self.update_screen()  ## do it here
        elif key == KEY_TAB: ## TABify line 
            ns = self.spaces(l, 0)
            ni = self.tab_size - ns % self.tab_size
            self.content[self.cur_line] = l[:self.col + self.margin] + ' ' * ni + l[self.col + self.margin:]
            if ns == len(l) or self.col + self.margin >= ns: # lines of spaces or in text
                self.col += ni # move cursor
            self.adjust_col(True)
        elif key == KEY_BACKTAB: ## unTABify line
            ns = self.spaces(l, 0)
            if ns and self.col + self.margin < ns: # at BOL
                ni = (ns - 1) % self.tab_size + 1
                self.content[self.cur_line] = l[ni:]
                self.adjust_col(True)
            else: # left to cursor & move
                ns = self.spaces(l, self.col + self.margin)
                ni = (self.col + self.margin - 1) % self.tab_size + 1
                if (ns >= ni):
                    self.content[self.cur_line] = l[:self.col + self.margin - ni] + l[self.col + self.margin:]
                    self.col -= ni    
                    self.adjust_col(True)
                else:
                    self.changed = sc
        elif key == KEY_ZAP: ## insert buffer
            if self.y_buffer:
                self.content[self.cur_line:self.cur_line] = self.y_buffer # insert lines
                self.total_lines += len(self.y_buffer)
                if not self.adjust_cursor_eol(): ## if not done here
                    self.update_screen() ## do it here
            else:
                self.changed = sc
        elif key == KEY_REPLC:
            pat = self.line_edit("Find: ", self.find_pattern)
            if pat:
                rpat = self.line_edit("Replace with: ", self.replc_pattern)
                if rpat != None:
                    self.replc_pattern = rpat
                    count = 0
                    q = ''
                    while True:
                        if self.find_in_file(pat.lower(), self.col):
                            if q != 'a':
                                self.update_screen() ## do it here
                                self.goto(self.height, 0)
                                self.wr("Replace (yes/No/all/quit) ? ")
                                self.goto(self.row, self.col)
                                key = self.c_or_f()  ## Get Char of Fct.
                                q = chr(key).lower()
                            if q == 'q' or key == KEY_QUIT: 
                                break
                            elif q in ('a','y'):
                                self.content[self.cur_line] = self.content[self.cur_line][:self.col + self.margin] + rpat +  self.content[self.cur_line][self.col + self.margin + len(pat):]
                                self.col += len(rpat)
                                count += 1
                            else: ## everything else is no
                                self.col += len(pat)
                        else:
                            break
                    self.update_screen() ## do it here
                    self.message = "Replaced %d times" % count
                else:
                    self.changed = sc
            else:
                self.changed = sc
#endif
        elif 32 <= key < 0x4000:
            self.content[self.cur_line] = l[:self.col + self.margin] + chr(key) + l[self.col + self.margin:]
            self.col += 1
            self.adjust_col(True)
        else: # Ctrl key or not supported function, ignore
            self.changed = sc

    def loop(self): ## main editing loop
        self.update_screen()
        while True:
            self.show_status()
            self.goto(self.row, self.col) ## deferred
            key = self.c_or_f()  ## Get Char of Fct-key code
            self.clear_status()
            
            if key == KEY_QUIT:
                if self.changed != ' ':
                    res = self.line_edit("Content changed! Quit without saving (y/N)? ", "N")
                    if not res or res[0].upper() != 'Y':
                        continue
                return None
            elif key == KEY_WRITE:
                fname = self.line_edit("File Name: ", self.fname)
                if fname:
                    try:
                        with open(fname, "w") as f:
                            self.wr(" ..Saving..")
                            for l in self.content:
                                f.write(l + '\n')
                        self.changed = " "
                    except:
                        pass
            elif  self.handle_cursor_keys(key):
                pass
            else: self.handle_key(key)
            self.lastkey = key

    def init_tty(self, device, baud):
#ifdef PYBOARD
        if sys.platform == "pyboard":
            if (device):
                Editor.serialcomm = pyb.UART(device, baud)
            else:
                Editor.serialcomm = pyb.USB_VCP()
                Editor.serialcomm.setinterrupt(-1)
            Editor.sdev = device
#endif
#ifdef LINUX        
        if sys.platform == "linux":
            import tty, termios
            self.org_termios = termios.tcgetattr(0)
            tty.setraw(0)
#endif
        ## Print out a sequence of ANSI escape code which will report back the size of the window.
        self.wr(b'\x1b7\x1b[r\x1b[999;999H\x1b[6n')
        pos = b''
        while True:
            char = self.rd()
            if char == b'R':
                break
            if char != b'\x1b' and char != b'[':
                pos += char
        self.wr(b'\x1b8')
        (height, width) = [int(i, 10) for i in pos.split(b';')]
        self.height = height - 1
        self.width = width
        self.hstep = int(width / 6)

    def deinit_tty(self):
        ## Do not leave cursor in the middle of screen
        self.goto(self.height, 0)
        self.clear_to_eol()
#ifdef PYBOARD
        if sys.platform == "pyboard":
            Editor.serialcomm.setinterrupt(3)
#endif
#ifdef LINUX        
        if sys.platform == "linux":
            import termios
            termios.tcsetattr(0, termios.TCSANOW, self.org_termios)
#endif

    def term_size(self):
        ## Print out a sequence of ANSI escape code which will report back the size of the window.
        self.wr(b'\x1b7\x1b[r\x1b[999;999H\x1b[6n')
        pos = b''
        while True:
            char = self.rd()
            if char == b'R':
                break
            if char != b'\x1b' and char != b'[':
                pos += char
        self.wr(b'\x1b8')
        (height, width) = [int(i, 10) for i in pos.split(b';')]
        return height, width

def pye(name="", content=[""], tab_size=4, status=True, device=0, baud=38400):

    if name:
       try:
            with open(name) as f:
                content = [l.rstrip('\r\n') for l in f]
       except Exception as err:
            print("Could not load %s, Reason %s" % (name, err))
            return              
    else:
        content = ["", ""]

    e = Editor(tab_size, status)
    e.init_tty(device, baud)
    e.set_lines(content, name)
    e.loop()
    e.deinit_tty()
 ## clean up memory
    if name:
        content.clear()
#ifdef PYBOARD
    if sys.platform == "pyboard":
        import gc
        gc.collect()
#endif
#ifdef LINUX
if __name__ == "__main__":
    if sys.platform == "linux":
        import getopt
        args_dict = {'-t' : '4'}
        try:
            options, args = getopt.getopt(sys.argv[1:],"t:") ## get the options -t x -s B
        except:
            print ("Undefined option in: " + ' '.join(sys.argv[1:]))
            sys.exit()
        args_dict.update( options ) ## Sort the input into the default parameters
        if len(args) > 0:
            name = args[0]
        else:
            name = ""
        pye(name, [], tab_size=int(args_dict["-t"]))
#endif

#ifdef JUNK
## this is still syntactically correct python code, even if it is never executed.
##
    if False:
##
## This is the regex version of find. Standard search is up north

        def find_in_file(self, pattern, pos):
            self.find_pattern = pattern ## remember it
            try:
                rex = re.compile(pattern)
            except:
                self.message = "Invalid pattern: " + pattern
                return True
            spos = pos + self.margin
            for line in range(self.cur_line, self.total_lines):
                match = rex.search(self.content[line][spos:].lower())
                if match:
                    break
                spos = 0
            else:
                self.message = pattern + " not found"
                return False
## pyboard does not support span(), therefere a second simple find on the target line
#ifdef PYBOARD
            if sys.platform == "pyboard":
                self.col = max(self.content[line][spos:].lower().find(match.group(0)), 0) + spos - self.margin
#endif
#ifdef LINUX
            if sys.platform == "linux":
                self.col = match.span()[0] + spos - self.margin
#endif
            self.cur_line = line
            self.adjust_col(False)
            self.adjust_row()
            return True
#endif

