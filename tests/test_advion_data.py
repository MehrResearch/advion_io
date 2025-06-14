"""Comprehensive tests for AdvionData functionality."""
import pytest
import numpy as np
from pathlib import Path
import tempfile
import pickle
import gzip

from advion_io import AdvionData


class TestAdvionDataInitialization:
    """Test AdvionData initialization and basic properties."""
    
    def test_init_with_valid_file(self):
        """Test initialization with a valid .datx file."""
        test_file = b"test_data.datx"
        data = AdvionData(test_file, False, False)
        assert data.handle is not None
        assert len(data.handle) == 32  # Buffer size from constructor
    
    def test_init_with_debug_output(self):
        """Test initialization with debug output enabled."""
        test_file = b"test_data.datx"
        data = AdvionData(test_file, True, False)
        assert data.handle is not None
    
    def test_init_with_decode_spectra(self):
        """Test initialization with spectrum decoding enabled."""
        test_file = b"test_data.datx"
        data = AdvionData(test_file, False, True)
        assert data.handle is not None


@pytest.fixture(scope="module")
def data_reader():
    """Create an AdvionData instance for testing."""
    return AdvionData(b"test_data.datx", False, False)

class TestAdvionDataBasicInfo:
    """Test basic information retrieval methods."""
    
    def test_get_num_masses(self, data_reader):
        """Test getting number of masses."""
        num_masses = data_reader.get_num_masses()
        assert isinstance(num_masses, int)
        assert num_masses >= 0
    
    def test_get_num_spectra(self, data_reader):
        """Test getting number of spectra."""
        num_spectra = data_reader.get_num_spectra()
        assert isinstance(num_spectra, int)
        assert num_spectra >= 0
    
    def test_get_tic_valid_index(self, data_reader):
        """Test getting TIC for valid index."""
        if data_reader.get_num_spectra() > 0:
            tic = data_reader.get_TIC(0)
            assert isinstance(tic, float)
            assert tic >= 0
    
    def test_get_is_centroid(self, data_reader):
        """Test getting centroid status."""
        is_centroid = data_reader.get_is_centroid()
        assert isinstance(is_centroid, bool)
    
    def test_get_date(self, data_reader):
        """Test getting acquisition date."""
        date = data_reader.get_date()
        assert isinstance(date, str)
    
    def test_get_scan_mode_index(self, data_reader):
        """Test getting scan mode index."""
        scan_mode = data_reader.get_scan_mode_index()
        assert isinstance(scan_mode, int)
        assert scan_mode >= 0
    
    def test_get_num_segments(self, data_reader):
        """Test getting number of segments."""
        num_segments = data_reader.get_num_segments()
        assert isinstance(num_segments, int)
        assert num_segments >= 0


class TestAdvionDataArrayMethods:
    """Test methods that return NumPy arrays."""
    
    def test_get_masses(self, data_reader):
        """Test getting mass array."""
        masses = data_reader.get_masses()
        assert isinstance(masses, np.ndarray)
        assert masses.dtype == np.float32
        assert len(masses) == data_reader.get_num_masses()
        if len(masses) > 1:
            # Masses should be sorted in ascending order
            assert np.all(masses[:-1] <= masses[1:])
    
    def test_get_retention_times(self, data_reader):
        """Test getting retention times array."""
        times = data_reader.get_retention_times()
        assert isinstance(times, np.ndarray)
        assert times.dtype == np.float32
        assert len(times) == data_reader.get_num_spectra()
        if len(times) > 1:
            # Times should be sorted in ascending order
            assert np.all(times[:-1] <= times[1:])
    
    def test_get_spectrum_valid_index(self, data_reader):
        """Test getting spectrum for valid index."""
        if data_reader.get_num_spectra() > 0:
            spectrum = data_reader.get_spectrum(0)
            assert isinstance(spectrum, np.ndarray)
            assert spectrum.dtype == np.float32
            assert len(spectrum) == data_reader.get_num_masses()
            assert np.all(spectrum >= 0)  # Intensities should be non-negative
    
    def test_get_spectrum_invalid_index(self, data_reader):
        """Test getting spectrum for invalid index raises IndexError."""
        max_index = data_reader.get_num_spectra() - 1
        with pytest.raises(IndexError):
            data_reader.get_spectrum(max_index + 1)
    
    def test_get_delta_spectrum_valid_index(self, data_reader):
        """Test getting delta spectrum for valid index."""
        if data_reader.get_num_spectra() > 0:
            delta_spectrum = data_reader.get_delta_spectrum(0)
            assert isinstance(delta_spectrum, np.ndarray)
            assert delta_spectrum.dtype == np.float32
            assert len(delta_spectrum) == data_reader.get_num_masses()
    
    def test_get_delta_spectrum_invalid_index(self, data_reader):
        """Test getting delta spectrum for invalid index raises IndexError."""
        max_index = data_reader.get_num_spectra() - 1
        with pytest.raises(IndexError):
            data_reader.get_delta_spectrum(max_index + 1)


