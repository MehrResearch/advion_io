"""Walk a folder, decode every ``.datx`` to a gzipped pickle.

Uses the pure-Python :class:`advion_io.DataReader`, so it runs on any
platform.  Output schema (one pickle per ``.datx``): a dict with keys
``masses``, ``times`` and ``intensities``.
"""
import logging
import sys
from pathlib import Path

from advion_io import DataReader


def main():
    path = Path(sys.argv[-1])
    for data_file in path.glob("**/*.datx"):
        outfile = data_file.with_suffix(".pkgz")
        if outfile.exists():
            print(f"Skipping {data_file} => {outfile}")
            continue
        print(f"Now processing {data_file} => {outfile}")
        try:
            with DataReader(data_file) as reader:
                reader.save(outfile)
        except (IOError, ValueError) as e:
            logging.exception(e)
            continue


if __name__ == "__main__":
    main()
