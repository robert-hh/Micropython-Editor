#Pyboard-Editor

**Description**

A small text editor written in Python running on PYBoard, allowing to edit files locally. It is based on the editor widget of pfalcon at https://github.com/pfalcon/pyedit. I ported it to PyBoard and added a few functions:

- Use USB_VCP or UART for input and output.
- Changed the read keyboard function to comply with slow byte-by-byte input on serial lines.
- Added support for TAB, BACKTAB, SAVE, FIND, REPLACE, GOTO line, YANK (delete line into a buffer), ZAP (insert buffer)
- Join Lines by 'Delete Char' at the end or Backspace at the beginning of a line, Auto-indent for ENTER, context sensitive TAB, BACKTAB and HOME
- Moved main into a function with some optional parameters
- Added an optional status line and single line prompts for QUIT, SAVE, FIND, REPLACE, and GOTO. 
  The status line can be turned (almost) off for slow connections.

The editor assumes a VT100 terminal. It works in Insert mode. Cursor Keys, Home, End, PgUp, PgDn, Del and Backspace work as you would expect. Most functions are available with Ctrl-Keys too, if a VT100 keyboard mapping is not available. On reading files, tab characters are expanded to spaces with a tab size of 8, and trailing white space on a line will be discarded. It will not restored when the file is written.

The editor works also well in a Linux environment, with both python3 and micropython.

**Files:**

- Pyboard Editor.pdf: A short documentation
- README.md: This one
- pe.py: Editor Python file with all functions in a stripped down version for PyBoard only without comments
- pemin.py: Editor Python file with a reduced function set in a stripped down version for PyBoard only without comments
- pye.py: Source file with comments and code for both PyBoard and Linux micropython/python3. Runs on PyBoard as well, but the file size is much larger than the stripped down version.
- strip.sh: sample Shell script which creates the different variants out of pye.py using cpp

