import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1]/"setupsrc"))
from base import get_cool_date

cooldown_days = int(sys.argv[1])
freeze_date = sys.argv[2] if len(sys.argv) > 2 else ""
if freeze_date:
    print(freeze_date)
else:
    print(get_cool_date(cooldown_days))
