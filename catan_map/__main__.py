import sys

if not __package__:
    # Started as a file or as a folder (`python catan_map/__main__.py`, `python catan_map`):
    # make the package importable first.
    import os

    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from catan_map.cli import main
else:
    from .cli import main

sys.exit(main())
