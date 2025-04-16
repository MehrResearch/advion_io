import logging
import sys
from pathlib import Path

from advion_io import AdvionData

if __name__ == "__main__":
    path = Path(sys.argv[-1])
    for data_file in path.glob("**/*.datx"):
        outfile = data_file.with_suffix(".pkgz")
        if outfile.exists():
            print(f"Skipping {data_file} => {outfile}")
            continue
        print(f"Now processing {data_file} => {outfile}")
        data_reader = AdvionData(str(data_file).encode(), False, False)
        try:
            data_reader.save(outfile)
        except IOError as e:
            logging.exception(e)
            continue
