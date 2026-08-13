"""Tests for the pure-Python ``DataReader``.

These tests exercise every method on the bundled example acquisition.
They need no vendor libraries and run on Linux, macOS and Windows.
"""
from __future__ import annotations

import gzip
import pickle
from pathlib import Path

import numpy as np
import pytest

from advion_io import DataReader
from advion_io.constants import AdvionDataErrorCode
from example_data import EXAMPLE_DATX, SKIP_REASON, requires_example


@pytest.fixture(scope="module")
def dr():
    if not EXAMPLE_DATX.exists():
        pytest.skip(SKIP_REASON)
    with DataReader(EXAMPLE_DATX) as r:
        yield r


# ---------------------------------------------------------------------------
# Initialisation / validity
# ---------------------------------------------------------------------------


@requires_example
def test_init_accepts_bytes_and_str():
    DataReader(str(EXAMPLE_DATX)).close()
    DataReader(bytes(str(EXAMPLE_DATX), "utf-8")).close()


@requires_example
def test_init_accepts_decode_spectra_eager():
    # The flag is accepted and triggers eager decode; result must still
    # be correct.
    with DataReader(EXAMPLE_DATX, debug_output=False, decode_spectra=True) as r:
        assert r.get_num_spectra() > 0
        np.testing.assert_array_equal(r.get_spectrum(0), r.get_spectrum(0))


def test_get_data_set_validity_ok(dr):
    dr.get_data_set_validity()  # should not raise


# ---------------------------------------------------------------------------
# Basic shape / metadata
# ---------------------------------------------------------------------------


def test_basic_counts(dr):
    assert dr.get_num_masses() == 11999
    assert dr.get_num_spectra() == 137


def test_metadata_strings(dr):
    assert dr.get_date() == "2026.05.07 14:36:10"
    assert dr.get_software_version() == "7.0.5.4"
    assert dr.get_firmware_version() == "VERSION191001A-V3"
    assert dr.get_hardware_type() == "CMS-L"
    assert dr.get_instrument_id() == "CMS-0000-0000"
    assert dr.get_is_centroid() is False


def test_scan_mode_and_segments(dr):
    assert dr.get_scan_mode_index() == 0
    assert dr.get_num_segments() == 1
    assert dr.get_segment_time(0) == 0.0
    # Out-of-range returns 0.0 per the C++ contract.
    assert dr.get_segment_time(1) == 0.0
    assert dr.get_segment_time(-1) == 0.0


# ---------------------------------------------------------------------------
# Mass / time / spectrum
# ---------------------------------------------------------------------------


def test_masses_and_times(dr):
    masses = dr.get_masses()
    assert masses.dtype == np.float32
    assert masses.shape == (dr.get_num_masses(),)
    assert masses[0] == pytest.approx(99.9, abs=1e-3)

    times = dr.get_retention_times()
    assert times.dtype == np.float32
    assert times.shape == (dr.get_num_spectra(),)
    assert np.all(np.diff(times) > 0)


def test_get_TIC_matches_index(dr):
    expected = dr.get_TIC(0)
    assert expected == pytest.approx(3285908170.2841, rel=1e-9)


def test_get_TIC_out_of_range(dr):
    with pytest.raises(IndexError):
        dr.get_TIC(dr.get_num_spectra())
    with pytest.raises(IndexError):
        dr.get_TIC(-1)


def test_get_spectrum_shape_and_dtype(dr):
    spec = dr.get_spectrum(0)
    assert spec.dtype == np.float32
    assert spec.shape == (dr.get_num_masses(),)
    assert np.all(spec >= 0)


def test_get_spectrum_index_bounds(dr):
    with pytest.raises(IndexError):
        dr.get_spectrum(-1)
    with pytest.raises(IndexError):
        dr.get_spectrum(dr.get_num_spectra())


def test_get_averaged_spectrum_matches_manual(dr):
    avg = dr.get_averaged_spectrum([0, 5, 10])
    manual = (
        dr.get_spectrum(0).astype(np.float64)
        + dr.get_spectrum(5).astype(np.float64)
        + dr.get_spectrum(10).astype(np.float64)
    ) / 3.0
    np.testing.assert_allclose(avg, manual, rtol=1e-6, atol=1e-3)


def test_get_averaged_spectrum_empty(dr):
    with pytest.raises(IOError):
        dr.get_averaged_spectrum([])


# ---------------------------------------------------------------------------
# XIC
# ---------------------------------------------------------------------------


def test_generate_xic(dr):
    xic = dr.generate_xic([0, 100, 200])
    assert xic.dtype == np.float32
    assert xic.shape == (dr.get_num_spectra(),)
    # Spot-check: sum equals sum of those columns across the full matrix.
    expected = sum(
        dr.get_spectrum(i)[[0, 100, 200]].sum() for i in range(dr.get_num_spectra())
    )
    assert float(xic.sum()) == pytest.approx(expected, rel=1e-6)


