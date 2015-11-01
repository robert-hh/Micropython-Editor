#Pyboard-Editor

**Description**

A small text editor written in Python running on PYBoard, allowing to edit files locally. It is based on the editor widget of pfalcon at https://github.com/pfalcon/pyedit. I ported it to PyBoard and added a few functions:

- Use USB_VCP or UART for input and output.
- Changed the read keyboard function to comply with slow byte-by-byte input on serial lines.
- Added support for TAB, BACKTAB, SAVE, FIND, REPLACE, GOTO line, YANK (delete line into a buffer), DUP (copy line into a buffer), ZAP (insert buffer), UNDO and GET (file)
- Join Lines by 'Delete Char' at the end or Backspace at the beginning of a line, Auto-indent for ENTER, context sensitive TAB, BACKTAB, HOME and and BACKSPACE
- Moved main into a function with some optional parameters
- Added an optional status line and single line prompts for QUIT, SAVE, FIND, REPLACE, GOTO, GET and Toggles.
  The status line can be turned (almost) off for slow connections.
- Support of the basic mouse functions scrolling up/down and setting the cursor.

The editor assumes a VT100 terminal. It works in Insert mode. Cursor Keys, Home, End, PgUp, PgDn, Del and Backspace work as you would expect. The additional functions like FIND etc. are available with Ctrl-Keys. On reading files, tab characters are expanded to spaces with a tab size of 8, and trailing white space on a line will be discarded. The orginal state of tabs will not be restored when the file is written. Optionally, tabs can be written when saving the file, replacing spaces with tabs when possible. The screen size is determined, when the editor is started or when the Redraw-key (Ctrl-E) is hit.

The editor works also well in a Linux or MAC terminal environment, with both python3 and micropython. For that purpose, a small main() section is embedded, which also accepts data from a pipe or redirection.

**Files:**

- pye.py: Source file with comments and code for PyBoard, WiPy and Linux micropython/python3. Runs on PyBoard as well, but the file size is much larger than the stripped down version.
- Pyboard Editor.pdf: A short documentation
- README.md: This one
- pe.py: Condensed source file for PyBoard with all functions
- pemin.py: Condensed source file with a reduced function set for PyBoard
- wipye.py: Condensed source file with a reduced function set for WiPy
- tuning_pye.py: A file with some improved replacements for functions of pye:
a) find_in_file() supporting regular expressions,
b) line_edit() supporting the cursor left/right/home/end keys, and
c) expandtabs() and packtabs() with a second argument for tabsize (not for pye, but maybe useful)
- strip.sh: sample Shell script which creates the different variants out of pye.py using cpp

**Short Version History**

**1.0** Initial release with all the basic functions

**1.1** Same function set, but simplified keyboard mapping. 
- Removed the duplicated definitions for cursor motion keys.
- Allowed both \r and \n for ENTER, and both \x08 and \x7f for BACKSPACE, which avoid some hazzle with terminal settings. 
- Removed auto-indent from the minimal version.

**1.2** Mouse support added, as well as some other minor changes.
- Simple Mouse support for scrolling and placing the cursor
- Flags setting for search case, autoindent on/off and statusline on/off
- GOTO line sets cursor to the middle row
- The function pye(..) returns a value now

**1.3** UNDO added. Added a multilevel UNDO (Ctrl-Z) for most functions that change the content. Other changes:
- Backspace at the first non-blank character mimics BackTab, if Auto-indent is enabled
- Added a REDRAW (Ctrl-E) function, which checks for the changed screen size after the window size has been changed.
- Added a line number column on the left side of the screen (can be turned off).
- Improved the scrolling speed, such that it lags less.
- Some code simplification and straightening, such that functions group better and a easier to understand.

**1.4** GET file added. Adding a function GET (Ctrl-O), which inserts the content of a file before the current line. Other changes:
- Both HOME and END stop at start of text is passing by on their way to their destination.
- Flag allowing to replace spaces by Tab when writing the file, complementary to what is done while reading. Tabsize is 8. A tab is inserted whenever possible, even if it replaces a single space character.
- Fixed a mild amnesia in UNDO

**1.5** WiPy Port and body shaping:
- Support for WiPy added. WiPy runs only the minimal version.
- Aligned function set of the minimal version, in order to comply with WiPy. Dropped Mouse support, GET file, Line number column, and write tabs; but included Tab, Backtab, the buffer functions Yank, Dup & ZAP and scrolling optimization.
- LEFT and RIGHT move to the adjacent line if needed
- When used with Linux **and** CPython, a terminal window resize cause redrawing the screen content. The REDRAW key (Ctrl-E) stays functional and is required for all other use cases, when the window size is changed. 
- HOME toggles again between start-of-line and start-of-text. END moves always to end-of-line
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

