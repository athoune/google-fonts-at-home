# Google Fonts at home

Google fonts is useful, but, for more privacy, you should host this fonts.

## Install

Install [Google's woff2 tool](https://github.com/google/woff2).

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install .

./local.py "your google fonts CSS file" "https://fonts.example.com"
```