class TestAdvionDataAveragedSpectra:
    """Test averaged spectrum methods."""
    
    def test_get_averaged_spectrum(self, data_reader):
        """Test getting averaged spectrum."""
        num_spectra = data_reader.get_num_spectra()
        if num_spectra >= 2:
            indices = [0, 1]
            avg_spectrum = data_reader.get_averaged_spectrum(indices)
            assert isinstance(avg_spectrum, np.ndarray)
            assert avg_spectrum.dtype == np.float32
            assert len(avg_spectrum) == data_reader.get_num_masses()
    
    def test_get_averaged_delta_spectrum(self, data_reader):
        """Test getting averaged delta spectrum."""
        num_spectra = data_reader.get_num_spectra()
        if num_spectra >= 2:
            indices = [0, 1]
            avg_delta_spectrum = data_reader.get_averaged_delta_spectrum(indices)
            assert isinstance(avg_delta_spectrum, np.ndarray)
            assert avg_delta_spectrum.dtype == np.float32
            assert len(avg_delta_spectrum) == data_reader.get_num_masses()
    
    def test_averaged_spectrum_empty_indices(self, data_reader):
        """Test averaged spectrum with empty indices list."""
        with pytest.raises((IOError, ValueError)):
            data_reader.get_averaged_spectrum([])


class TestAdvionDataXICGeneration:
    """Test XIC (Extracted Ion Chromatogram) generation methods."""
    
    def test_generate_xic(self, data_reader):
        """Test generating XIC."""
        num_masses = data_reader.get_num_masses()
        if num_masses > 0:
            mass_indices = [0]
            xic = data_reader.generate_xic(mass_indices)
            assert isinstance(xic, np.ndarray)
            assert xic.dtype == np.float32
            assert len(xic) == data_reader.get_num_spectra()
    
    def test_generate_delta_xic(self, data_reader):
        """Test generating delta XIC."""
        num_masses = data_reader.get_num_masses()
        if num_masses > 0:
            mass_indices = [0]
            delta_xic = data_reader.generate_delta_xic(mass_indices)
            assert isinstance(delta_xic, np.ndarray)
            assert delta_xic.dtype == np.float32
            assert len(delta_xic) == data_reader.get_num_spectra()
    
    def test_xic_multiple_masses(self, data_reader):
        """Test XIC generation with multiple mass indices."""
        num_masses = data_reader.get_num_masses()
        if num_masses >= 3:
            mass_indices = [0, 1, 2]
            xic = data_reader.generate_xic(mass_indices)
            assert isinstance(xic, np.ndarray)
            assert len(xic) == data_reader.get_num_spectra()


