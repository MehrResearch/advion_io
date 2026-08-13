# advion_io

Pure-Python reading and writing of Advion `.datx` mass-spectrometry
data sets. No vendor DLLs, no `ctypes`, no Windows requirement — the
package decodes and encodes the container and per-scan binary format
directly, so it runs anywhere NumPy does.

```bash
uv add advion-io          # or: pip install advion-io
```

## Reading

Two layers are provided.

`DatxFile` is the lean container/decoder. Use it when you just want
the numbers, plus the archive's metadata XML (method, tune, log):

```python
from advion_io import DatxFile

with DatxFile("acquisition.datx") as dx:
    masses      = dx.masses              # float32, shape (M,)
    times       = dx.retention_times     # float32, shape (N,)
    intensities = dx.intensities         # float32, shape (N, M)
    one_scan    = dx.get_spectrum(0)     # float32, shape (M,)
```

`DataReader` is a higher-fidelity, Advion-shaped API on top of
`DatxFile`. Method names and return types match the Advion reference
implementation, so code written against the vendor API needs no
changes. It adds Peak Express delta backgrounds / delta spectra, XICs,
segment / scalar-channel / aux-file metadata, `save()`, and so on:

```python
from advion_io import DataReader

with DataReader("acquisition.datx") as dr:
    n     = dr.get_num_spectra()
    tic   = dr.get_TIC(0)
    spec  = dr.get_spectrum(0)
    dr.set_delta_background_parameters(0.0, 10.0, 3.0, 0.4, 1_000_000)
    delta = dr.get_delta_spectrum(10)
    xic   = dr.generate_xic([100, 200])
```

## Writing

`DataWriter` is the inverse of `DataReader`: it produces `.datx`
archives that any compatible reader (ours or the vendor's) can open.
Like the reference implementation it writes a folder of loose files
during acquisition and only zips it up at the end:

```python
import numpy as np
from advion_io import DataWriter

masses = np.arange(100.0, 700.0, 0.05, dtype=np.float32)

with DataWriter("./data", "my_run", is_centroid=False) as w:
    w.set_metadata("my-app 0.1", "firmware-X", "inst-001", "CMS-L")
    w.write_method(method_xml)
    w.write_tune_params(tune_xml)
    w.write_ion_source_opt(ion_source_xml)
    w.write_spectrum_masses(masses)
    for t, intensities in scans:
        w.write_scan_data(intensities, retention_time=t,
                          tic=float(intensities.sum()))
    out_path = w.create_datx_file()    # ./data/my_run.datx
```

Decoded values match the reference output to the precision of float32
(TIC reproduces to ~4e-7 relative error on the bundled example file).
Every scan of the example file round-trips through `encode → decode`
bit-for-bit identical, and the total `.spectra` byte count matches what
the reference produces.

## Batch conversion

A `convert-all` console script walks a folder and decodes every `.datx`
it finds into a gzipped pickle of `{masses, times, intensities}`:

```bash
uv run convert-all /path/to/folder
```

## Layout

```
src/advion_io/
    constants.py        # IntEnums mirroring the Advion API (error codes, states, …)
    data_reader.py      # DataReader + DatxFile + decoder
    data_writer.py      # DataWriter + encoder
    convertall.py       # `convert-all` batch decoder
tests/
    test_data_reader.py
    test_data_writer.py
    test_datx_file.py
    data/example.datx   # Example acquisition used by the tests
datx_dashboard.py       # marimo notebook plotting an acquisition
```

## Development

```bash
uv sync
uv run pytest
```

Tests that need the example acquisition skip automatically when it is
absent. Point `ADVION_EXAMPLE_DATX` at another `.datx` file to run them
against your own data (a few assertions are specific to the bundled
file).

## Scope

This package covers *data files only*. Live instrument control
(the vendor's `AdvionCMS` layer) is not implemented here.

## License

MIT — see [`LICENSE`](./LICENSE).

Advion, Expression and CMS are trademarks of their respective owners;
this project is not affiliated with or endorsed by them.
