# advion_io

Pure-Python reading and writing of Advion `.datx` mass-spectrometry
data sets.

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
`DatxFile`.

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

## Interactive dashboard

[`Analysis.py`](./Analysis.py) is a [marimo](https://marimo.io) notebook for
exploring Advion .datx data.

```bash
# app mode (marimo run)
uvx --from git+https://github.com/MehrResearch/advion_io ms-dashboard

# editor mode (marimo edit), to tweak the cells
uvx --from git+https://github.com/MehrResearch/advion_io ms-dashboard-edit
```

Extra arguments are forwarded to marimo, e.g. `... ms-dashboard --port 2718
--headless`. Pick the acquisitions to analyse with the file browser at the top
of the notebook.

In a checkout the same notebook runs directly:

```bash
uvx marimo edit --sandbox Analysis.py    # isolated venv from its PEP 723 header
uv run marimo edit Analysis.py           # against the local advion_io source
```

## Batch conversion

A `convert-all` console script walks a folder and decodes every `.datx`
it finds into a gzipped pickle of `{masses, times, intensities}`:

```bash
uv run convert-all /path/to/folder
```