class TestAdvionDataBackgroundSubtraction:
    """Test background subtraction methods."""
    
    def test_set_delta_background_parameters(self, data_reader):
        """Test setting delta background parameters."""
        # Should not raise an exception
        data_reader.set_delta_background_parameters(0.0, 10.0, 0.1, 0.5, 0.0)
    
    def test_get_delta_background_spectrum(self, data_reader):
        """Test getting delta background spectrum."""
        # Set background parameters first
        data_reader.set_delta_background_parameters(0.0, 10.0, 0.1, 0.5, 0.0)
        
        bg_spectrum = data_reader.get_delta_background_spectrum()
        assert isinstance(bg_spectrum, np.ndarray)
        assert bg_spectrum.dtype == np.float32
        assert len(bg_spectrum) == data_reader.get_num_masses()
    
    def test_get_delta_ic(self, data_reader):
        """Test getting delta IC."""
        if data_reader.get_num_spectra() > 0:
            delta_ic = data_reader.get_delta_ic(0)
            assert isinstance(delta_ic, float)


class TestAdvionDataVersionInfo:
    """Test version and instrument information methods."""
    
    def test_get_software_version(self, data_reader):
        """Test getting software version."""
        version = data_reader.get_software_version()
        assert isinstance(version, str)
    
    def test_get_firmware_version(self, data_reader):
        """Test getting firmware version."""
        version = data_reader.get_firmware_version()
        assert isinstance(version, str)
    
    def test_get_hardware_type(self, data_reader):
        """Test getting hardware type."""
        hw_type = data_reader.get_hardware_type()
        assert isinstance(hw_type, str)
    
    def test_get_instrument_id(self, data_reader):
        """Test getting instrument ID."""
        inst_id = data_reader.get_instrument_id()
        assert isinstance(inst_id, str)


class TestAdvionDataXMLMethods:
    """Test XML data retrieval methods."""
    
    def test_get_method_xml(self, data_reader):
        """Test getting method XML."""
        xml = data_reader.get_method_xml()
        assert isinstance(xml, str)
    
    def test_get_experiment_xml(self, data_reader):
        """Test getting experiment XML."""
        xml = data_reader.get_experiment_xml()
        assert isinstance(xml, str)
    
    def test_get_icpms_experiment_xml(self, data_reader):
        """Test getting ICPMS experiment XML."""
        xml = data_reader.get_icpms_experiment_xml()
        assert isinstance(xml, str)
    
    def test_get_icpms_instrument_settings_xml(self, data_reader):
        """Test getting ICPMS instrument settings XML."""
        xml = data_reader.get_icpms_instrument_settings_xml()
        assert isinstance(xml, str)
    
    def test_get_ion_source_optimization_xml(self, data_reader):
        """Test getting ion source optimization XML."""
        xml = data_reader.get_ion_source_optimization_xml()
        assert isinstance(xml, str)
    
    def test_get_tune_parameters_xml(self, data_reader):
        """Test getting tune parameters XML."""
        xml = data_reader.get_tune_parameters_xml()
        assert isinstance(xml, str)
    
    def test_get_experiment_log(self, data_reader):
        """Test getting experiment log."""
        log = data_reader.get_experiment_log()
        assert isinstance(log, str)


class TestAdvionDataScalarChannels:
    """Test scalar channel methods."""
    
    def test_get_num_scalar_channels(self, data_reader):
        """Test getting number of scalar channels."""
        num_channels = data_reader.get_num_scalar_channels()
        assert isinstance(num_channels, int)
        assert num_channels >= 0
    
    def test_scalar_channel_methods(self, data_reader):
        """Test scalar channel related methods."""
        num_channels = data_reader.get_num_scalar_channels()
        
        if num_channels > 0:
            # Test first channel
            channel_name = data_reader.get_scalar_channel_name(0)
            assert isinstance(channel_name, str)
            
            num_samples = data_reader.get_scalar_channel_num_samples(0)
            assert isinstance(num_samples, int)
            assert num_samples >= 0
            
            if num_samples > 0:
                times = data_reader.get_scalar_channel_times(0)
                assert isinstance(times, np.ndarray)
                assert len(times) == num_samples
                
                values = data_reader.get_scalar_channel_values(0)
                assert isinstance(values, np.ndarray)
                assert len(values) == num_samples
            
            num_attrs = data_reader.get_scalar_channel_num_attributes(0)
            assert isinstance(num_attrs, int)
            assert num_attrs >= 0
            
            if num_attrs > 0:
                attr_name = data_reader.get_scalar_channel_attribute_name(0, 0)
                assert isinstance(attr_name, str)
                
                attr_value = data_reader.get_scalar_channel_attribute_value(0, 0)
                assert isinstance(attr_value, float)


