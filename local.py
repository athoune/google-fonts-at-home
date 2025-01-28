#!/usr/bin/env python3

import io
from pathlib import Path
import re
import subprocess

import requests
import tinycss2
from tinycss2.ast import (
    AtRule,
    WhitespaceToken,
    LiteralToken,
    FunctionBlock,
    IdentToken,
    NumberToken,
    URLToken,
    StringToken,
)

BAD = re.compile(r"[. ]+")


def slurp(google_css_url: str, my_url_prefix: str = ""):
    my_url_prefix = my_url_prefix.rstrip("/")
    resp = requests.get(google_css_url)
    assert resp.status_code == 200
    rules = tinycss2.parse_stylesheet(
        resp.content.decode("utf-8"), skip_comments=True, skip_whitespace=True
    )
    sources = []
    names = []

    for rule in rules:
        block = dict(line for line in atRule_to_kv(rule))
        name = file_name(block)
        print(name)
        names.append(name)
        sources.append(block["src"][0])
        if not Path(name).exists():
            google_css_url = block["src"][0].value
            download(google_css_url, name)
        if not Path(name[:-3] + "woff2").exists():
            subprocess.run(["woff2_compress", name], check=True, capture_output=True)

    names.reverse()
    for rule in rules:
        patched = []
        for c in rule.content:
            if isinstance(c, URLToken):
                patched.append(WhitespaceToken(0, 0, "\n    "))
                name = names.pop()
                value = "%s/%s" % (my_url_prefix, name[:-3] + "woff2")
                patched.append(URLToken(0, 0, value, "url(%s)" % value))
                patched.append(WhitespaceToken(0, 0, " "))
                patched.append(
                    FunctionBlock(0, 0, "format", [StringToken(0, 0, "woff2", "woff2")])
                )
                patched.append(LiteralToken(0, 0, ","))
                patched.append(WhitespaceToken(0, 0, "\n    "))
                c.value = "%s/%s" % (my_url_prefix, name)
                c.representation = "url(%s)" % c.value
            patched.append(c)
        rule.content = patched

    with open("index.css", "w") as output:
        output.write(tinycss2.serialize(rules))


def file_name(block: dict):
    buff = io.StringIO()
    for k in ["family", "style", "weight"]:
        v = block["font-" + k][0]
        if isinstance(v, NumberToken):
            buff.write(str(int(v.value)))
        else:
            buff.write(BAD.sub("_", v.value))
        buff.write("-")
    buff.seek(buff.tell() - 1)  # removing trailing -
    buff.write(".")
    assert isinstance(block["src"][-1], FunctionBlock)
    format = block["src"][-1].arguments[0].value
    if format == "truetype":
        buff.write("ttf")
    else:
        raise Exception("Unknown format:", format)
    buff.seek(0)
    return buff.read()


def download(url, file):
    resp = requests.get(url)
    assert resp.status_code == 200
    with open(file, "wb") as f:
        f.write(resp.content)


def atRule_to_kv(rule):
    if isinstance(rule, AtRule) and rule.lower_at_keyword == "font-face":
        for line in cut(rule.content):
            assert isinstance(line[0], IdentToken)
            assert isinstance(line[1], LiteralToken) and line[1].value == ":"
            key = line[0].value
            values = line[2:]
            yield (key, values)


def cut(content):
    last = 0
    for i, token in enumerate(content):
        if isinstance(token, LiteralToken) and token.value == ";":
            yield [c for c in content[last:i] if not isinstance(c, WhitespaceToken)]
            last = i + 1


if __name__ == "__main__":
    slurp(
        "https://fonts.googleapis.com/css2?family=Fira+Code:wght@300..700&family=Open+Sans:ital,wght@0,300..800;1,300..800&display=swap",
        "https://font.example.com",
    )
