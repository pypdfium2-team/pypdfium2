import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1]/"setupsrc"))
from base import get_cool_date

n_days = int(sys.argv[1])
print(get_cool_date(n_days))
