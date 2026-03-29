"""Quick diagnostic: check if Cyrillic search works on search-index.json"""
import json, sys

path = r'b:\antigravity\dori\site1_tv\build_v2\static\js\search-index.json'

# Check first bytes for BOM
with open(path, 'rb') as f:
    head = f.read(20)
    print(f"First 20 bytes (hex): {head[:20].hex()}")
    if head[:3] == b'\xef\xbb\xbf':
        print("⚠️  BOM detected!")
    else:
        print("✅ No BOM")

# Load JSON
with open(path, 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"\nTotal entries: {len(data)}")

# Check first 3 entries
for d in data[:3]:
    t = d.get('t', '')
    s = d.get('s', '')
    print(f"  s={s[:50]}")
    print(f"  t={t[:60]}")
    print(f"  t bytes: {t[:10].encode('utf-8').hex()}")
    print()

# Test Cyrillic search
test_queries = ['телевизор', 'samsung', 'как', 'настройка', 'звук']
for q in test_queries:
    ql = q.lower()
    results = [d for d in data if ql in d.get('t', '').lower() or ql in d.get('s', '').lower()]
    print(f"Query '{q}' -> {len(results)} results")
    if results:
        print(f"  First: {results[0]['t'][:60]}")

# Check for entries without 't' field or with empty 't'
no_t = sum(1 for d in data if not d.get('t'))
print(f"\nEntries without title: {no_t}")

# Check if any 't' contains non-UTF8 or mojibake
import unicodedata
mojibake = 0
for d in data:
    t = d.get('t', '')
    # Check for replacement characters or unusual code points
    if '\ufffd' in t or any(unicodedata.category(c) == 'Cn' for c in t[:20]):
        mojibake += 1
print(f"Entries with encoding issues: {mojibake}")
