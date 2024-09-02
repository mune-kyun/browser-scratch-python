import tkinter
import tkinter.font
from ex1 import URL, lex, Tag, Text

FONTS = {}

def get_font(size, weight, style):
    key = (size, weight, style)
    if key not in FONTS:
        font = tkinter.font.Font(
            size=size,
            weight=weight,
            slant=style
        )
        FONTS[key] = font
    return FONTS[key]

class Layout:
    def __init__(self, tokens, hstep=13, vstep=18, height=600, width=800):
        self.display_list = []
        self.line = []

        self.hstep = hstep
        self.vstep = vstep
        self.cursor_x = hstep
        self.cursor_y = vstep
        self.width = width
        self.height = height

        self.weight = "normal"
        self.style = "roman"
        self.size = 12

        for tok in tokens:
            self.handleToken(tok)
        self.flush()

    def handleToken(self, tok):
        if isinstance(tok, Text):
            #TODO: this doesnt handle \n
            for word in tok.text.split():
                self.handleWord(word)
        
        elif isinstance(tok, Tag):
            tag = tok.tag
            if tag == "i":
                self.style = "italic"
            elif tag == "/i":
                self.style = "roman"
            elif tag == "b":
                self.weight = "bold"
            elif tag == "/b":
                self.weight = "normal"
            elif tag == "small":
                self.size -= 2
            elif tag == "/small":
                self.size += 2
            elif tag == "big":
                self.size += 4
            elif tag == "/big":
                self.size -= 4

    def handleWord(self, word):
        font = get_font(self.size, self.weight, self.style)
        word_width = font.measure(word)
        if self.cursor_x + word_width > self.width - self.hstep:
            self.flush()
        self.line.append((self.cursor_x, word, font))
        
        self.cursor_x += word_width + font.measure(" ")
        #TODO: needs to be tested since parsing \n doesnt work
        if "\n" in word:
            self.flush()

    def flush(self):
        if not self.line: return
        metrics = [font.metrics() for x, word, font in self.line]
        max_ascent = max([metric["ascent"] for metric in metrics])
        max_descent = max([metric["descent"] for metric in metrics])
        baseline = self.cursor_y + 1.25 * max_ascent

        for x, word, font in self.line:
            y = baseline - font.metrics("ascent")
            self.display_list.append((x, y, word, font))

        self.cursor_x = self.hstep
        self.cursor_y += baseline + 1.25 * max_descent
        self.line = []

class Browser:
    HEIGHT, WIDTH = 600, 800
    HSTEP, VSTEP = 13, 18
    SCROLL_STEP = 100
    
    def __init__(self):
        self.display_list = []
        self.hstep = self.HSTEP
        self.vstep = self.VSTEP
        self.width = self.WIDTH
        self.height = self.HEIGHT
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(
            self.window,
            width=self.width,
            height=self.height
        )
        self.canvas.pack(
            fill=tkinter.BOTH,
            expand=1
        )
        self.scroll_val = 0
        self.bind_keys()

    def bind_keys(self):
        self.window.bind("<Down>", lambda e: self.scroll("<Down>"))
        self.window.bind("<Up>", lambda e: self.scroll("<Up>"))
        self.window.bind("<Configure>", lambda e: self.handle_configure(e))
        self.canvas.bind("<MouseWheel>", self.handle_mouse_wheel)

    def handle_configure(self, e):
        width, height = e.width, e.height
        if abs(self.width - width) > 9 or abs(self.height - height) > 9:
            self.width = width
            self.height = height
            #TODO: handle this pls
            self.display_list = Layout(
                tokens=self.tokens,
                hstep=self.hstep,
                vstep=self.vstep,
                height=self.height,
                width=self.width
            ).display_list
            self.canvas.delete("all")
            self.draw()

    def scroll(self, direction):
        display_list = self.display_list
        if len(display_list) == 0:
            return
        
        if direction == "<Down>":
            char = display_list[len(display_list) - 1]
            _, y, _, _ = char
            
            if self.y_below_screen(y):
                self.scroll_val += self.SCROLL_STEP
            else:
                return
            
        elif direction == "<Up>":
            char = display_list[0]
            _, y, _, _ = char

            if self.y_above_screen(y):
                self.scroll_val -= self.SCROLL_STEP
            else:
                return

        self.canvas.delete("all")
        self.draw()

    def handle_mouse_wheel(self, e):
        if e.delta < 0:
            self.scroll("<Down>")
        elif e.delta > 0:
            self.scroll("<Up>")

    def load(self, url: URL):
        res = url.request()
        self.tokens = lex(res)
        #TODO: refactor havent handle view source
        self.display_list = Layout(
            tokens=self.tokens,
            hstep=self.hstep,
            vstep=self.vstep,
            height=self.height,
            width=self.width
        ).display_list
        self.draw()

    def y_above_screen(self, y):
        y_dest = y - self.scroll_val
        return y_dest < 0
    
    def y_below_screen(self, y):
        y_dest = y - self.scroll_val
        return y_dest > self.height

    def draw(self):
        display_list = self.display_list
        for x, y, word, font in display_list:
            if self.y_above_screen(y) or self.y_below_screen(y): continue
            y_dest = y - self.scroll_val
            self.canvas.create_text(x, y_dest, text=word, font=font, anchor="nw")

if __name__ == "__main__":
    import sys
    Browser().load(URL(sys.argv[1]))
    tkinter.mainloop()