import os
import sys

if __package__ in (None, ""):          # allow:  python3 path/to/PM-Framework/pmf <command>
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pmf.cli import main

if __name__ == "__main__":
    sys.exit(main())
