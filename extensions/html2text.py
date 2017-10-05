#https://stackoverflow.com/a/15609065/2403000
import HTMLParser
import re


#Regular expressions to recognize different parts of HTML. 
#Internal style sheets or JavaScript 
SCRIPT_SHEET = re.compile(r"<(script|style).*?>.*?(</\1>)", re.IGNORECASE | re.DOTALL)

#HTML comments - can contain ">"
COMMENT = re.compile(r"<!--(.*?)-->", re.DOTALL) 

#Consecutive whitespace characters
NWHITES = re.compile(r"[\s]+")

#<p>, <div>, <br> tags and associated closing tags
P_DIV = re.compile(r"</?(p|div|br).*?>", re.IGNORECASE | re.DOTALL)

#HTML tags: <any-text>
TAG = re.compile(r"<.*?>", re.DOTALL)
                   
#Consecutive whitespace, but no newlines
NSPACE = re.compile("[^\S\n]+", re.UNICODE)

#A return followed by a space
RETSPACE = re.compile("(\n )")

#At least two consecutive newlines
N2RET = re.compile("\n\n+")

#For converting HTML entities to unicode
HTML_PARSER = HTMLParser.HTMLParser()


def html2text(html=None):
    """Remove all HTML tags and produce a nicely formatted text."""
    if html is None:
        return u''
    text = unicode(html)
    
    #Strip tags
    text = SCRIPT_SHEET.sub("", text)
    text = COMMENT.sub("", text)
    text = NWHITES.sub(" ", text)
    text = P_DIV.sub("\n", text) #convert <p>, <div>, <br> to "\n"
    text = TAG.sub("", text)     #remove all tags
    text = HTML_PARSER.unescape(text)
    
    #Handle whitespace
    text = NSPACE.sub(" ", text)
    text = RETSPACE.sub("\n", text)
    text = N2RET.sub("\n\n", text)
    
    return text.strip()
