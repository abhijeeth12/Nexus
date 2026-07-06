import re
import json

s = '{"command": "find downloads -type f \\\\\\( -name"}'
print("LLM literal string:", repr(s))

c = re.sub(r'\\(?![\\"/bfnrtu])', r'\\\\', s)
print("After re.sub:", repr(c))

try:
    print(json.loads(c))
except Exception as e:
    print("Error:", repr(e))
