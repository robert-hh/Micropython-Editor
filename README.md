# Micropython-Editor

**Description**

A small text editor written in Python running on PYBoard, WiPy and ESP8266 modules, allowing to edit files locally. It is based on the editor widget of pfalcon at https://github.com/pfalcon/pyedit. I ported it to PyBoard, WiPy and ESP8266 and added a few functions:

- Use USB_VCP/Telnet or UART (PybOard only) for input and output.
- Changed the read keyboard function to comply with slow byte-by-byte input on serial lines.
- Added support for Tab, BackTab, Save, Del and Backspace joining lines, Find, Replace, Goto Line, Undo, Get file, Auto-Indent, Set Flags, Copy/Delete & Paste, Indent, Un-Indent
- Handling tab (0x09) on reading & writing files,
- Added a status line, and single line prompts for Quit, Save, Find, Replace, Goto, Get file and Flag settings.
- Optional support of the basic mouse functions scrolling up/down and setting the cursor.

The editor assumes a VT100 terminal. It works in Insert mode. The following list
shows most of the commands. Commands marked with (opt) may not be supported in minimal versions:

|Key(s)|Function|
|:---|:---|
|Up Down Left Right| Cursor movement by one line or char|
|PgUp & PgDd|Page up/down|
|Home End|Goto the start or end of a line|
|Enter|Enter a line break at the cursor position. Autoindent is supported|
|Backspace|Delete char left to the  cursor (The key must be set to ASCII-Del)|
|Del|Delete the char under the cursor. If lines are marked, delete the marked area|
|Tab & Backtab|Insert or remove spaces up to the next tab position. If lines are marked, indent or unindent (opt)|
|Ctrl-O|Open a new file. If the file name is left empty, an empty buffer is opened|
|Ctrl-W|Toggle to the next file buffer|
|Ctrl-Q|Close a file buffer or end line-edit|
|Ctrl-S|Save to file|
|Ctrl-W|Switch to the next file buffer|
|Ctrl-F|Find|
|Ctrl-N|Repeat last find|
|Ctrl-H|Find and Replace (opt)|
|Ctrl-G|Go to a line|
|Ctrl-T|Go to the first line (opt)|
|Ctrl-B|Go to the last line (opt)|
|Ctrl-K|Goto the bracket matching the one under the cursor (opt)|
|Ctrl-L|Mark/Unmark the current line. The mark can then be extended by moving the cursor|
|Ctrl-X|Cut the marked lines (Alternative: Ctrl-Y)|
|Ctrl-C|Copy the marked lines (Alternative: Ctrl-D)|
|Ctrl-V|Insert the copied/cut lines|
|Ctrl-Z|Undo the last change(s)|
|Ctrl-A|Change settings for tab size, search case sensitivity, auto-indent and writing tabs (opt)|
|Ctrl-E|Redraw the screen. On WiPy and PyBord it shows the amoount of free memory|  

More details can be found in the doc file. On reading files, tab characters
are expanded to spaces with a tab size of 8, and trailing white space on a
line will be discarded. The orginal state of tabs will not be restored when
the file is written. Optionally, tabs can be written when saving the file, replacing
spaces with tabs when possible. The screen size is determined, when the editor is
started, when the Redraw-key (Ctrl-E) is hit or on any file window change (Ctrl-W).

The editor works also well in a Linux or MAC terminal environment (and also in some
terminal apps of Android - tested with Termux), with both python3 and micropython.
For that purpose, a small main() section is embedded, which when called with
CPython also accepts data from a pipe or redirection.

**Files:**

- pye.py: Source file with comments and code for PyBoard, WiPy and Linux micropython/python3. Runs on PyBoard as well, but the file size is much larger than the stripped down version.
- pye2.py: a variant of pye.py which does not change the cursor column during vertical moves.
- Pyboard Editor.pdf: A short documentation
- README.md: This one
- pe.py: Condensed source file for PyBoard with all functions
- pemin.py: Condensed source file with a reduced function set for PyBoard
- wipye.py: Condensed source file with a reduced function set for WiPy
- wipye.mpy: Precompiled version of pye.py for WiPy with all functions enabled. To be able to run it, you have to add:  

    `#define MICROPY_PERSISTENT_CODE_LOAD (1)`  

    to the file mpconfigport.h of the cc3200 branch, rebuild the binary it, and load it to WiPy.