def test_generate_xic_mass_index_bounds(dr):
    with pytest.raises(IndexError):
        dr.generate_xic([dr.get_num_masses()])


# ---------------------------------------------------------------------------
# Peak Express delta
# ---------------------------------------------------------------------------


def test_set_delta_background_parameter_validation(dr):
    with pytest.raises(IOError):
        dr.set_delta_background_parameters(-1.0, 1.0, 3.0, 0.4, 0)
    with pytest.raises(IOError):
        dr.set_delta_background_parameters(0.0, 0.0, 3.0, 0.4, 0)
    with pytest.raises(IOError):
        dr.set_delta_background_parameters(0.0, 1.0, 0.5, 0.4, 0)
    with pytest.raises(IOError):
        dr.set_delta_background_parameters(0.0, 1.0, 3.0, 0.01, 0)
    # Valid call goes through.
    dr.set_delta_background_parameters(0.0, 10.0, 3.0, 0.4, 1_000_000)


def test_delta_background_and_delta_spectrum(dr):
    dr.set_delta_background_parameters(0.0, 10.0, 3.0, 0.4, 1_000_000)
    bg = dr.get_delta_background_spectrum()
    assert bg.shape == (dr.get_num_masses(),)
    assert bg.dtype == np.float32
    # noiseOffset is added everywhere => background >= noiseOffset.
    assert bg.min() >= 1_000_000

    # delta = (raw - bg) / bg, thresholded; for an in-background scan
    # everything should be zero.
    delta0 = dr.get_delta_spectrum(0)
    assert delta0.dtype == np.float32
    assert float(delta0.max()) == 0.0
    assert dr.get_delta_ic(0) == pytest.approx(0.0)


def test_delta_min_width_filters_narrow_peaks(dr):
    # Strict threshold + huge min_width should kill everything.
    dr.set_delta_background_parameters(0.0, 5.0, 3.0, 100.0, 0)
    for i in range(dr.get_num_spectra()):
        assert float(dr.get_delta_spectrum(i).max()) == 0.0


def test_delta_xic_and_averaged_delta(dr):
    dr.set_delta_background_parameters(0.0, 10.0, 3.0, 0.4, 1_000_000)
    xic = dr.generate_delta_xic([100, 200, 300])
    assert xic.dtype == np.float32
    assert xic.shape == (dr.get_num_spectra(),)

    avg = dr.get_averaged_delta_spectrum([0, 1, 2])
    assert avg.shape == (dr.get_num_masses(),)
    assert avg.dtype == np.float32


# ---------------------------------------------------------------------------
# XML accessors
# ---------------------------------------------------------------------------


def test_xml_accessors(dr):
    assert "<method" in dr.get_method_xml()
    assert "<tuneParameters" in dr.get_tune_parameters_xml()
    assert "<ionSourceOptimization" in dr.get_ion_source_optimization_xml()
    # Older datasets don't have an experiment / ICP-MS section; ours
    # returns "" rather than raising.
    assert dr.get_experiment_xml() == ""
    assert dr.get_icpms_experiment_xml() == ""
    assert dr.get_icpms_instrument_settings_xml() == ""
    assert "Acquisition begins" in dr.get_experiment_log()


# ---------------------------------------------------------------------------
# Scalar channels / aux files
# ---------------------------------------------------------------------------


def test_scalar_channels(dr):
    assert dr.get_num_scalar_channels() == 1
    assert dr.get_scalar_channel_name(0) == "DeconTIC"
    # No entries in this example: the .scalar file is just a header.
    assert dr.get_scalar_channel_num_samples(0) == 0
    assert dr.get_scalar_channel_num_attributes(0) == 0
    # Out-of-range queries follow the C++ contract: name "", samples 0,
    # nattr -1, times/values raise.
    assert dr.get_scalar_channel_name(99) == ""
    assert dr.get_scalar_channel_num_samples(99) == 0
    assert dr.get_scalar_channel_num_attributes(99) == -1
    with pytest.raises(IOError):
        dr.get_scalar_channel_times(99)
    with pytest.raises(IOError):
        dr.get_scalar_channel_values(99)


def test_aux_files_absent(dr):
    # Bundled example has no aux files.
    assert dr.get_num_aux_files() == 0
    assert dr.get_aux_file_name(0) == ""
    assert dr.get_aux_file_type(0) == ""
    assert dr.get_aux_file_text(0) == ""


# ---------------------------------------------------------------------------
# Save round-trip
# ---------------------------------------------------------------------------


