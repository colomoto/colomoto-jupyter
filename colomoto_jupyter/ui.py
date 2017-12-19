
import sys

from colomoto_jupyter import IN_IPYTHON

if IN_IPYTHON:
    from IPython.display import display, Markdown


if IN_IPYTHON:
    def info(msg):
        """
        Display `msg` (interpreted in Markdown format)
        """
        display(Markdown(msg))
else:
    def info(msg):
        """
        Print `msg` in stderr
        """
        print(msg, file=sys.stderr)