- pesp8266.py: A version of for the esp8266 port. It requires frozen byte code
to be enabled, which available from version 1.8.1 on. In order to use it, you have to
put pesp8266 into the directory esp8266/modules and rebuild micropython.
A cross-compiled version may executed from the file system. You have to create a new build, adding:

     `#define MICROPY_PERSISTENT_CODE_LOAD (1)`  

     to mpconfigport.h and changing line 430 of py/emitglue.c into:  

    `#elif defined(__thumb2__) || defined(__xtensa__)`
- tuning_pye.py: A file with some improved replacements for functions of pye:
a) find_in_file() supporting regular expressions,
b) line_edit() supporting the cursor left/right/home/end keys, and
c) expandtabs() and packtabs() with a second argument for tabsize (not for pye, but maybe useful)
- strip.sh: sample Shell script which creates the different variants out of pye.py using cpp, including all variants of wipye.py with either speed up scrolling or support replace or support goto bracket or support indent/un-indent or support mouse.

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

**1.7a** Size reduction for WiPy & Tabbify for PyBoard
- Reduced KEYMAP in the WiPy version by omitting entries, where the function code is identical to the key value (e.g. \x08 -> 8). Not fool proof, but it helps reducing the size.
- Adding a "Tabbify" behaviour for the full version. Tab/Backtab with the cursor at col 1 indents/unindents the line and moves the cursor one line down.

**1.7b** Further size reduction for WiPy
- Moved setting of the change flag into the function add_undo()
- Removed skipping to the adjacent line with Right/Left in the WiPy Version
- Temporary avoidance of the memory leak when a file is not found

**1.7c** Re-establish try-except for file-not-found error
- Removed the temporary fix for memory corruption by exception for file-not-found error
- Changed string formatting to Python3 style

**1.8** Clean Copy & Paste, Indent, Un-Indent
- Added a Mark Line key forFixed a glitch, that allowed to paste text longer then the available space on the status line. No harm was done, just the screen content scrolled up. After leaving the line edit mode, a redraw fixed that. Line Delete, Line Copy, Indent and Un-Indent
- Changed Line Delete, Line Copy and Buffer Insert into a cleaner Copy & Paste mode
- Added a cleaner Indent and Un-Indent method; for WiPy too
- Removed the attempt to recover from out-of-memory situations: did not work.
- Still runs on WiPy, but really at it's limit

**1.9** Refinement of Mark and Undo
- Mark setting affects Save and Replace now. With Save, only the marked range is written, with replace, search & replace is done in the marked area only.
- The Undo history is kept after Save. So you can go back to a state before saving
- Removed UART mode on WiPy. Not stable yet. UART mode can be achieved by redirecting REPL.
- A variant of pye.py, called pye2.py, keeps the cursor column even if the cursor is moved beyond the text in a line, instead of moving to the end of text if a line is shorter than the actual cursor column. Another variant, pye3, tries to go back to the cursor column which once was set by a horizontal move. That's more how gedit works. Not sure which I like better.

**1.10** Further refinement of Mark
- When the mark is set, the whole area affected is now highlighted instead of just the line with the mark.
- Paste, Delete and Backspace now also take notice of the line Mark. You can Mark a line range and delete it (or cut it). Implicit deleting marked lines when pressing the Enter or character key was considered but rejected (easy - just 3 lines of code).
- Except for Delete, Backspace, Cut and Paste, Mark has to be toggled off when not needed any more.
- Right click (Button 2) or Ctrl-Click on the mouse sets/unsets the Mark, left Click extends it, when set.