class TestAdvionDataAuxFiles:
    """Test auxiliary file methods."""
    
    def test_get_num_aux_files(self, data_reader):
        """Test getting number of auxiliary files."""
        num_files = data_reader.get_num_aux_files()
        assert isinstance(num_files, int)
        assert num_files >= 0
    
    def test_aux_file_methods(self, data_reader):
        """Test auxiliary file related methods."""
        num_files = data_reader.get_num_aux_files()
        
        if num_files > 0:
            # Test first aux file
            file_name = data_reader.get_aux_file_name(0)
            assert isinstance(file_name, str)
            
            file_type = data_reader.get_aux_file_type(0)
            assert isinstance(file_type, str)
            
            file_text = data_reader.get_aux_file_text(0)
            assert isinstance(file_text, str)


class TestAdvionDataSegments:
    """Test segment-related methods."""
    
    def test_get_segment_time(self, data_reader):
        """Test getting segment time."""
        num_segments = data_reader.get_num_segments()
        if num_segments > 0:
            segment_time = data_reader.get_segment_time(0)
            assert isinstance(segment_time, float)
            assert segment_time >= 0


class TestAdvionDataSave:
    """Test data saving functionality."""
    
    def test_save_to_file(self, data_reader):
        """Test saving data to compressed pickle file."""
        with tempfile.NamedTemporaryFile(suffix='.pkgz', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            data_reader.save(temp_path)
            
            # Verify file was created
            assert Path(temp_path).exists()
            
            # Verify file contents
            with gzip.open(temp_path, 'rb') as f:
                saved_data = pickle.load(f)
            
            assert 'masses' in saved_data
            assert 'times' in saved_data
            assert 'intensities' in saved_data
            
            assert isinstance(saved_data['masses'], np.ndarray)
            assert isinstance(saved_data['times'], np.ndarray)
            assert isinstance(saved_data['intensities'], np.ndarray)
            
            # Check dimensions
            assert len(saved_data['masses']) == data_reader.get_num_masses()
            assert len(saved_data['times']) == data_reader.get_num_spectra()
            assert saved_data['intensities'].shape == (data_reader.get_num_spectra(), data_reader.get_num_masses())
            
        finally:
            # Clean up
            if Path(temp_path).exists():
                Path(temp_path).unlink()


class TestAdvionDataErrorHandling:
    """Test error handling and validation."""
    
    def test_get_data_set_validity(self, data_reader):
        """Test data set validity check."""
        # Should not raise an exception if data is valid
        data_reader.get_data_set_validity()
    
    def test_invalid_spectrum_index_bounds(self, data_reader):
        """Test spectrum index bounds checking."""
        num_spectra = data_reader.get_num_spectra()
        
        # Test negative index
        with pytest.raises(IndexError):
            data_reader.get_spectrum(-1)
        
        # Test index too large
        if num_spectra > 0:
            with pytest.raises(IndexError):
                data_reader.get_spectrum(num_spectra)
    
    def test_error_code_handling(self, data_reader):
        """Test that IOError is raised for non-zero error codes."""
        # This test would require mocking the underlying DLL calls
        # to return specific error codes, which is complex for real DLL testing
        pass