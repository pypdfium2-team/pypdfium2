import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "setupsrc"))
from pypdfium2_setup.craft_packages import TmpCommitCtx

def main():
    if TmpCommitCtx.FILE.exists():
        TmpCommitCtx.undo()

if __name__ == "__main__":
    main()
