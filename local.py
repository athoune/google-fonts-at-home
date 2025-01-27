#!/usr/bin/env python3

import requests
import tinycss2
from tinycss2.ast import (
    AtRule,
    WhitespaceToken,
    LiteralToken,
    FunctionBlock,
    IdentToken,
)


def slurp(url: str):
    resp = requests.get(url)
    assert resp.status_code == 200
    rules = tinycss2.parse_stylesheet(
        resp.content.decode("utf-8"), skip_comments=True, skip_whitespace=True
    )
    for rule in rules:
        if isinstance(rule, AtRule) and rule.lower_at_keyword == "font-face":
            for line in cut(rule.content):
                assert isinstance(line[0], IdentToken)
                assert isinstance(line[1], LiteralToken) and line[1].value == ":"
                key = line[0].value
                values = line[2:]
                print(key, values)
        print("----------------")


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
