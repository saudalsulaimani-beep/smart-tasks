#!/usr/bin/env python3
"""
index.html هو مستند كامل لأنه يُقدَّم كموقع.
صفحة Artifact على claude.ai تضيف غلافها بنفسها، فتحتاج نفس المحتوى
بلا doctype ولا html/head/body. هذا السكربت يولّدها من المصدر الواحد
حتى لا تفترق النسختان.
"""
import os, re, sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SRC = os.path.join(ROOT, "index.html")
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "build", "artifact.html")

src = open(SRC, encoding="utf-8").read()

head = re.search(r"<head>(.*?)</head>", src, re.S).group(1)
body = re.search(r"<body>(.*?)</body>", src, re.S).group(1)

# الغلاف يوفّر الترميز، والملفات المجاورة غير موجودة داخل الـ Artifact
drop = (
    r'<meta charset="utf-8">',
    r'<link rel="manifest"[^>]*>',
    r'<link rel="icon"[^>]*>',
    r'<link rel="apple-touch-icon"[^>]*>',
)
for pat in drop:
    head = re.sub(pat, "", head)
head = re.sub(r"\n{3,}", "\n\n", head).strip()

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(head + "\n\n" + body.strip() + "\n")
print("wrote", OUT, os.path.getsize(OUT), "bytes")
