import tkinter
from ex1 import URL, lex

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
        self.canvas.pack()
        self.scroll = 0
        self.window.bind("<Down>", self.scrolldown)

    def scrolldown(self, e):
        self.scroll += self.SCROLL_STEP
        self.canvas.delete("all")
        self.draw()

    def load(self, url: URL):
        res = url.request()
        text = lex(res["content"])

        self.display_list = self.layout(text)
        self.draw()

    def layout(self, text):
        display_list = []
        cursor_x, cursor_y = self.HSTEP, self.VSTEP
        for c in text:
            display_list.append((cursor_x, cursor_y, c))
            cursor_x += self.HSTEP
            if cursor_x >= self.WIDTH + self.HSTEP:
                cursor_x = self.HSTEP
                cursor_y += self.VSTEP
        return display_list
    
    def draw(self):
        for x, y, c in self.display_list:
            self.canvas.create_text(x, y - self.scroll, text=c)

if __name__ == "__main__":
    import sys
    Browser().load(URL(sys.argv[1]))
    tkinter.mainloop()