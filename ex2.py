import tkinter
import tkinter.font
from ex1 import URL, lex, Tag, Text

class Browser:
    HEIGHT, WIDTH = 600, 800
    HSTEP, VSTEP = 13, 18
    SCROLL_STEP = 100
    
    def __init__(self):
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(
            self.window,
            width=self.WIDTH,
            height=self.HEIGHT
        )
        self.canvas.pack(
            fill=tkinter.BOTH,
            expand=1
        )
        self.scroll_val = 0
        self.font = tkinter.font.Font(
            family="Times",
            size=16,
            weight="bold",
            slant="italic",
        )
        self.display_list = []
        self.bind_keys()

    def bind_keys(self):
        self.window.bind("<Down>", lambda e: self.scroll("<Down>"))
        self.window.bind("<Up>", lambda e: self.scroll("<Up>"))
        self.window.bind("<Configure>", lambda e: self.handle_configure(e))
        self.canvas.bind("<MouseWheel>", self.handle_mouse_wheel)

    def handle_configure(self, e):
        width, height = e.width, e.height
        if abs(self.WIDTH - width) > 9 or abs(self.HEIGHT - height) > 9:
            self.WIDTH = width
            self.HEIGHT = height
            self.display_list = self.layout(self.tokens)
            self.canvas.delete("all")
            self.draw()

    def scroll(self, direction):
        if len(self.display_list) == 0:
            return
        
        if direction == "<Down>":
            char = self.display_list[len(self.display_list) - 1]
            _, y, _ = char
            
            if self.y_below_screen(y):
                self.scroll_val += self.SCROLL_STEP
            else:
                return
            
        elif direction == "<Up>":
            char = self.display_list[0]
            _, y, _ = char

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
        self.display_list = self.layout(self.tokens)
        self.draw()

    def y_above_screen(self, y):
        y_dest = y - self.scroll_val
        return y_dest < 0
    
    def y_below_screen(self, y):
        y_dest = y - self.scroll_val
        return y_dest > self.HEIGHT

    def draw(self):
        for x, y, word, font in self.display_list:
            y_dest = y - self.scroll_val
            if self.y_above_screen(y) or self.y_below_screen(y): continue
            self.canvas.create_text(x, y_dest, text=word, font=font, anchor="nw")

    def layout(self, tokens):
        style = "roman"
        weight = "normal"
        display_list = []
        cursor_x, cursor_y = self.HSTEP, self.VSTEP
        for tok in tokens:
            if isinstance(tok, Text):
                for word in tok.text.split():
                    font = tkinter.font.Font(
                        size=16,
                        weight=weight,
                        slant=style
                    )
                    word_width = self.font.measure(word)
                    if cursor_x + word_width > self.WIDTH - self.HSTEP:
                        cursor_x = self.HSTEP
                        cursor_y += self.font.metrics("linespace") * 1.25
                    display_list.append((cursor_x, cursor_y, word, font))
                    
                    cursor_x += word_width + self.font.measure(" ")
                    if "\n" in word:
                        cursor_x = self.HSTEP
                        cursor_y += self.font.metrics("linespace") * 1.25
            
            elif isinstance(tok, Tag):
                tag = tok.tag
                if tag == "i":
                    style = "italic"
                elif tok.tag == "/i":
                    style = "roman"
                elif tok.tag == "b":
                    weight = "bold"
                elif tok.tag == "/b":
                    weight = "normal"

        return display_list

if __name__ == "__main__":
    import sys
    Browser().load(URL(sys.argv[1]))
    tkinter.mainloop()