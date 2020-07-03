# Micropython-Editor

## Description

A small text editor written in Python running on 
- MicroPython.org modules like the PYBoards, ESP32, ESP8266, Teensy 3.5, 3.6 and 4.x, W60x
- pycom.io modules like WipPy, Lopy, SiPy, FiPy, GPy
- Adafruit Circuitpython modules,
- SiPeed MaixPy modules,
- Linux and Android's terminal windows

 It allows allows to edit files locally on the boards. The offsprong was the editor widget of pfalcon at
 <https://github.com/pfalcon/pyedit>. I ported it to PyBoard and the other modules
 and added a lot of functions:

- Use sys.stdin.read() and sys.stdout.write() for input and output of the Micropython version.
- Changed the read keyboard function to comply with byte-by-byte input on serial lines.
- Added support for Tab, BackTab, Save, Del and Backspace joining lines, Find,
Replace, Goto Line, Undo, Redo, Open file, Auto-Indent, Set Flags, Copy/Delete & Paste,
Indent, Dedent, Block-Comment, Scrolling, line-shift
- Handling tab (0x09) on reading & writing files,
- Added a status line, and single line prompts for Quit, Save, Find, Replace,
Goto, Open file and Flag settings.
- Support the simultaneous editing of multiple files.
- Basic mouse functions for scrolling up/down, setting the cursor and highlighting text.

The editor assumes a VT100 terminal. It works in Insert mode. The following list
shows most of the commands.:

|Key(s)|Function|
|:---|:---|
|Up Down Left Right| Cursor movement by one line or char|
|Ctrl-Left| Move the cursor left to the start of the (next) word|
|Ctrl-Right| Move the cursor right behind the end of the (next) word|
|Shift-Up -Down -Left -Right| Highlight the text or extend the highlighted area|
|Ctrl-Shift-Left -Right|Highlight the next or previous word or extend the highlighted area|
|Ctrl-Up Ctr-Down|Scroll the windows down/up|
|Alt-Up Alt-Down|Move the current line or highlighted area up/down by one line|
|PgUp & PgDd|Page up/down|
|Home|Toggle the position between the start-of-code and the start of line|
|End|Toggle the position between the end-of-the-code and end-of-line|
|Enter|Enter a line break at the cursor position. Auto-indent is supported|
|Backspace|Delete char left to the  cursor (The key must be set to ASCII-Del). If text are highlighted, delete the highlighted area|
|Del|Delete the char under the cursor. At the end of the line join the next line. If autoindent is enabled, delete also the leading spaces of the joined line. If text are highlighted, delete the highlighted area. In line edit mode, Del as first keystroke will clear the entry.|
|Ctrl-Del|Delete the word under the cursor or space up to the next non-space|
|Ctrl-O|Open a new file. If the file name is left empty, an empty buffer is opened|
|Ctrl-W|Toggle to the next file buffer|
|Ctrl-Q|Close a file buffer or end line-edit|
|Ctrl-S|Save to file with the option to change the file name|
|Ctrl-F|Find|
|Ctrl-N|Repeat the last find|
|Ctrl-H or Ctrl-R|Find and Replace|
|Ctrl-G|Go to a line|
|Ctrl-T|Go to the first line|
|Ctrl-B|Go to the last line|
|Ctrl-K|Goto the bracket matching the one under the cursor|
|Ctrl-Home & Ctr-End|Got to the first/last line|
|Ctrl-L or Ctrl-Space|Start hightlighting at the current position, or clear the highlight. The highlight can then be extended by moving the cursor|
|Ctrl-X|Cut the highlighted text|
|Ctrl-C or Ctrl-D|Copy the highlighted text|
|Ctrl-V|Insert the copied/cut text.|
|Ctrl-Z|Undo the last change(s)|
|Ctrl-Y|Redo the last undo(s), repeating what had been undone by undo|
|Ctrl-P|Comment/Uncomment a line or highlighted area|
|Ctrl-A|Change settings for tab size, search case sensitivity, auto-indent, comment string and writing tabs (opt)|
|Ctrl-E|Redraw the screen. On the Micro devices it shows the amount of free memory|

**Instead of Ctrl-letter (e.g. Ctrl-Q), Alt-letter (e.g. Alt-Q) can be used, avoiding conflicts with key binding of some terminal emulators.**

The editor is contained in the files pye_gen.py pye.py. Start pye from the REPL prompt
e.g. with  

