import json
with open('openapi.json', 'r', encoding='utf-16' if '\0' in open('openapi.json', 'rb').read() else 'utf-8') as f:
    try:
        data = json.load(f)
    except:
        # PowerShell ConvertTo-Json might output UTF-16 LE
        f = open('openapi.json', 'r', encoding='utf-16-le')
        data = json.load(f)

print("ROUTES:")
paths = data.get('paths', {})
for path, methods in paths.items():
    print(f"{path}: {list(methods.keys())}")
