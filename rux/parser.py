# coding=utf8

"""
    rux.parser
    ~~~~~~~~~~

    Parser from post source to html.
"""

from datetime import datetime
import os

from . import charset, src_ext
from .exceptions import *

import houdini
import misaka
from misaka import HtmlRenderer, SmartyPants
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter
from pygments.util import ClassNotFound

src_ext_len = len(src_ext)  # cache this, call only once


class RuxHtmlRenderer(HtmlRenderer, SmartyPants):
    """misaka render with color codes feature"""

    def _code_no_lexer(self, text):
        # encode to utf8 string
        text = text.encode(charset).strip()
        return(
            """
            <div class="highlight">
              <pre><code>%s</code></pre>
            </div>
            """ % houdini.escape_html(text)
        )

    def block_code(self, text, lang):
        """text: unicode text to render"""

        if not lang:
            return self._code_no_lexer(text)

        try:
            lexer = get_lexer_by_name(lang, stripall=True)
        except ClassNotFound:  # lexer not found, use plain text
            return self._code_no_lexer(text)

        formatter = HtmlFormatter()

        return highlight(text, lexer, formatter)


class Parser(object):
    """Usage::

        parser = Parser()
        parser.parse(str)   # return dict
        parser.markdown.render(markdown_str)  # render markdown to html

    """

    separator = '---'

    def __init__(self):
        """Initialize the parser, set markdown render handler as
        an attribute `markdown` of the parser"""
        render = RuxHtmlRenderer()  # initialize the color render
        extensions = (
            misaka.EXT_FENCED_CODE |
            misaka.EXT_NO_INTRA_EMPHASIS |
            misaka.EXT_AUTOLINK
        )

        self.markdown = misaka.Markdown(render, extensions=extensions)

    def parse_markdown(self, markdown):
        return self.markdown.render(markdown)

    def parse(self, source):
        """Parse unicode post source, return dict"""

        head, markdown = self.split(source)

        # parse title, pic title from source
        lines = filter(lambda x: x and not x.isspace(), head.splitlines())

        if not lines:
            raise PostTitleNotFound

        title = lines[0]

        title_pic = ''
        if len(lines) == 2:
            title_pic = lines[1]
        elif len(lines) > 2:  # too many no-space lines
            raise PostHeadSyntaxError

        # render to html
        html = self.markdown.render(markdown)
        summary = self.markdown.render(markdown[:200])

        return {
            'title': title,
            'markdown': markdown,
            'html': html,
            'summary': summary,
            'title_pic': title_pic
        }

    def split(self, source):
        """split head and body, return tuple(head, body)"""
        lines = source.splitlines()
        l = None

        for lineno, line in enumerate(lines):
            if self.separator in line:
                l = lineno
                break

        if not l:
            raise SeparatorNotFound

        head, body = "\n".join(lines[:l]), "\n".join(lines[l+1:])

        return head, body

    def parse_filename(self, filepath):
        """parse post source files name to datetime object"""
        name = os.path.basename(filepath)[:-src_ext_len]
        try:
            dt = datetime.strptime(name, "%Y-%m-%d-%H-%M")
        except ValueError:
            raise PostNameInvalid
        return {'name': name, 'datetime': dt, 'filepath': filepath}

    def parse_file(self, filepath):
        """parse post from file"""
        data = self.parse(open(filepath).read().decode(charset))
        data.update(self.parse_filename(filepath))
        return data


parser = Parser()  # build a runtime parser