from pye_gen import pye  
res = pye(object_1, object_2, ..[, tabsize=n][, undo=n])  

You may also use the combined version pye_mp.py:

from pye_mp import pye  
res = pye(object_1, object_2, ..[, tabsize=n][, undo=n])  

If object_n is a string, it's considered as the name of a file to be edited
or a directory to be opened. If it’s a file, the content will be loaded,
and the name of the file will be returned when pye is closed. If the
file does not exist, an error is displayed, but the edit window is given that
name. If it’s a directory, the list of file names will be loaded to the edit
window. If object_n is a list of other items, they will be converted to strings 
and edited, and the edited list if strings will be returned. 
If no object is named, pye() will give show the list of files, 
creating a list of strings, unless you save to a file. In that case,
the file name will be returned. 
It is always the last buffer closed, which determines the return value of pye().  

Optional named parameters:

tabsize=n    Tab step (integer). The default is 4  
undo=n  Size of the undo stack (integer). The minimum size is 4.  

The Linux/Darwin version can be called from the command line with:

python3 pye_ux.py [filename(s)]

or using the combined exedcutable version pye:

pye [filename(s)]

Obviously, you may use micropython too. Using python3 (not micropython),
content can also be redirected or pipe'd into the editor.

More details can be found in the doc file. On reading files, tab characters
are expanded to spaces with a tab size of 8, and trailing white space on a
line will be discarded. Optionally, tabs can be written when saving the file, replacing
spaces with tabs when possible. However, the original state of tabs will NOT be restored when
the file is written. The screen size is determined, when the editor is
started, when the Redraw-key (Ctrl-E) is hit or on any file window change (Ctrl-W).

The editor works also well in a Linux or MAC terminal environment (and also in some
terminal apps of Android - tested with Termux), with both python3 and micropython.
For that purpose, a small main() section is embedded in pye_ux.py, which when called with
CPython also accepts data from a pipe or redirection.

## Files

### Base files
- pye.py: Core file with comments, intended to ebtha same for all platforms 
- pye_ux.py: Front-end for Linux CPython and Linux MicroPython
- pye_gen.py: Front-end for Micropython and Circuitpython modules with I/O through
sys.stdout and sys.stdin.
- peteensy.py: A front-end for teensy 3.5 and 3.6 .
- pye_win.py: an experimental version for the cmd window of Windows 10. It requires
enabling the VT100 support, as detailed e.g. here: https://stackoverflow.com/questions/51680709/colored-text-output-in-powershell-console-using-ansi-vt100-codes
- Pyboard Editor.pdf: A short documentation
- strip.sh: sample Shell script which creates the different derived files out of pye.py and
the front-end files, using cat and sed.
- README.md: This one

### Derived files
- pye_mp.py, pye_mp.mpy: Condensed source files of pye.py + pye_gen.py for
all MicroPython boards. In order to use it on an board with small memory
like the esp8266, you have to put pye_mp.py into the directory esp8266/modules,
esp32/modules or smt32/modules (micropython.org) or esp32/frozen (pycom.io) and
rebuild micropython.  A cross-compiled version may executed from the file system.
- pye: Executable single file for Linux

### Further front-ends
- pye_lcd.py: Front-end provided by user @kmatch98 for Circuitpython using a LCD as output
device and UART as input device. The port requires further python scripts.
- lcd_io.md: Readme for the pye_lcd version, provided by @kmatch98.
- pye_tft.py: Sample front-end using a tft with a SSD1963 controller as output device. The port
requires the SSD1963 drivers: https://github.com/robert-hh/SSD1963-TFT-Library-for-PyBoard


## Branches

|Branch|Features|
|:---|:---|
|master|Actual main line with slowly changing features|
|modules| Split pye.py into a core editor and port specific front-ends|
|pye2|Similar to the linemode branch, but the column does not change during vertcal moves (stale)|
|new_mark|Changed method of highlighting blocks, allowing to move away the cursor once a block is highlighted (stale)|

## Short Version History

**1.0** Initial release with all the basic functions

**1.1** Same function set, but simplified keyboard mapping.

- Removed the duplicated definitions for cursor motion keys.
- Allowed both \r and \n for ENTER, and both \x08 and \x7f for BACKSPACE, which
avoid some hassle with terminal settings.
- Removed auto-indent from the minimal version.

**1.2** Mouse support added, as well as some other minor changes.

