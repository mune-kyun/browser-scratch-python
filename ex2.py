import tkinter
from ex1 import URL, lex

HEIGHT, WIDTH = 600, 800
HSTEP, VSTEP = 13, 18
SCROLL_STEP = 100
class Browser:
    def __init__(self):
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(
            self.window,
            width=WIDTH,
            height=HEIGHT
        )
        self.canvas.pack()
        self.scroll_val = 0
        self.bind_keys()

    def bind_keys(self):
        self.window.bind("<Down>", lambda e: self.scroll("<Down>"))
        self.window.bind("<Up>", lambda e: self.scroll("<Up>"))

    def scroll(self, direction):
        if direction == "<Down>":
            self.scroll_val += SCROLL_STEP
        elif direction == "<Up>":
            self.scroll_val -= SCROLL_STEP
        self.canvas.delete("all")
        self.draw()

    def load(self, url: URL):
        res = url.request()
        text = lex(res["content"])

        self.display_list = layout(text)
        self.draw()

    def draw(self):
        for x, y, c in self.display_list:
            y_dest = y - self.scroll_val
            if y_dest < 0 or y_dest > HEIGHT: continue
            self.canvas.create_text(x, y_dest, text=c)

def layout(text):
    display_list = []
    cursor_x, cursor_y = HSTEP, VSTEP
    for c in text:
        display_list.append((cursor_x, cursor_y, c))
        cursor_x += HSTEP

        if "\n" in c:
            cursor_x = HSTEP
            cursor_y += 1.2*VSTEP
        
        if cursor_x >= WIDTH + HSTEP:
            cursor_x = HSTEP
            cursor_y += VSTEP

    return display_list

if __name__ == "__main__":
    import sys
    Browser().load(URL(sys.argv[1]))
    tkinter.mainloop()