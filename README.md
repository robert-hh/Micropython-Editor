#Pyboard-Editor

**Description**

A small text editor written in Python running on PYBoard, allowing to edit files locally. It is based on the editor widget of pfalcon at https://github.com/pfalcon/pyedit. I ported it to PyBoard and added a few functions:

- Use USB_VCP or UART for input and output.
- Changed the read keyboard function to comply with slow byte-by-byte input on serial lines.
- Added support for TAB, BACKTAB, SAVE, FIND, REPLACE, GOTO line, YANK (delete line into a buffer), DUP (copy line into a buffer), ZAP (insert buffer)
- Join Lines by 'Delete Char' at the end or Backspace at the beginning of a line, Auto-indent for ENTER, context sensitive TAB, BACKTAB and HOME
- Moved main into a function with some optional parameters
- Added an optional status line and single line prompts for QUIT, SAVE, FIND, REPLACE, GOTO, and Toggles. 
  The status line can be turned (almost) off for slow connections.
- Support of the basic mouse functions scrolling up/down and setting the cursor.

The editor assumes a VT100 terminal. It works in Insert mode. Cursor Keys, Home, End, PgUp, PgDn, Del and Backspace work as you would expect. The additional functions like FIND etc. are available with Ctrl-Keys. On reading files, tab characters are expanded to spaces with a tab size of 8, and trailing white space on a line will be discarded. It will not restored when the file is written.

The editor works also well in a Linux or MAC terminal environment, with both python3 and micropython.

**Files:**

- pye.py: Source file with comments and code for both PyBoard and Linux micropython/python3. Runs on PyBoard as well, but the file size is much larger than the stripped down version.
- Pyboard Editor.pdf: A short documentation
- README.md: This one
- pe.py: Editor Python file with all functions in a stripped down version for PyBoard only without comments
- pemin.py: Editor Python file with a reduced function set in a stripped down version for PyBoard only without comments
- tuning_pye.py: A file with some improved replacements for functions of pye: 
a) find_in_file() supporting regular expressions, 
b) line_edit() supporting cursor keys, and
c) expandtabs() with a second argument for tabsize (not for pye, but maybe useful)
- strip.sh: sample Shell script which creates the different variants out of pye.py using cpp

