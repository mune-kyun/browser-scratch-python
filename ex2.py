import tkinter
import tkinter.font
from ex1 import URL, lex, Element, Text, HTMLParser

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

BLOCK_ELEMENTS = [
    "html", "body", "article", "section", "nav", "aside",
    "h1", "h2", "h3", "h4", "h5", "h6", "hgroup", "header",
    "footer", "address", "p", "hr", "pre", "blockquote",
    "ol", "ul", "menu", "li", "dl", "dt", "dd", "figure",
    "figcaption", "main", "div", "table", "form", "fieldset",
    "legend", "details", "summary"
]

HEIGHT, WIDTH = 600, 800
HSTEP, VSTEP = 13, 18
SCROLL_STEP = 100

class DocumentLayout:
    def __init__(self, node):
        self.node = node    # HTML tree
        self.parent = None
        self.children = []  # Store layout tree

        self.x = None   # Start position x
        self.y = None   # Start position y
        self.width = None
        self.height = None

    def layout(self):
        self.width = WIDTH - 2*HSTEP
        self.x = HSTEP
        self.y = VSTEP

        '''
        - Make the node child as blocklayout
        - then recursive to do the same for the child
        '''
        child = BlockLayout(self.node, self, None)
        self.children.append(child)
        child.layout()

        '''
        Always count height at the end after recursive since total height can only be calculated 
        after knowing the child height (kinda like height: fit-content)
        '''
        self.height = child.height

    def paint(self):
        return []

class BlockLayout:
    def __init__(self, node, parent, previous):
        self.display_list = []

        self.hstep = HSTEP
        self.vstep = VSTEP
        self.x = None
        self.y = None
        self.width = None
        self.height = None

        self.weight = "normal"
        self.style = "roman"
        self.size = 12

        self.node = node    # HTML tree
        self.parent = parent
        self.previous = previous
        self.children = []  # Layout tree
    
    '''
    - Create layout tree
    - Also creating HTML tree per leaf, so now each leaf contain sub tree of the whole HTML tree
    - So, now per-BlockLayout has it's own smaller tree
    '''
    def layout(self):
        # Set x starting point and width to parent
        self.x = self.parent.x
        self.width = self.parent.width

        # Set y starting point taking account siblings height or parent's height
        if self.previous:
            self.y = self.previous.y + self.previous.height
        else:
            self.y = self.parent.y

        mode = self.layout_mode()
        
        if mode == "block":
            previous = None

            for child in self.node.children:
                next = BlockLayout(child, self, previous)
                self.children.append(next)
                previous = next
        else: # Leaf node in layout tree
            self.cursor_x = 0
            self.cursor_y = 0
            self.weight = "normal"
            self.style = "roman"
            self.size = 12
            
            '''
            Since it's leaf node, then we can generate the x, y, word, font to be added to display_list
            '''
            self.line = []
            self.recurse(self.node)
            self.flush()

        # For each children recursively do the same
        for child in self.children:
            child.layout()
        
        # Like the root layout, can calculate height after the child height is calculated
        if mode == "block":
            self.height = sum([child.height for child in self.children])
        else:
            self.height = self.cursor_y

    def layout_intermediate(self):
        previous = None
        for child in self.node.children:
            next = BlockLayout(child, self, previous)
            self.children.append(next)
            previous = next

    # Determine whether a node is a block or inline
    def layout_mode(self):
        if isinstance(self.node, Text):
            return "inline"
        elif any([isinstance(child, Element) and \
                  child.tag in BLOCK_ELEMENTS
                  for child in self.node.children]):
            return "block"
        elif self.node.children:
            return "inline"
        else:
            return "block"

    # This method is obsolete since we already use html tree
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
            elif tag == "br" or tag == "br/":
                self.flush()
            elif tag == "/p":
                self.flush()
                self.cursor_y += self.vstep

    # Determine coordinate of word
    def handleWord(self, word):
        font = get_font(self.size, self.weight, self.style)
        word_width = font.measure(word)
        if self.cursor_x + word_width > self.width:
            self.flush()
        self.line.append((self.cursor_x, word, font))
        
        self.cursor_x += word_width + font.measure(" ")
        #TODO: needs to be tested since parsing \n doesnt work
        if "\n" in word:
            pass

    '''
    1. Flush [array]line
    2. Append the line to [array]display_list
    3. Determine max_ascent, max_descent, and baseline for every word position
    '''
    def flush(self):
        if not self.line: return
        metrics = [font.metrics() for x, word, font in self.line]
        max_ascent = max([metric["ascent"] for metric in metrics])
        max_descent = max([metric["descent"] for metric in metrics])
        baseline = self.cursor_y + 1.25 * max_ascent

        for rel_x, word, font in self.line:
            x = self.x + rel_x
            y = self.y + baseline - font.metrics("ascent")
            self.display_list.append((x, y, word, font))

        # Reset cursor_x, move cursor_y at the end of flush
        self.cursor_x = 0
        self.cursor_y = baseline + 1.25 * max_descent
        self.line = []

    # Change style
    def open_tag(self, tag):
        if tag == "i":
            self.style = "italic"
        elif tag == "b":
            self.weight = "bold"
        elif tag == "small":
            self.size -= 2
        elif tag == "big":
            self.size += 4
        elif tag == "br":
            self.flush()
    
    # Revert style
    def close_tag(self, tag):
        if tag == "i":
            self.style = "roman"
        elif tag == "b":
            self.weight = "normal"
        elif tag == "small":
            self.size += 2
        elif tag == "big":
            self.size -= 4
        elif tag == "p":
            self.flush()
            self.cursor_y += self.vstep

    '''
    Recursively convert (calling handleWord and flush) to x, y, font, blabla.
    Btw the self.open_tag/close_tag work since class recursive is not creating a new instance
    '''
    def recurse(self, node):
        if isinstance(node, Text):
            for word in node.text.split():
                self.handleWord(word)

        else:
            self.open_tag(node.tag)
            for child in node.children:
                self.recurse(child)
            self.close_tag(node.tag)

    def paint(self):
        return self.display_list

def paint_tree(layout_object, display_list):
    display_list.extend(layout_object.paint())

    for child in layout_object.children:
        paint_tree(child, display_list)

class Browser:
    def __init__(self):
        self.display_list = []
        self.hstep = HSTEP
        self.vstep = VSTEP
        self.width = WIDTH
        self.height = HEIGHT
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
        if abs(self.width - width) > 1 or abs(self.height - height) > 1:
            self.width = width
            self.height = height
            # self.display_list = Layout(
            #     hstep=self.hstep,
            #     vstep=self.vstep,
            #     height=self.height,
            #     width=self.width,
            #     nodes=self.nodes
            # ).display_list
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
                self.scroll_val += SCROLL_STEP
            else:
                return
            
        elif direction == "<Up>":
            char = display_list[0]
            _, y, _, _ = char

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
        self.nodes = HTMLParser(res["content"]).parse()
        
        #TODO: refactor havent handle view source
        self.document = DocumentLayout(self.nodes)
        self.document.layout()
        paint_tree(self.document, self.display_list)
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