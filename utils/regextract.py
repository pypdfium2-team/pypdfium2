import re
import sys

pattern = sys.argv[1]
out_pattern = sys.argv[2]
string = sys.argv[3]

match = re.search(pattern, string)
result = out_pattern % match.groups()
print(result, end="")
