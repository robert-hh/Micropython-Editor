  ^ is control or esc                         | This file 'h' is 99 characters wide.   ----------->
Go to first line    ^[home]                   |
Go to top of file   ^t                        | ^open file  ^w next window     [esc]save    ^quit
Scroll up           ^[up]                     | ^find    ^next  ^r find & replace
                                              | Undo  ^z  Redo ^y
Move current line           alt-up alt-down   | ^e redraw   
Move character under cursor  alt<- / alt->    | 
                                              | Selection start / end           ^L
Move to:                                      |
before/after word   ^<- / ^->                 | Select text                      shift-arrow
start-of-text and the start of line  [home]   |       Moving cursor selects more.
end-of-the-text and end-of-line      [end]    | Move selection up/down            alt-up / alt-down
                                              | Delete selected                  [delete]
Go to line #   ^g   Matching ()[] {} <>   ^k  | Copy / Cut selected to clipboard ^c / ^x   
                                              | Paste clipboard                  ^v
Insert a line break        [enter]            | 
character under cursor left/right ^<- / ^->   | Comment toggle i.e. add/remove #  ^p
                                              | Change pye attributes ^a
Delete:                                       |   (indent, ^f case, tab size,
Char left of the cursor [backspace]           |    comment string, write tabs)
Char under the cursor   [delete]
Word under the cursor  ^[delete] 
Space up to the next non-space ^[delete]
line              Shift-[delete]

Merge with previous line           [backspace] if at the beginning of a line
Merge with next line if at end of line, 
     with autoindent delete leading spaces of the joined line.  [backspace]
Clear the entry in line edit mode,  [delete] as first keystroke will clear the entry.

Scroll the window down         ^[down]  
Go to Bottom                   ^b
Go to last line                ^[end]                   v.82   phor pye v2.72
___________________________________________
      Mac keyboard: 
Move to:
before/after word                   ^cmd-left/right arrow 
start-of-text and the start of line fn-left
end-of-the-text and end-of-line     fn-right 
scroll up/down                      fn-arrow-up/down

Simple usage: transfer this file ( h ) to the target filesystem to the same directory
    as the file being edited.
To view it ^oh. To switch back to the file being edited window ^w . Back to help ^w and so on.
Edit this file ( h ), with pye to customize it.
