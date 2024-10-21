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
        while self.i < len(self.s) and self.s[self.i] != "}":
            try:
                prop, val = self.pair()
                pairs[prop.casefold()] = val
                self.whitespace()
                self.literal(";")
                self.whitespace()
            except Exception:
                why = self.ignore_until([";", "}"])
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
    
    # Selector is basically like this => div p span {}
    # Return nested Descendant Selector
    # e.g. for this div span p, gonna return this
    # DescendantSelector(
    #     DescendantSelector(
    #         TagSelector('div'), 
    #         TagSelector('span')
    #     ), 
    #     TagSelector('p')
    # )
    def selector(self):
        out = TagSelector(self.word().casefold())
        self.whitespace()
        while self.i < len(self.s) and self.s[self.i] != "{":
            tag = self.word()
            descendant = TagSelector(tag.casefold())
            out = DescendantSelector(out, descendant)
            self.whitespace()
        return out
    
    # e.g. for => p {color: red} div {color: blue} gonna return
    # [(p, {color: red})] list of tuple
    def parse(self):
        rules = []
        while self.i < len(self.s):
            try:
                self.whitespace()
                selector = self.selector()
                self.literal("{")
                self.whitespace()
                body = self.body()
                self.literal("}")
                rules.append((selector, body))
            except Exception:
                why = self.ignore_until(["}"])
                if why == "}":
                    self.literal("}")
                    self.whitespace()
                else:
                    break
        return rules

INHERITED_PROPERTIES = {
    "font-size": "16px",
    "font-style": "normal",
    "font-weight": "normal",
    "color": "black",
}

# Check if node has style attribute, the value is still string
# Put the style in the node (node.style)
def style(node, rules):
    node.style = {}

    # Setting default style properties
    for property, default_value in INHERITED_PROPERTIES.items():
        if node.parent:
            node.style[property] = node.parent.style[property]
        else:
            node.style[property] = default_value

    # For every rules in CSS file, check if the node match the rule
    for selector, body in rules:
        if not selector.matches(node): continue
        for property, value in body.items():
            node.style[property] = value

    # Style attribute in element override
    if isinstance(node, Element) and "style" in node.attributes:
        pairs = CSSParser(node.attributes["style"]).body()
        for property, value in pairs.items():
            node.style[property] = value

    # Handle styling with value of %, this needs to be handled since it's relative to it's parent
    # Convert from % to px
    if node.style["font-size"].endswith("%"):
        if node.parent:
            parent_font_size = node.parent.style["font-size"]
        else:
            parent_font_size = INHERITED_PROPERTIES["font-size"]
        node_pct = float(node.style["font-size"][:-1]) / 100
        parent_px = float(parent_font_size[:-2])
        node.style["font-size"] = str(node_pct * parent_px) + "px"

    # Do the same to the child
    for child in node.children:
        style(child, rules)

# Wrap tag (e.g. p, div) to a class
# TODO: check if the priority order is correct
class TagSelector:
    def __init__(self, tag):
        self.tag = tag
        self.priority = 1

    def matches(self, node):
        return isinstance(node, Element) and self.tag == node.tag

class DescendantSelector:
    def __init__(self, ancestor, descendant):
        # These two are of type TagSelector
        self.ancestor = ancestor
        self.descendant = descendant
        self.priority = ancestor.priority + descendant.priority

    # Check if current node match the tag
    # Then recursively going up checking ancestor with node.parent
    def matches(self, node):
        if not self.descendant.matches(node): return False
        while node.parent:
            if self.ancestor.matches(node.parent): return True
            node = node.parent
        return False

# Generic helper function
def tree_to_list(tree, list):
    list.append(tree)
    for child in tree.children:
        tree_to_list(child, list)
    return list

# for sorting css rule
def cascade_priority(rule):
    selector, body = rule
    return selector.priority