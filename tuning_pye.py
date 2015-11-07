##
## This is the regex version of find.
    def find_in_file(self, pattern, pos):
        import re
        self.find_pattern = pattern ## remember it
        if self.case != "y":
            pattern = pattern.lower()
        try:
            rex = re.compile(pattern)
        except:
            self.message = "Invalid pattern: " + pattern
            return False
        spos = pos
        for line in range(self.cur_line, self.total_lines):
            if self.case != "y":
                match = rex.search(self.content[line][spos:].lower())
            else:
                match = rex.search(self.content[line][spos:])
            if match:
                break
            spos = 0
        else:
            self.message = pattern + " not found"
            return 0
## micropython does not support span(), therefore a second simple find on the target line
        if self.case != "y":
            self.col = max(self.content[line][spos:].lower().find(match.group(0)), 0) + spos
        else:
            self.col = max(self.content[line][spos:].find(match.group(0)), 0) + spos
        self.cur_line = line
        self.message = ' ' ## force status once
        return len(match.group(0))

    @staticmethod
    def push_msg(msg): ## Write a message and place cursor back
        Editor.wr("\x1b[s")  ## Push cursor
        Editor.wr(msg)
        Editor.wr("\x1b[u")  ## Pop Cursor

    def line_edit(self, prompt, default):  ## better one: added cursor keys and backsp, delete
        self.goto(self.height, 0)
        self.hilite(True)
        self.wr(prompt)
        self.clear_to_eol()
        res = default
        self.message = ' ' # Shows status after lineedit
        pos = 0
        self.push_msg(res)
        while True:
            key = self.get_input()  ## Get Char of Fct.
            if key in (KEY_ENTER, KEY_TAB): ## Finis
                self.hilite(False)
                return res
            elif key == KEY_QUIT: ## Abort
                self.hilite(False)
                return None
            elif key == KEY_LEFT:
                if pos > 0:
                    self.wr("\b")
                    pos -= 1
            elif key == KEY_RIGHT:
                if pos < len(res):
                    self.wr(res[pos])
                    pos += 1
            elif key == KEY_HOME:
                self.wr("\b" * pos)
                pos = 0
            elif key == KEY_END:
                self.wr(res[pos:])
                pos = len(res)
            elif key == KEY_BACKSPACE: ## Backspace
                if pos > 0:
                    res = res[:pos-1] + res[pos:]
                    self.wr("\b")
                    pos -= 1
                    self.push_msg(res[pos:] + ' ') ## Push + pop cursor
            elif key == KEY_DELETE: ## Delete
                if pos < len(res):
                    res = res[:pos] + res[pos+1:]
                    self.push_msg(res[pos:] + ' ') ## Push + pop cursor
            else: ## char to be inserted
                if len(prompt) + len(res) < self.width - 2:
                    res = res[:pos] + chr(key) + res[pos:]
                    self.wr(res[pos])
                    pos += 1
                    self.push_msg(res[pos:]) ## Push + pop cursor


    @staticmethod
    def expandtabs(s, tabsize = 8):
        import _io
        if '\t' in s and tabsize > 0:
            sb = _io.StringIO()
            pos = 0
            for c in s:
                if c == '\t': ## tab is seen
                    sb.write(" " * (tabsize - pos % tabsize)) ## replace by space
                    pos += tabsize - pos % tabsize
                else:
                    sb.write(c)
                    pos += 1
            return sb.getvalue()
        else:
            return s

    @staticmethod
    def packtabs(s, tabsize = 8):
        if tabsize > 0:
            sb = _io.StringIO()
            for i in range(0, len(s), tabsize):
                c = s[i:i + tabsize]
                cr = c.rstrip(" ")
                if c != cr: ## Spaces at the end of a section
                    sb.write(cr + "\t") ## replace by tab
                else:
                    sb.write(c)
            return sb.getvalue()
        else:
            return s

    @staticmethod
    def cls():
        Editor.wr(b"\x1b[2J")
#
# This is a safe place for the initial get_file function, which is replaced by another one
# until the MiPy error about stalling about non-existing files is solved
#
    def get_file(self, fname):
        try:
#ifdef LINUX
            if sys.implementation.name == "cpython":
                with open(fname, errors="ignore") as f:
                    content = f.readlines()
            else:
#endif
                with open(fname) as f:
                    content = f.readlines()
        except Exception as err:
            message = 'Could not load {}, {!r}'.format(fname, err)
            return (None, message)
        for i in range(len(content)):  ## strip and convert
            content[i] = self.expandtabs(content[i].rstrip('\r\n\t '))
        return (content, "")



