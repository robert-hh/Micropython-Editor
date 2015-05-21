# Pyboard-Editor
Onboard Text Editor for Pyboard

A small text editor written in Python running on PYBoard, allwoing to edit files locally. It is based on the editor widget og pfalcon at https://github.com/pfalcon/pyedit. I've ported that to PyBoard and added a few functions:
- Use USB_VCP or UART for input and output.
- Changed the read keyboard function to comply with slow char-by-char input on serial lines.
- Added support for TAB, BACKTAB, SAVE, Find, Goto Line, Yank (delete line into buffer), Zap (insert buffer)
- Join Lines by Delete char at the end, Autoindent for Enter
- Moved main into a function with some optional parameters
- Added an optional status line and single line prompts for Quit, Save, Find and Goto. The status line can be turned (almost) off for slow connections.
The editor works in Insert mode. Cursor Keys, Home, End, PgUp and PgDn work as you would expect. Most functions are available with Ctrl-Keys too, if a keyboard mapping is not available. 
----

