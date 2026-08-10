import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[2]/"setupsrc"))
from shared_base import install_dep_groups

install_dep_groups(sys.argv[1:], need_fallback=True)
