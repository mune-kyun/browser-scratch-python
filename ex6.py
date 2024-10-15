from ex1 import Element

class CSSParser:
    def __init__(self, s):
        self.s = s
        self.i = 0

    # Move index till no whitespace left
    def whitespace(self):
        while self.i < len(self.s) and self.s[self.i].isspace():
            self.i += 1
    
    # Move index till it doesnt meet word (a-z, #-.%)
    # Return word
    def word(self):
        start = self.i
        while self.i < len(self.s):
            if self.s[self.i].isalnum() or self.s[self.i] in "#-.%":
                self.i += 1
            else:
                break
        if not (self.i > start):
            raise Exception("Parsing error")
        return self.s[start:self.i]
    
    # Move index (just once)
    # Check for literal (e.g. ;) 
    def literal(self, literal):
        if not (self.i < len(self.s) and self.s[self.i] == literal):
            raise Exception("Parsing error")
        self.i += 1

    # Get key val property of css (e.g. body-color: red)
    # Return as key, val
    def pair(self):
        prop = self.word()
        self.whitespace()
        self.literal(":")
        self.whitespace()
        val = self.word()
        return prop.casefold(), val
    
    # Get bunch of key, val of style attribute
    # Return as {key: val, key2: val2}
    def body(self):
        pairs = {}
        while self.i < len(self.s):
            try:
                prop, val = self.pair()
                pairs[prop.casefold()] = val
                self.whitespace()
                self.literal(";")
                self.whitespace()
            except Exception:
                why = self.ignore_until([";"])
                if why == ";":
                    self.literal(";")
                    self.whitespace()
                else:
                    break
        return pairs
    
    # Move index, ignore all characters until it meet some in (param)chars
    # e.g. broken style (k&6hd: ssa;). Ignore that, move index till meet (;)
    # Return the character
    def ignore_until(self, chars):
        while self.i < len(self.s):
            if self.s[self.i] in chars:
                return self.s[self.i]
            else:
                self.i += 1
        return None

# Check if node has style attribute, the value is still string
# Put the style in the node (node.style)
def style(node):
    node.style = {}
    if isinstance(node, Element) and "style" in node.attributes:
        pairs = CSSParser(node.attributes["style"]).body()
        for property, value in pairs.items():
            node.style[property] = value
    
    # Do the same to the child
    for child in node.children:
        style(child)