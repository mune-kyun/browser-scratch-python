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

# In short, it wraps node to layout to be better
class BlockLayout:
    def __init__(self, node, parent, previous):
        self.display_list = []

        self.hstep = HSTEP
        self.vstep = VSTEP
        self.x = None   # Absolute in the screen, starting x
        self.y = None   # Absolute in the screen, starting y
        self.width = None
        self.height = None

        self.weight = "normal"
        self.style = "roman"
        self.size = 12

        # HTML tree. After BlockLayout exist, now the children won't matter except for building the layout tree
        self.node = node
        self.parent = parent
        self.previous = previous
        self.children = []  # Layout tree
    
    '''
    - Create layout tree
    - Now each html element has it's own layout (previously it's the tree is in a single layout)
    - Per-BlockLayout has it's own smaller display_list tree
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
    Btw the self.open_tag/close_tag work since class recursive is not creating a new instance.
    Note: this traverse HTML tree
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

    '''
    From existing display_list, convert to DrawText/DrawRect
    '''
    def paint(self):
        cmds = []
        
        if isinstance(self.node, Element) and self.node.tag == "pre":
            x2, y2 = self.x + self.width, self.y + self.height
            cmds.append(DrawRect(self.x, self.y, x2, y2, "gray"))
        
        if self.layout_mode() == "inline":
            for x, y, word, font in self.display_list:
                cmds.append(DrawText(x, y, word, font))

        return cmds

class DrawText():
    def __init__(self, x1, y1, text, font):
        self.top = y1
        self.left = x1
        self.text = text
        self.font = font
        self.bottom = y1 + font.metrics("linespace")

    def execute(self, scroll, canvas):
        canvas.create_text(
            self.left,
            self.top - scroll,
            text=self.text,
            font=self.font,
            anchor='nw'
        )

class DrawRect():
    def __init__(self, x1, y1, x2, y2, color):
        self.top = y1
        self.left = x1
        self.bottom = y2
        self.right = x2
        self.color = color
    
    def execute(self, scroll, canvas):
        canvas.create_rectangle(
            self.left,
            self.top - scroll,
            self.right,
            self.bottom - scroll,
            width=0,
            fill=self.color
        )

'''
Note: Traversing layout tree
Convert display_list to DrawText/DrawRect
Return the result to the passed display_list
'''
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

        # Handle resize window
        if abs(self.width - width) > 1 or abs(self.height - height) > 1:
            self.width = width
            self.height = height
            # TODO: Handle reposition text
            self.canvas.delete("all")
            self.draw()

    def scroll(self, direction):
        display_list = self.display_list
        if len(display_list) == 0:
            return
        
        if direction == "<Down>":
            # Max_y is self.document.height
            # - by HEIGHT since that much content is already shown initially
            # + 2*VSTEP whitespace top/bottom page
            max_y = max(self.document.height + 2*VSTEP - HEIGHT, 0)
            
            # Guard when scrolling beyond the whole content height
            self.scroll_val = min(self.scroll_val + SCROLL_STEP, max_y)
            
        elif direction == "<Up>":
            self.scroll_val = max(self.scroll_val - SCROLL_STEP, 0)

        self.draw()

    def handle_mouse_wheel(self, e):
        if e.delta < 0:
            self.scroll("<Down>")
        elif e.delta > 0:
            self.scroll("<Up>")

    def load(self, url: URL):
        res = url.request()
        self.nodes = HTMLParser(res["content"]).parse()
        
        self.document = DocumentLayout(self.nodes)
        self.document.layout()
        paint_tree(self.document, self.display_list)
        self.draw()

    def draw(self):
        self.canvas.delete("all")
        for cmd in self.display_list:
            # Skip if above the screen (cuz if the bottom is above then is out of screen)
            # Cuz scroll_val keeps increasing when scroll down
            if cmd.bottom < self.scroll_val: continue
            
            # Skip if below the screen
            # Equivalent with y - scroll_val > height
            # On init, y/cmd.top that is below the screen is > 800
            if cmd.top > self.scroll_val + HEIGHT: continue

            cmd.execute(self.scroll_val, self.canvas)

if __name__ == "__main__":
    import sys
    Browser().load(URL(sys.argv[1]))
    tkinter.mainloop()