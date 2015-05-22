# Pyboard-Editor
Onboard Text Editor for Pyboard

A small text editor written in Python running on PYBoard, allwoing to edit files locally. It is based on the editor widget of pfalcon at https://github.com/pfalcon/pyedit. Ported to PyBoard and added a few functions:

- Use USB_VCP or UART for input and output.
- Changed the read keyboard function to comply with slow char-by-char input on serial lines.
- Added support for TAB, BACKTAB, SAVE, Find, Goto Line, Yank (delete line into buffer), Zap (insert buffer)
- Join Lines by Delete char at the end, Autoindent for Enter
- Moved main into a function with some optional parameters
- Added an optional status line and single line prompts for Quit, Save, Find and Goto. The status line can be turned (almost) off for slow connections.

Th editor assumes a VT100 terminal. The editor works in Insert mode. Cursor Keys, Home, End, PgUp, PgDn, Del and Backspace work as you would expect. Most functions are available with Ctrl-Keys too, if a VT100 keyboard mapping is not available. 
----
Files:
Pyboard Editor.pdf: A short documentation
README.md: This one
pe.py: Editor Python file with all fucntions in a stripped down version for PyBoard only without comments
pemin.py: Editor Python file wit a reduced fucntion set in a stripped down version for PyBoard only without comments
pye.hlp: Help file for online help
pye.py: Source file with comments and code for both PyBoard and Linux micropython/python3. Runs on PyBoard as well, but the file size is much larger.