**1.11** Minor fixes
- Change the way a marked area is highlighted from reverse to a different background color. That works well for black chars on yellow background (code 43). For white chars on black background, the setting for background color in the function hilite() has to be changed, e.g. to blue (code 44).
- Save to a temporary file first, and rename it to the target name when successfully written.
- Lazy screen update: defer screen update, until all chars from the keyboard are processed. Not provided for WiPY, even if needed there most. WiPy has no way to tell if more chars are waiting in the input or at least a read with timeout.

**1.12** Bracket Match and Minor changes
- Ctrl-K causes the cursor set to the matching bracket, if any. Pretty raw, not elegant.
Brackets in comments and strings are counting as well.
- On Copy the mark will be cleared, since it is assumed that the just copied lines will not be overwritten.
- High level try/except catching internal errors (mostly coding errors)
- Separate cpp options for including scroll optimization, replace or bracket match into the minimal version. Changes in strip.sh script to generate the minimal wipye version too.
- Some editorial changes and fixing of typos.

**1.12b** Fixing a inconsistency in the Save command
- Fixing a inconsistency in the Save command, which caused the change flag being reset when writing just a block
- Squeezing a few lines out of the source code

**1.12c** Speed up pasting again
- Speed up pasting again. Slowing down pasting was caused by a in-function import statement in V1.11.
- Squeezing another few lines out of the source code by combining two functions, which were
anyhow called one after the other, resulting in a enormous long function handling the keyboard input.

**1.12d** Split undo of Indent/Un-Indent
- Split undo for Indent and Un-Indent
- Fixed a minor inconvenience when going left at the line start (sqeezed too much in v1.12b)
- Move a few lines around, such that keys which are more likely used with fast repeats are checked for earlier.
- Some editorial changes

**2.0** Edit muliple files
- Support for editing mutiple files at once and copy/paste between them
- Ctrl-W steps through the list of files/buffers
- Ctrl-O opens a new file/buffer.

**2.1** Some shrinking for WiPy
- Make Indent/Un-Indent optional in the WiPy version, to allow all variants to get compiled w/o running out of memory.
The final code saving is just a few hundred bytes, so it's still not clear to me why these few extra lines dont't fit.
- Fixing a glitch which added an extra line when un-doing the delete of all lines
- Some shifting around of code lines
- Making the MOUSE support an extra option
- Removed the extra indent after ':' as the last char on the line. More confusing than helpful.
- Update of the doc file

**2.2** Further cleaning and some slight improvements
- Moved error catching one level up to the function pye(), catching load-file errors too.
- If open file names a directory, the list of files is loaded to the edit buffer.
- Ctrl-V in line edit mode inserts the first line of the paste buffer
- The WiPy version does not support undo for Indent/Un-indent, even if Indent is enabled. It is too memory consuming at runtime. It's questionable whether this is needed at all.
- And of course: update of the doc file

**2.3** Minor fixes & changes
- Catched file not found errors when starting pye, introduced in version 2.2
- Added a flag to pye2 such that it supports both vertical cursor movement types
- use uos.stat with micropython, since os.stat is not supported on linux-micropython
- When opening a directory, replace the name '.' by the result of os.getcwd(), avoiding error 22 on PyBoard and WiPy

**2.4** Fix for the regular expression search variant
- Fix a glitch, that the regular expression variant of search and replace did not find patterns anchored at the end, single line starts or single line endings. That fix required changes not only to the find function, such that all variants of pye are affected.
- Consider '.' **and** '..' in file open as directory names, avoiding stat() on these.

**2.5** Fix a small bug of edit_line()'s paste command
- Fixed a glitch, that allowed to paste text longer then the available space on the status line. No harm was done, just the screen content scrolled up. After leaving the line edit mode, a redraw fixed that.

**2.6** Adapted to change lib names in micropython
- For micropython replaced \_io with uio
- Preliminary esp8266 version.

**2.7** Change file save method and settings dialogue
- Further adaption to esp8266, which is now identical to the WiPy version
- Changed file save method, such that it works now across devices
- Made settings dialogue visible in basic mode, allowing to change both the
autoindent flag and the search case flag
- Create the ESP8266 version with all features but mouse support.
