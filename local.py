#!/usr/bin/env python3

import io
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
)

BAD = re.compile(r"[. ]+")


def slurp(url: str):
    resp = requests.get(url)
    assert resp.status_code == 200
    rules = tinycss2.parse_stylesheet(
        resp.content.decode("utf-8"), skip_comments=True, skip_whitespace=True
    )
    for rule in rules:
        block = dict(line for line in handle_rule(rule))
        name = file_name(block)
        url = block["src"][0].value
        print(name)
        download(url, name)
        subprocess.run(["woff2_compress", name], check=True)


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


def handle_rule(rule):
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
        "https://fonts.googleapis.com/css2?family=Fira+Code:wght@300..700&family=Open+Sans:ital,wght@0,300..800;1,300..800&display=swap"
    )
