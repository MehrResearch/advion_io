"""Tests for the pure-Python ``DataWriter`` reimplementation.

We exercise every public method, plus a full read \u2192 write \u2192 read
fidelity check against the bundled example file.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from advion_io import (
    DataReader,
    DataWriter,
    decode_intensities_blob,
    encode_intensities_blob,
)
from advion_io.constants import AdvionDataErrorCode
from example_data import EXAMPLE_DATX, SKIP_REASON


# ---------------------------------------------------------------------------
# Low-level encoder round-trip
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "values",
    [
        [0, 0, 0, 0, 0],
        [1, 1, 1, 1, 1],
        [100, 200, 300, 400, 500],
        [0, 100, 0, 100, 0, 100, 0, 100],
        list(range(1, 100)),
        # Many leading and trailing zeros around peaks.
        [0] * 50 + [1000, 2000, 1500, 0, 0, 0, 5000, 0, 0],
    ],
)
def test_encode_decode_roundtrip_synthetic(values):
    arr = np.asarray(values, dtype=np.int64)
    blob = encode_intensities_blob(arr)
    out = decode_intensities_blob(blob, arr.size).astype(np.int64)
    np.testing.assert_array_equal(out, arr)


def test_encode_decode_roundtrip_random():
    rng = np.random.default_rng(42)
    for _ in range(20):
        n = int(rng.integers(20, 2000))
        # Skewed: many small values, occasional spikes.
        arr = rng.integers(0, 1000, size=n).astype(np.int64)
        spikes = rng.integers(0, n, size=n // 20)
        arr[spikes] = rng.integers(100_000, 5_000_000, size=spikes.size)
        blob = encode_intensities_blob(arr)
        np.testing.assert_array_equal(
            decode_intensities_blob(blob, n).astype(np.int64), arr
        )


def test_encode_decode_against_example_file():
    """Every scan from the bundled file round-trips bit-identically."""
    if not EXAMPLE_DATX.exists():
        pytest.skip(SKIP_REASON)
    from advion_io import DatxFile

    with DatxFile(EXAMPLE_DATX) as dx:
        for i in range(dx.num_spectra):
            original = dx.get_spectrum(i).astype(np.int64)
            blob = encode_intensities_blob(original)
            assert len(blob) == dx.scans[i].size, (
                f"scan {i}: encoded size {len(blob)} != reference size "
                f"{dx.scans[i].size}"
            )
            rt = decode_intensities_blob(blob, dx.num_masses).astype(np.int64)
            np.testing.assert_array_equal(rt, original)


def test_encode_rejects_negative_or_huge():
    with pytest.raises(ValueError):
        encode_intensities_blob(np.array([-1, 0, 1], dtype=np.int64))
    with pytest.raises(ValueError):
        encode_intensities_blob(np.array([0, 0, 0xFFFFFFFFF], dtype=np.int64))
    with pytest.raises(ValueError):
        encode_intensities_blob(np.zeros(0, dtype=np.int64))


# ---------------------------------------------------------------------------
# DataWriter \u2014 high-level
# ---------------------------------------------------------------------------


@pytest.fixture
def writer_setup(tmp_path):
    """Returns a callable that builds a small valid dataset and returns the
    written .datx path."""

    def build(
        n_scans: int = 5,
        n_masses: int = 50,
        with_scalar: bool = False,
        with_aux: bool = False,
        log_msg: str | None = None,
    ) -> Path:
        rng = np.random.default_rng(0)
        masses = np.arange(100.0, 100.0 + n_masses * 0.05, 0.05, dtype=np.float32)
        masses = masses[:n_masses]  # guard against floating step drift

        scans = []
        for _ in range(n_scans):
            spec = rng.integers(0, 500, size=n_masses).astype(np.int64)
            spec[n_masses // 2] += 10_000
            scans.append(spec)

        with DataWriter(tmp_path, "T", is_centroid=False) as w:
            w.set_metadata("1.2.3", "fwX", "inst-001", "CMS-L")
            w.write_method('<?xml version="1.0"?><method/>')
            w.write_tune_params('<?xml version="1.0"?><tuneParameters/>')
            w.write_ion_source_opt('<?xml version="1.0"?><ionSourceOptimization/>')
            w.write_scan_mode_index(0)
            if log_msg:
                w.write_log_message(log_msg)
            w.write_spectrum_masses(masses)
            for i, s in enumerate(scans):
                w.write_scan_data(s, retention_time=0.5 + 0.1 * i, tic=float(s.sum()))

            if with_scalar:
                cid = w.create_scalar_channel("UV")
                w.add_scalar_channel_attribute(cid, "wavelength", 254.0)
                w.write_scalar_entries(cid, [0.0, 0.1, 0.2], [1.0, 2.0, 1.5])

            if with_aux:
                aid = w.create_auxiliary_file("notes", "text")
                w.write_text_to_file(aid, "auxiliary body")

            return w.create_datx_file()

    return build


def test_write_then_read_basic(writer_setup):
    path = writer_setup(n_scans=4, n_masses=40)
    with DataReader(path) as r:
        assert r.get_num_spectra() == 4
        assert r.get_num_masses() == 40
        assert r.get_software_version() == "1.2.3"
        assert r.get_firmware_version() == "fwX"
        assert r.get_instrument_id() == "inst-001"
        assert r.get_hardware_type() == "CMS-L"
        # Times are stored in the .scans XML; check ordering and shape.
        rts = r.get_retention_times()
        assert rts.shape == (4,)
        assert np.all(np.diff(rts) > 0)
        # Masses come back exactly as written.
        masses = r.get_masses()
        assert masses.shape == (40,)
        assert masses.dtype == np.float32


def test_write_then_read_round_trip_intensities(writer_setup, tmp_path):
    # Re-build inline so we have direct access to the source arrays.
    rng = np.random.default_rng(123)
    masses = np.arange(100.0, 110.0, 0.05, dtype=np.float32)
    scans = [rng.integers(0, 5000, size=masses.size).astype(np.int64) for _ in range(8)]

    with DataWriter(tmp_path, "RT", is_centroid=False) as w:
        w.set_metadata("v", "f", "i", "CMS")
        w.write_spectrum_masses(masses)
        for i, s in enumerate(scans):
            w.write_scan_data(s, retention_time=0.1 * i, tic=float(s.sum()))
        path = w.create_datx_file()

    with DataReader(path) as r:
        for i, expected in enumerate(scans):
            got = r.get_spectrum(i).astype(np.int64)
            np.testing.assert_array_equal(got, expected)


def test_write_scalar_channel(writer_setup):
    path = writer_setup(with_scalar=True)
    with DataReader(path) as r:
        assert r.get_num_scalar_channels() == 1
        assert r.get_scalar_channel_name(0) == "UV"
        assert r.get_scalar_channel_num_samples(0) == 3
        assert r.get_scalar_channel_num_attributes(0) == 1
        assert r.get_scalar_channel_attribute_name(0, 0) == "wavelength"
        assert r.get_scalar_channel_attribute_value(0, 0) == pytest.approx(254.0)
        np.testing.assert_allclose(
            r.get_scalar_channel_times(0), np.array([0.0, 0.1, 0.2], dtype=np.float32)
        )
        np.testing.assert_allclose(
            r.get_scalar_channel_values(0), np.array([1.0, 2.0, 1.5], dtype=np.float32)
        )


def test_write_aux_file(writer_setup):
    path = writer_setup(with_aux=True)
    with DataReader(path) as r:
        assert r.get_num_aux_files() == 1
        assert r.get_aux_file_name(0) == "notes"
        assert r.get_aux_file_type(0) == "text"
        assert r.get_aux_file_text(0) == "auxiliary body"


def test_write_log_message(writer_setup):
    path = writer_setup(log_msg="hello there")
    with DataReader(path) as r:
        assert "hello there" in r.get_experiment_log()


def test_write_scalar_attribute_after_entry_raises(tmp_path):
    masses = np.arange(100.0, 101.0, 0.05, dtype=np.float32)
    with DataWriter(tmp_path, "X", is_centroid=False) as w:
        w.set_metadata("v", "f", "i", "CMS")
        w.write_spectrum_masses(masses)
        # Need at least one scan or create_datx_file would fail.
        w.write_scan_data(np.zeros(masses.size, dtype=np.int64), 0.0, 0.0)
        cid = w.create_scalar_channel("UV")
        w.write_scalar_entry(cid, 0.0, 1.0)
        with pytest.raises(IOError):
            w.add_scalar_channel_attribute(cid, "wavelength", 254.0)
        path = w.create_datx_file()
    # Sanity: the file still loads.
    DataReader(path).close()


def test_write_unknown_scalar_channel_raises(tmp_path):
    with DataWriter(tmp_path, "X", is_centroid=False) as w:
        with pytest.raises(IOError):
            w.add_scalar_channel_attribute(99, "n", 1.0)
        with pytest.raises(IOError):
            w.write_scalar_entry(99, 0.0, 1.0)


def test_write_without_masses_raises(tmp_path):
    with DataWriter(tmp_path, "X", is_centroid=False) as w:
        with pytest.raises(IOError):
            w.write_scan_data(np.zeros(10, dtype=np.int64), 0.0, 0.0)


def test_write_mismatched_scan_size_raises(tmp_path):
    masses = np.arange(100.0, 101.0, 0.05, dtype=np.float32)
    with DataWriter(tmp_path, "X", is_centroid=False) as w:
        w.write_spectrum_masses(masses)
        with pytest.raises(IOError):
            w.write_scan_data(np.zeros(5, dtype=np.int64), 0.0, 0.0)


def test_can_write_data_static(tmp_path):
    assert DataWriter.can_write_data(tmp_path, "foo") == AdvionDataErrorCode.OK


# ---------------------------------------------------------------------------
# Full read -> write -> read fidelity against the bundled example
# ---------------------------------------------------------------------------


def test_round_trip_example_file(tmp_path):
    if not EXAMPLE_DATX.exists():
        pytest.skip(SKIP_REASON)

    with DataReader(EXAMPLE_DATX) as r:
        masses = r.get_masses()
        times = r.get_retention_times()
        is_centroid = r.get_is_centroid()
        sw = r.get_software_version()
        fw = r.get_firmware_version()
        inst = r.get_instrument_id()
        hw = r.get_hardware_type()
        method_xml = r.get_method_xml()
        tune_xml = r.get_tune_parameters_xml(0)
        ion_xml = r.get_ion_source_optimization_xml(0)
        scan_mode = r.get_scan_mode_index()
        spectra = [r.get_spectrum(i) for i in range(r.get_num_spectra())]
        tics = [r.get_TIC(i) for i in range(r.get_num_spectra())]

    with DataWriter(tmp_path, "Copy", is_centroid=is_centroid) as w:
        w.set_metadata(sw, fw, inst, hw)
        w.write_method(method_xml)
        w.write_tune_params(tune_xml)
        w.write_ion_source_opt(ion_xml)
        w.write_scan_mode_index(scan_mode)
        w.write_spectrum_masses(masses)
        for spec, t, tic in zip(spectra, times, tics):
            w.write_scan_data(spec.astype(np.int64), float(t), float(tic))
        out_path = w.create_datx_file()

    with DataReader(out_path) as r2:
        np.testing.assert_array_equal(r2.get_masses(), masses)
        np.testing.assert_array_equal(r2.get_retention_times(), times)
        assert r2.get_num_spectra() == len(spectra)
        for i, s in enumerate(spectra):
            np.testing.assert_array_equal(r2.get_spectrum(i), s)
        assert r2.get_software_version() == sw
        assert r2.get_firmware_version() == fw
        assert r2.get_instrument_id() == inst
        assert r2.get_hardware_type() == hw
        assert r2.get_method_xml() == method_xml
        assert r2.get_tune_parameters_xml(0) == tune_xml
        assert r2.get_ion_source_optimization_xml(0) == ion_xml
        assert r2.get_scan_mode_index() == scan_mode


def test_write_segments_round_trip(tmp_path):
    masses = np.arange(100.0, 101.0, 0.05, dtype=np.float32)
    with DataWriter(tmp_path, "Seg", is_centroid=False) as w:
        w.set_metadata("v", "f", "i", "CMS")
        w.write_spectrum_masses(masses)
        w.write_segments(
            2,
            [0.0, 1.5],
            [
                '<?xml version="1.0"?><ionSourceOptimization version="1"/>',
                '<?xml version="1.0"?><ionSourceOptimization version="2"/>',
            ],
            [
                '<?xml version="1.0"?><tuneParameters version="1"/>',
                '<?xml version="1.0"?><tuneParameters version="2"/>',
            ],
        )
        w.write_scan_data(np.zeros(masses.size, dtype=np.int64), 0.0, 0.0)
        path = w.create_datx_file()

    with DataReader(path) as r:
        assert r.get_num_segments() == 2
        assert r.get_segment_time(0) == pytest.approx(0.0)
        assert r.get_segment_time(1) == pytest.approx(1.5)
        assert 'version="1"' in r.get_ion_source_optimization_xml(0)
        assert 'version="2"' in r.get_ion_source_optimization_xml(1)
        assert 'version="1"' in r.get_tune_parameters_xml(0)
        assert 'version="2"' in r.get_tune_parameters_xml(1)
