##
## This is the regex version of find.
    def find_in_file(self, pattern, col, end):
        import re
#define REGEXP 1
        Editor.find_pattern = pattern ## remember it
        if Editor.case != "y":
            pattern = pattern.lower()
        try:
            rex = re.compile(pattern)
        except:
            self.message = "Invalid pattern: " + pattern
            return -1
        scol = col
        for line in range(self.cur_line, end):
            l = self.content[line]
            if Editor.case != "y":
                l = l.lower()
## since micropython does not support span, a step-by_step match has to be performed
            ecol = 1 if pattern[0] == '^' else len(l) + 1 
            for i in range(scol, ecol):
                match = rex.match(l[i:])
                if match: ## bingo!
                    self.col = i
                    self.cur_line = line
                    return len(match.group(0))
            scol = 0
        else:
            self.message = pattern + " not found"
            return -1

    def line_edit(self, prompt, default):  ## better one: added cursor keys and backsp, delete
        push_msg = lambda msg: self.wr(msg + "\b" * len(msg)) ## Write a message and move cursor back
        self.goto(Editor.height, 0)
        self.hilite(True)
        self.wr(prompt)
        self.wr(default)
        self.clear_to_eol()
        res = default
        self.message = ' ' # Shows status after lineedit
        pos = len(res)
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
            elif key == KEY_DELETE: ## Delete
                if pos < len(res):
                    res = res[:pos] + res[pos+1:]
                    push_msg(res[pos:] + ' ') ## update tail
            elif key == KEY_BACKSPACE: ## Backspace
                if pos > 0:
                    res = res[:pos-1] + res[pos:]
                    self.wr("\b")
                    pos -= 1
                    push_msg(res[pos:] + ' ') ## update tail
            elif key == KEY_ZAP: ## Get from content
                if Editor.yank_buffer:
                    self.wr('\b' * pos + ' ' * len(res) + '\b' * len(res))
                    res = Editor.yank_buffer[0].strip()
                    self.wr(res)
                    pos = len(res)
            elif 0x20 <= key < 0xfff0: ## char to be inserted
                if len(prompt) + len(res) < self.width - 2:
                    res = res[:pos] + chr(key) + res[pos:]
                    self.wr(res[pos])
                    pos += 1
                    push_msg(res[pos:]) ## update tail

    def line_edit(self, prompt, default):  ## simple one: only 4 fcts
        self.goto(Editor.height, 0)
        self.hilite(1)
        self.wr(prompt)
        self.wr(default)
        self.clear_to_eol()
        res = default
        while True:
            key = self.get_input()  ## Get Char of Fct.
            if key in (KEY_ENTER, KEY_TAB): ## Finis
                self.hilite(0)
                return res
            elif key == KEY_QUIT: ## Abort
                self.hilite(0)
                return None
            elif key == KEY_BACKSPACE: ## Backspace
                if (len(res) > 0):
                    res = res[:len(res)-1]
                    self.wr('\b \b')
            elif key == KEY_DELETE: ## Delete prev. Entry
                self.wr('\b \b' * len(res))
                res = ''
            elif key >= 0x20: ## char to be added at the end
                if len(prompt) + len(res) < self.width - 2:
                    res += chr(key)
                    self.wr(chr(key))

    def expandtabs(self, s, tabsize = 8):
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

    def packtabs(self, s, tabsize = 8):
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

    def cls(self):
        self.wr(b"\x1b[2J")