- Simple Mouse support for scrolling and placing the cursor
- Flags setting for search case, auto-indent on/off and status line on/off
- GOTO line sets cursor to the middle row
- The function pye(..) returns a value now

**1.3** UNDO added. Added a multilevel UNDO (Ctrl-Z) for most functions that

change the content. Other changes:
- Backspace at the first non-blank character mimics BackTab, if Auto-indent is
enabled
- Added a REDRAW (Ctrl-E) function, which checks for the changed screen size
after the window size has been changed.
- Added a line number column on the left side of the screen (can be turned off).
- Improved the scrolling speed, such that it lags less.
- Some code simplification and straightening, such that functions group better
and are easier to understand.

**1.4** GET file added. Adding a function GET (Ctrl-O), which inserts the
content of a file before the current line. Other changes:

- Both HOME and END stop at start of text is passing by on their way to their
destination.
- Flag allowing to replace spaces by Tab when writing the file, complementary to
what is done while reading. Tabsize is 8. A tab is inserted whenever possible,
even if it replaces a single space character.
- Fixed a mild amnesia in UNDO

**1.5** WiPy Port and body shaping:

- Support for WiPy added. WiPy runs only the minimal version.
- Aligned function set of the minimal version, in order to comply with WiPy.
Dropped Mouse support, GET file, Line number column, and write tabs; but
included Tab, Backtab, the buffer functions Yank, Dup & ZAP and scrolling optimization.
- LEFT and RIGHT move to the adjacent line if needed
- When used with Linux **and** CPython, a terminal window resize cause redrawing
the screen content. The REDRAW key (Ctrl-E) stays functional and is required
for all other use cases, when the window size is changed.
- HOME toggles again between start-of-line and start-of-text. END moves always
to end-of-line
- Dropped context sensitive behaviour of Tab, Backtab, Backspace and Delete. Too confusing.
- Dropped the line number column, and made the status line permanent in all modes.
- Rearranged the code such that any platform related sections are grouped together.

**1.6** WiPy fixes and further trimming:

- Making rarely used small functions inline again, which saves some space. Important for WiPy.
- Catch Ctrl-C on WiPy. Not really nice yet, since the next input byte is lost.
- Tab Size can be set with the Ctrl-A command (if available).
- Simplified Linux main(). No calling options any more.
- Always ask when leaving w/o saving after the content was changed.

**1.7** WiPy fixes and other minor changes

- Fixed a memory leak in REDRAW, removed every instance of "del name"
- Changed REDRAW to tell the amount of free memory
- changed wr() for WiPy
- Simplified the internal interface to init_tty()
- Changed the handling of reading an empty file
- Non-supported functions in the minimal version like REPLACE trigger a "Sorry" message
- Try to recover from MemoryError by clearing the line-buffer and UNDO

**1.7a** Size reduction for WiPy & Tabbify for PyBoard

- Reduced KEYMAP in the WiPy version by omitting entries, where the function
code is identical to the key value (e.g. \x08 -> 8). Not fool proof, but it helps
reducing the size.
- Adding a "Tabbify" behaviour for the full version. Tab/Backtab with the cursor
at col 1 indents/unindents the line and moves the cursor one line down.

**1.7b** Further size reduction for WiPy

- Moved setting of the change flag into the function add_undo()
- Removed skipping to the adjacent line with Right/Left in the WiPy Version
- Temporary avoidance of the memory leak when a file is not found

**1.7c** Re-establish try-except for file-not-found error

- Removed the temporary fix for memory corruption by exception for file-not-found error
- Changed string formatting to Python3 style

**1.8** Clean Copy & Paste, Indent, Un-Indent

- Added a Highlight Line key for Line Delete, Line Copy, Indent and Un-Indent
- Fixed a glitch, that allowed to paste text longer
then the available space on the status line. No harm was done, just the screen
content scrolled up. After leaving the line edit mode, a redraw fixed that.
- Changed Line Delete, Line Copy and Buffer Insert into a cleaner Copy & Paste mode
- Added a cleaner Indent and Un-Indent method; for WiPy too
- Removed the attempt to recover from out-of-memory situations: did not work.
- Still runs on WiPy, but really at it's limit

**1.9** Refinement of Highlight and Undo

