with open('train_nasa_dl.py', 'r', encoding='utf-8') as f:
    content = f.read()
with open('train_nasa_dl.py', 'w', encoding='utf-8') as f:
    f.write("import sys; sys.stdout.reconfigure(encoding='utf-8')\n" + content)