def test_save_round_trip(dr, tmp_path):
    out = tmp_path / "saved.pkgz"
    dr.save(out)
    with gzip.open(out, "rb") as gz:
        payload = pickle.load(gz)
    assert set(payload) == {"masses", "times", "intensities"}
    assert payload["masses"].shape == (dr.get_num_masses(),)
    assert payload["times"].shape == (dr.get_num_spectra(),)
    assert payload["intensities"].shape == (
        dr.get_num_spectra(),
        dr.get_num_masses(),
    )
    np.testing.assert_array_equal(payload["intensities"][0], dr.get_spectrum(0))


# ---------------------------------------------------------------------------
# Cross-check against the lower-level DatxFile (regression / consistency)
# ---------------------------------------------------------------------------


def test_synthetic_scalar_channel_parsing(tmp_path):
    """Mixed attribute-style and element-style scalar entries parse correctly."""
    import io
    import struct
    import zipfile

    path = tmp_path / "synth.datx"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(
            "x/x.scans",
            '<?xml version="1.0"?><scans version="1.1">'
            "<dataType>continuum</dataType><samplesPerScan>4</samplesPerScan>"
            "<storeAsFloat>false</storeAsFloat></scans>",
        )
        z.writestr("x/x.masses", struct.pack("<4f", 100.0, 100.05, 100.1, 100.15))
        z.writestr("x/x.spectra", b"")
        z.writestr(
            "x/x.0.scalar",
            """<?xml version="1.0"?>
<scalarChannel version="1.0">
  <name>Pressure</name>
  <attribute><name>gain</name><value>1.5</value></attribute>
  <attribute name="offset" value="-0.2"/>
  <entry><time>0.10</time><value>1.0</value></entry>
  <entry time="0.20" value="2.5"/>
</scalarChannel>
""",
        )
    with DataReader(path) as r:
        assert r.get_num_scalar_channels() == 1
        assert r.get_scalar_channel_name(0) == "Pressure"
        assert r.get_scalar_channel_num_samples(0) == 2
        assert r.get_scalar_channel_num_attributes(0) == 2
        assert r.get_scalar_channel_attribute_name(0, 0) == "gain"
        assert r.get_scalar_channel_attribute_value(0, 0) == pytest.approx(1.5)
        assert r.get_scalar_channel_attribute_name(0, 1) == "offset"
        assert r.get_scalar_channel_attribute_value(0, 1) == pytest.approx(-0.2)
        np.testing.assert_allclose(
            r.get_scalar_channel_times(0), np.array([0.1, 0.2], dtype=np.float32)
        )
        np.testing.assert_allclose(
            r.get_scalar_channel_values(0), np.array([1.0, 2.5], dtype=np.float32)
        )


def test_synthetic_aux_files_parsing(tmp_path):
    """`auxfiles` index + per-file bodies + isHTML→type rewriting."""
    import struct
    import zipfile

    path = tmp_path / "aux.datx"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(
            "y/y.scans",
            '<?xml version="1.0"?><scans version="1.1">'
            "<dataType>continuum</dataType><samplesPerScan>1</samplesPerScan>"
            "<storeAsFloat>false</storeAsFloat></scans>",
        )
        z.writestr("y/y.masses", struct.pack("<f", 100.0))
        z.writestr("y/y.spectra", b"")
        z.writestr(
            "y/auxfiles",
            '<?xml version="1.0"?><auxFiles>'
            "<file><name>foo</name><type>text</type><isHTML>false</isHTML></file>"
            "<file><name>bar</name><type>text</type><isHTML>true</isHTML></file>"
            "</auxFiles>",
        )
        z.writestr("y/foo", "plain text body")
        z.writestr("y/bar", "<html><body>hi</body></html>")
    with DataReader(path) as r:
        assert r.get_num_aux_files() == 2
        assert r.get_aux_file_name(0) == "foo"
        assert r.get_aux_file_type(0) == "text"
        assert r.get_aux_file_text(0) == "plain text body"
        assert r.get_aux_file_name(1) == "bar"
        assert r.get_aux_file_type(1) == "text/html"
        assert r.get_aux_file_text(1) == "<html><body>hi</body></html>"


def test_consistency_with_datx_reader(dr):
    from advion_io import DatxFile

    with DatxFile(EXAMPLE_DATX) as dx:
        np.testing.assert_array_equal(dr.get_masses(), dx.masses)
        np.testing.assert_array_equal(dr.get_retention_times(), dx.retention_times)
        for i in (0, dr.get_num_spectra() // 2, dr.get_num_spectra() - 1):
            np.testing.assert_array_equal(dr.get_spectrum(i), dx.get_spectrum(i))