- Highlight setting affects Save and Replace now. With Save, only the highlighted range is
written, with replace, search & replace is done in the highlighted area only.
- The Undo history is kept after Save. So you can go back to a state before saving
- Removed UART mode on WiPy. Not stable yet. UART mode can be achieved by
redirecting REPL.
- A variant of pye.py, called pye2.py, keeps the cursor column even if the
cursor is moved beyond the text in a line, instead of moving to the end of text
if a line is shorter than the actual cursor column. Another variant, pye3, tries
to go back to the cursor column which once was set by a horizontal move.
That's more how gedit works. Not sure which I like better.

**1.10** Further refinement of Highlight

- When the highlight is set, the whole area affected is now highlighted instead of
just the line with the highlight.
- Paste, Delete and Backspace now also take notice of the line Highlight. You can Highlight
a line range and delete it (or cut it). Implicit deleting highlighted lines when
pressing the Enter or character key was considered but rejected (easy - just 3
    lines of code).
- Except for Delete, Backspace, Cut and Paste, Highlight has to be toggled off when
not needed any more.
- Right click (Button 2) or Ctrl-Click on the mouse sets/unsets the Highlight, left
Click extends it, when set.

**1.11** Minor fixes

- Change the way a highlighted area is highlighted from reverse to a different
background colour. That works well for black chars on yellow background (code 43).
For white chars on black background, the setting for background colour in the
function hilite() has to be changed, e.g. to blue (code 44).
- Save to a temporary file first, and rename it to the target name when
successfully written.
- Lazy screen update: defer screen update, until all chars from the keyboard
are processed. Not provided for WiPY, even if needed there most. WiPy has no
way to tell if more chars are waiting in the input or at least a read with timeout.

**1.12** Bracket Match and Minor changes

- Ctrl-K causes the cursor set to the matching bracket, if any. Pretty raw, not elegant.
Brackets in comments and strings are counting as well.
- On Copy the highlight will be cleared, since it is assumed that the just copied
lines will not be overwritten.
- High level try/except catching internal errors (mostly coding errors)
- Separate cpp options for including scroll optimization, replace or bracket
match into the minimal version. Changes in strip.sh script to generate the
minimal wipye version too.
- Some editorial changes and fixing of typos.

**1.12b** Fixing an inconsistency in the Save command

- Fixing an inconsistency in the Save command, which caused the change flag being
reset when writing just a block
- Squeezing a few lines out of the source code

**1.12c** Speed up pasting again

- Speed up pasting again. Slowing down pasting was caused by an in-function
import statement in V1.11.
- Squeezing another few lines out of the source code by combining two functions,
which were anyhow called one after the other, resulting in an enormous long function
handling the keyboard input.

**1.12d** Split undo of Indent/Un-Indent

- Split undo for Indent and Un-Indent
- Fixed a minor inconvenience when going left at the line start (squeezed too much in v1.12b)
- Move a few lines around, such that keys which are more likely used with fast
repeats are checked for earlier.
- Some editorial changes

**2.0** Edit muliple files

- Support for editing multiple files at once and copy/paste between them
- Ctrl-W steps through the list of files/buffers
- Ctrl-O opens a new file/buffer.

**2.1** Some shrinking for WiPy

- Make Indent/Un-Indent optional in the WiPy version, to allow all variants to
get compiled w/o running out of memory. The final code saving is just a few
hundred bytes, so it's still not clear to me why these few extra lines don’t fit.
- Fixing a glitch which added an extra line when undoing the delete of all lines
- Some shifting around of code lines
- Making the MOUSE support an extra option
- Removed the extra indent after ':' as the last char on the line. More confusing
than helpful.
- Update of the doc file

**2.2** Further cleaning and some slight improvements

- Moved error catching one level up to the function pye(), catching load-file
errors too.
- If open file names a directory, the list of files is loaded to the edit buffer.
- Ctrl-V in line edit mode inserts the first line of the paste buffer
- The WiPy version does not support undo for Indent/Un-indent, even if Indent is
enabled. It is too memory consuming at runtime. It's questionable whether this
is needed at all.
- And of course: update of the doc file

**2.3** Minor fixes & changes

- Catched file not found errors when starting pye, introduced in version 2.2
- Added a flag to pye2 such that it supports both vertical cursor movement types
- use uos.stat with micropython, since os.stat is not supported on linux-micropython
- When opening a directory, replace the name '.' by the result of os.getcwd(),
avoiding error 22 on PyBoard and WiPy

**2.4** Fix for the regular expression search variant

