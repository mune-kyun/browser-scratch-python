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
        self.display_list = []
        self.bind_keys()

    def bind_keys(self):
        self.window.bind("<Down>", lambda e: self.scroll("<Down>"))
        self.window.bind("<Up>", lambda e: self.scroll("<Up>"))
        self.canvas.bind("<MouseWheel>", self.handle_mouse_wheel)

    def scroll(self, direction):
        if len(self.display_list) == 0:
            return
        
        if direction == "<Down>":
            char = self.display_list[len(self.display_list) - 1]
            _, y, _ = char
            
            if self.y_below_screen(y):
                self.scroll_val += SCROLL_STEP
            else:
                return
            
        elif direction == "<Up>":
            char = self.display_list[0]
            _, y, _ = char

            if self.y_above_screen(y):
                self.scroll_val -= SCROLL_STEP
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
        text = lex(res["content"])

        self.display_list = layout(text)
        self.draw()

    def y_above_screen(self, y):
        y_dest = y - self.scroll_val
        return y_dest < 0
    
    def y_below_screen(self, y):
        y_dest = y - self.scroll_val
        return y_dest > HEIGHT

    def draw(self):
        for x, y, c in self.display_list:
            y_dest = y - self.scroll_val
            if self.y_above_screen(y) or self.y_below_screen(y): continue
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