#!/usr/bin/env python3
from dataclasses import dataclass
from typing import Union, List, Dict
import re

@dataclass
class SSMLTag:
    name: str
    attributes: Dict[str, str]
    children: List["SSMLNode"]

    def __init__(self, name: str, attributes=None, children=None):
        self.name = name
        self.attributes = attributes or {}
        self.children = children or []

@dataclass
class SSMLText:
    text: str

SSMLNode = Union[SSMLTag, SSMLText]

def parseSSML(ssml: str) -> SSMLNode:
    """
    Parses a minimal SSML string into an SSMLNode tree.
    Enforces exactly one <speak>…</speak>, proper matching tags, double-quoted attrs,
    and unescapes &lt;, &gt;, &amp;.
    """
    ssml = ssml.strip()

    # Allow spaces around tag name and closing tag
    full_re = re.compile(
        r'^\s*<\s*speak'                                 # < speak
        r'(?P<attrs>(?:\s+[A-Za-z0-9_:-]+\s*=\s*"[^"]*")*)'  # optional attrs
        r'\s*>\s*'                                       # >
        r'(?P<body>.*)'                                  # body
        r'\s*<\s*/\s*speak\s*>\s*$'                      # </ speak >
        , re.DOTALL
    )

    m_full = full_re.match(ssml)
    if not m_full:
        raise ValueError("SSML must have a single top-level <speak>…</speak> with valid attrs")

    # Parse <speak> attributes
    attrs_raw = m_full.group('attrs')
    attrs: Dict[str, str] = {}
    if attrs_raw:
        for am in re.finditer(r'([A-Za-z0-9_:-]+)\s*=\s*"([^"]*)"', attrs_raw):
            attrs[am.group(1)] = am.group(2)

    body = m_full.group('body')

    token_re = re.compile(
        r'(?P<text>[^<]+)|'
        r'<\s*(?P<closing>/)?\s*'
          r'(?P<name>[A-Za-z0-9_:-]+)'
          r'(?P<attrs>(?:\s+[A-Za-z0-9_:-]+\s*=\s*"[^"]*")*)'
        r'\s*(?P<selfclose>/)?>'
        , re.DOTALL
    )

    def unescape(s: str) -> str:
        return s.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")

    stack: List[SSMLTag] = [SSMLTag("speak", attrs, [])]
    open_count = 0
    close_count = 0

    for m in token_re.finditer(body):
        if m.group("text"):
            txt = unescape(m.group("text"))
            stack[-1].children.append(SSMLText(txt))
        else:
            nm = m.group("name")
            is_closing = bool(m.group("closing"))
            is_self = bool(m.group("selfclose"))
            attrs_part = m.group("attrs") or ""

            # Validate double-quoted attrs
            if attrs_part and not all(
                re.fullmatch(r'\s*[A-Za-z0-9_:-]+\s*=\s*"[^"]*"', tok)
                for tok in attrs_part.strip().split()
            ):
                raise ValueError("Invalid attribute syntax in tag")

            tag_attrs: Dict[str, str] = {}
            for am in re.finditer(r'([A-Za-z0-9_:-]+)\s*=\s*"([^"]*)"', attrs_part):
                tag_attrs[am.group(1)] = am.group(2)

            if is_closing:
                close_count += 1
                node = stack.pop()
                if node.name != nm:
                    raise ValueError(f"Mismatched closing tag: {nm}")
                stack[-1].children.append(node)
            else:
                if not is_self:
                    open_count += 1
                new_tag = SSMLTag(nm, tag_attrs, [])
                if is_self:
                    stack[-1].children.append(new_tag)
                else:
                    stack.append(new_tag)

    if open_count != close_count:
        raise ValueError("Unbalanced tags in SSML body")

    return stack[0]

def ssmlNodeToText(node: SSMLNode) -> str:
    """
    Flattens an SSMLNode tree back to a string, including tags.
    """
    if isinstance(node, SSMLText):
        return node.text

    attrs_str = ""
    if node.attributes:
        parts = [f'{k}="{v}"' for k, v in node.attributes.items()]
        attrs_str = " " + " ".join(parts)
    inner = "".join(ssmlNodeToText(child) for child in node.children)
    return f"<{node.name}{attrs_str}>{inner}</{node.name}>"