- Fix a glitch, that the regular expression variant of search and replace did
not find patterns anchored at the end, single line starts or single line endings.
That fix required changes not only to the find function, such that all variants
of pye are affected.
- Consider '.' **and** '..' in file open as directory names, avoiding stat() on these.

**2.5** Fix a small bug of edit_line()'s paste command

- Fixed a glitch, that allowed to paste text longer then the available space on
the status line. No harm was done, just the screen content scrolled up. After
leaving the line edit mode, a redraw fixed that.

**2.6** Adapted to change lib names in micropython

- For micropython replaced \_io with uio
- Preliminary esp8266 version.

**2.7** Change file save method and settings dialogue

- Further adaptation to esp8266, which is now identical to the WiPy version
- Changed file save method, such that it works now across devices
- Made settings dialogue visible in basic mode, allowing to change both the
autoindent flag and the search case flag
- Create the ESP8266 version with all features but mouse support.

**2.8** Support of UTF-8 characters on keyboard input

- This in implemented for all versions. However WiPy does not support it in
the lower levels of sys.stdin.

**2.9** Support for teensy 3.5 and 3.6

- The only change was to add the teensy names to the platform detection
- Implement full function set for line-edit by default

**2.10** Support for esp32; simplified mouse handling

- The only change was adding the esp32  name to the platform detection
- Do not use global symbols for mouse parameters

**2.11** Small changes to the esp8266 version

- Faster paste from the keyboard
- Enabled Mouse support as default

**2.12** Use the kbd_intr() method to disable Keyboard Interrupts on Ctrl-C.

This method is supported by (almost) all micropython.org ports and maybe
sometime also supported by the pycom.io ports. The method of trying to catch
KeyboardInterrupt is still present.

**2.13** Reduce the numer of derived variants and make the full version the
default one. Update the documentation.

**2.14** Remove the PyBoard support using an UART as keyboard/display interface.
Use kbd_intr() too on Pyboard.

**2.15** Make a combined MicroPython version, which runs on all boards except Teensy 3.5 / 3.6. For teensy, a short wrapper is included.

**2.16** Optimize search with Regular expressions

**2.17** Remove all option variants from the source files, and make pye_sml.py
a pure micropython boards version with reduced function set. The only options
remaining are Linux/CPython vs. MicroPython

**2.18** On deleting the end of a line, remove space characters from the joined line, if autoindent is active. This behavior mirrors autoindent.

**2.19** Add a toggle key for commenting/uncommenting a line or highlighted area. The
 default comment string is '#', but can be changed through the settings command.

**2.20** Change the End-Key to toggle between EOL and last non-space char.

**2.21** Add Ctrl-\ as alternative key to close a file

**2.22** Add Ctrl-Space asl alternative to highlight line (Ctrl-L), and Block comment adds the comment string after leading spaces.

**2.23** Change the End key to toggle between end-of-line and end-of-code

**2.24** Changed the Paste key in line edit mode, in that it pastes the word under the cursor of the active window.

**2.25** Version number is shown with redraw command, and thus at startup and
window change

**2.26** Better separation of port-specific and OS-specific flags

**2.27** Change Homw/End key behavior. Py w/o filename will open a window with
the list of files in the current dir

**2.28** Add word left & right with ctrl-left and ctrl-right

**2.29** Add shift-up and shift-down for setting/extending the highlighted area

**2.30** Add Delete Word with Ctr-Del

**2.31** Re-Map Ctrl-Up and Ctrl-Down for scrolling

**2.32** Comment toggle ignores emty lines

**2.33** Scroll step is 1 for keyboard and 3 for mouse

**2.34** Added a branch with character mode highlight/cut/paste/delete. Intended to be the new master

**2.35** Change behaviour of the column position durign vertical moves, in that it tries to keep the position

**2.36** Add the redo function, which restates changes undone by undo.

**2.37** Entering text replaces an highlighted area.

**2.38** Add Ctrl-Shift-Left and Ctrl-Shift-Right for move & highlight 

**2.39** Move a line with Alt-Up and Alt-Dn

**2.40** Extend move up/down to move highlighted areas too.

**2.47** Move all terminal control strings into an list.

**2.48** Split pye.py into a core file and port specific front-ends. If a single file is required, just put the core and the front-end into a single file.

**2.49** Change the default search item behavior of find and replace as well as open file.

**2.50** Limit the span for bracket match to 50 lines and improve the speed