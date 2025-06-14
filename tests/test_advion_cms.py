"""Comprehensive tests for AdvionCMS instrument control functionality."""
import pytest

from advion_io.advion_cms import (
    USBInstrument, SimulatedInstrument, 
    AdvionInstrumentController
)
from advion_io.constants import (
    AdvionCMSErrorCode, InstrumentState, OperationMode,
    TuneParameter, InstrumentSwitch, BinaryReadback, NumberReadback
)


class TestInstrumentInstantiation:
    """Test instrument creation and basic properties."""
    
    def test_usb_instrument_creation(self, use_real_instrument):
        """Test USBInstrument creation."""
        if use_real_instrument:
            instrument = USBInstrument(auto_startup=True, auto_detect=True)
            assert instrument.handle is not None
        else:
            pytest.skip("Skipping USB instrument test - use --use-real-instrument flag")
    
    def test_simulated_instrument_creation(self, use_real_instrument, sim_config_path):
        """Test SimulatedInstrument creation."""
        if not use_real_instrument:
            instrument = SimulatedInstrument(sim_config_path)
            assert instrument.handle is not None
        else:
            pytest.skip("Skipping simulated instrument test - running with real instrument")
    
    def test_usb_instrument_auto_startup_disabled(self, use_real_instrument):
        """Test USBInstrument with auto_startup disabled."""
        if use_real_instrument:
            instrument = USBInstrument(auto_startup=False, auto_detect=True)
            assert instrument.handle is not None
        else:
            pytest.skip("Skipping USB instrument test - use --use-real-instrument flag")


@pytest.fixture
def instrument(use_real_instrument, sim_config_path):
    """Create appropriate instrument for testing."""
    if use_real_instrument:
        return USBInstrument(auto_startup=True, auto_detect=True)
    else:
        return SimulatedInstrument(sim_config_path)


class TestInstrumentController:
    """Test AdvionInstrumentController static methods."""
    
    def test_controller_lifecycle(self, instrument):
        """Test starting and stopping the instrument controller."""
        # Start controller
        start_result = AdvionInstrumentController.start_controller(instrument)
        assert isinstance(start_result, AdvionCMSErrorCode)
        assert start_result == AdvionCMSErrorCode.CMS_OK
        
        try:
            # Get initial state
            state = AdvionInstrumentController.get_state()
            assert isinstance(state, InstrumentState)
            
            # Get operation mode
            mode = AdvionInstrumentController.get_operation_mode()
            assert isinstance(mode, OperationMode)
            
        finally:
            # Always stop controller
            stop_result = AdvionInstrumentController.stop_controller()
            assert isinstance(stop_result, AdvionCMSErrorCode)
            assert stop_result == AdvionCMSErrorCode.CMS_OK
    
    def test_controller_capabilities(self, instrument):
        """Test controller capability queries."""
        AdvionInstrumentController.start_controller(instrument)
        
        try:
            # Test capability checks
            can_operate = AdvionInstrumentController.can_operate()
            assert isinstance(can_operate, bool)
            
            can_standby = AdvionInstrumentController.can_standby()
            assert isinstance(can_standby, bool)
            
            can_vent = AdvionInstrumentController.can_vent()
            assert isinstance(can_vent, bool)
            
            can_pump_down = AdvionInstrumentController.can_pump_down()
            assert isinstance(can_pump_down, bool)
            
            # Get operate preventers
            preventers = AdvionInstrumentController.get_operate_preventers()
            assert isinstance(preventers, int)
            assert preventers >= 0
            
        finally:
            AdvionInstrumentController.stop_controller()
    
    def test_state_transitions(self, instrument):
        """Test instrument state transitions."""
        AdvionInstrumentController.start_controller(instrument)
        
        try:
            AdvionInstrumentController.get_state()
            
            # Test state transition commands
            if AdvionInstrumentController.can_pump_down():
                result = AdvionInstrumentController.pump_down()
                assert isinstance(result, AdvionCMSErrorCode)
            
            if AdvionInstrumentController.can_standby():
                result = AdvionInstrumentController.standby()
                assert isinstance(result, AdvionCMSErrorCode)
            
            if AdvionInstrumentController.can_operate():
                result = AdvionInstrumentController.operate()
                assert isinstance(result, AdvionCMSErrorCode)
            
            if AdvionInstrumentController.can_vent():
                result = AdvionInstrumentController.vent()
                assert isinstance(result, AdvionCMSErrorCode)
                
        finally:
            AdvionInstrumentController.stop_controller()
    
    def test_software_version(self, instrument):
        """Test getting software version."""
        AdvionInstrumentController.start_controller(instrument)
        
        try:
            version = AdvionInstrumentController.get_software_version()
            assert isinstance(version, str)
            
        finally:
            AdvionInstrumentController.stop_controller()


class TestTuneParameters:
    """Test tune parameter management."""
    
    def test_tune_parameter_xml_operations(self, instrument):
        """Test getting and setting tune parameters via XML."""
        AdvionInstrumentController.start_controller(instrument)
        
        try:
            # Get current tune parameters
            tune_xml = AdvionInstrumentController.get_tune_parameters()
            assert isinstance(tune_xml, str)
            
            # Set tune parameters (should not fail)
            if tune_xml:  # Only test if we got valid XML
                result = AdvionInstrumentController.set_tune_parameters(tune_xml)
                assert isinstance(result, AdvionCMSErrorCode)
                
        finally:
            AdvionInstrumentController.stop_controller()
    
    def test_ion_source_optimization_xml_operations(self, instrument):
        """Test getting and setting ion source optimization via XML."""
        AdvionInstrumentController.start_controller(instrument)
        
        try:
            # Get current ion source optimization
            ion_source_xml = AdvionInstrumentController.get_ion_source_optimization()
            assert isinstance(ion_source_xml, str)
            
            # Set ion source optimization (should not fail)
            if ion_source_xml:  # Only test if we got valid XML
                result = AdvionInstrumentController.set_ion_source_optimization(ion_source_xml)
                assert isinstance(result, AdvionCMSErrorCode)
                
        finally:
            AdvionInstrumentController.stop_controller()


class TestInstrumentMethods:
    """Test individual instrument instance methods."""
    
    def test_binary_readbacks(self, instrument):
        """Test binary readback methods."""
        AdvionInstrumentController.start_controller(instrument)
        
        try:
            # Test a few binary readbacks
            comm_ok = instrument.get_binary_readback(BinaryReadback.CommunicationOK)
            assert isinstance(comm_ok, bool)
            
            fw_ok = instrument.get_binary_readback(BinaryReadback.FirmwareVersionOK)
            assert isinstance(fw_ok, bool)
            
            vacuum_ok = instrument.get_binary_readback(BinaryReadback.VacuumOK)
            assert isinstance(vacuum_ok, bool)
            
        finally:
            AdvionInstrumentController.stop_controller()
    
    def test_number_readbacks(self, instrument):
        """Test numeric readback methods."""
        AdvionInstrumentController.start_controller(instrument)
        
        try:
            # Test a few number readbacks
            pressure = instrument.get_number_readback(NumberReadback.PiraniPressureRB)
            assert isinstance(pressure, float)
            
            turbo_speed = instrument.get_number_readback(NumberReadback.TurboSpeedRB)
            assert isinstance(turbo_speed, float)
            
            cap_temp = instrument.get_number_readback(NumberReadback.CapillaryTemperatureRB)
            assert isinstance(cap_temp, float)
            
        finally:
            AdvionInstrumentController.stop_controller()
    
    def test_tune_parameter_operations(self, instrument):
        """Test individual tune parameter get/set operations."""
        AdvionInstrumentController.start_controller(instrument)
        
        try:
            # Test getting tune parameters
            cap_temp = instrument.get_tune_parameter(TuneParameter.CapillaryTemperature)
            assert isinstance(cap_temp, float)
            
            cap_voltage = instrument.get_tune_parameter(TuneParameter.CapillaryVoltage)
            assert isinstance(cap_voltage, float)
            
            # Test getting parameter limits
            cap_temp_min = instrument.get_tune_parameter_min(TuneParameter.CapillaryTemperature)
            assert isinstance(cap_temp_min, float)
            
            cap_temp_max = instrument.get_tune_parameter_max(TuneParameter.CapillaryTemperature)
            assert isinstance(cap_temp_max, float)
            assert cap_temp_max >= cap_temp_min
            
            # Test setting tune parameter (use current value to be safe)
            instrument.set_tune_parameter(TuneParameter.CapillaryTemperature, cap_temp)
            
        finally:
            AdvionInstrumentController.stop_controller()
    
    def test_instrument_switches(self, instrument):
        """Test instrument switch operations."""
        AdvionInstrumentController.start_controller(instrument)
        
        try:
            # Test setting some switches (use safe defaults)
            instrument.set_instrument_switch(InstrumentSwitch.PositiveIon, True)
            instrument.set_instrument_switch(InstrumentSwitch.CapillaryHeater, False)
            instrument.set_instrument_switch(InstrumentSwitch.SourceGasHeater, False)
            
        finally:
            AdvionInstrumentController.stop_controller()
    
    def test_instrument_info_methods(self, instrument):
        """Test instrument information methods."""
        AdvionInstrumentController.start_controller(instrument)
        
        try:
            # Test firmware version
            fw_version = instrument.get_firmware_version()
            assert isinstance(fw_version, str)
            
            # Test serial number
            serial = instrument.get_serial_number()
            assert isinstance(serial, str)
            
            # Test mass range
            min_mass = instrument.get_min_mass()
            assert isinstance(min_mass, float)
            assert min_mass > 0
            
            max_mass = instrument.get_max_mass()
            assert isinstance(max_mass, float)
            assert max_mass > min_mass
            
            # Test max scan speed
            max_scan_speed = instrument.get_max_scan_speed()
            assert isinstance(max_scan_speed, float)
            assert max_scan_speed > 0
            
        finally:
            AdvionInstrumentController.stop_controller()
    
    def test_pump_down_remaining_seconds(self, instrument):
        """Test pump down timing."""
        AdvionInstrumentController.start_controller(instrument)
        
        try:
            remaining = instrument.get_pump_down_remaining_seconds()
            assert isinstance(remaining, int)
            assert remaining >= 0
            
        finally:
            AdvionInstrumentController.stop_controller()
    
    def test_analog_input_reading(self, instrument):
        """Test analog input reading."""
        AdvionInstrumentController.start_controller(instrument)
        
        try:
            # Test reading analog inputs (typically 0-3)
            for line in range(4):
                value = instrument.read_analog_input(line)
                assert isinstance(value, float)
                # Analog inputs are typically 0-5V or similar
                assert 0.0 <= value <= 10.0
                
        finally:
            AdvionInstrumentController.stop_controller()


class TestErrorScenarios:
    """Test error handling and edge cases."""
    
    def test_controller_not_started_error(self):
        """Test operations when controller is not started."""
        # These should fail because controller is not started
        state = AdvionInstrumentController.get_state()
        # The actual behavior depends on the DLL implementation
        # It might return a specific error state or raise an exception
        assert isinstance(state, InstrumentState)
    
    def test_double_start_controller(self, instrument):
        """Test starting controller twice."""
        result1 = AdvionInstrumentController.start_controller(instrument)
        assert isinstance(result1, AdvionCMSErrorCode)
        
        try:
            # Second start should return an error or be handled gracefully
            result2 = AdvionInstrumentController.start_controller(instrument)
            assert isinstance(result2, AdvionCMSErrorCode)
            
        finally:
            AdvionInstrumentController.stop_controller()
    
    def test_invalid_tune_parameter_values(self, instrument):
        """Test setting invalid tune parameter values."""
        AdvionInstrumentController.start_controller(instrument)
        
        try:
            # Get valid range for capillary temperature
            min_temp = instrument.get_tune_parameter_min(TuneParameter.CapillaryTemperature)
            max_temp = instrument.get_tune_parameter_max(TuneParameter.CapillaryTemperature)
            
            # Try setting value below minimum (should be handled gracefully)
            instrument.set_tune_parameter(TuneParameter.CapillaryTemperature, min_temp - 100)
            
            # Try setting value above maximum (should be handled gracefully)
            instrument.set_tune_parameter(TuneParameter.CapillaryTemperature, max_temp + 100)
            
            # Verify current value is still within valid range
            current_temp = instrument.get_tune_parameter(TuneParameter.CapillaryTemperature)
            assert min_temp <= current_temp <= max_temp
            
        finally:
            AdvionInstrumentController.stop_controller()


class TestEnumValues:
    """Test enum constants and their values."""
    
    def test_instrument_state_enum(self):
        """Test InstrumentState enum values."""
        assert InstrumentState.Fault == 0
        assert InstrumentState.Initializing == 1
        assert InstrumentState.Vented == 2
        assert InstrumentState.PumpingDown == 3
        assert InstrumentState.Standby == 4
        assert InstrumentState.Operate == 5
    
    def test_operation_mode_enum(self):
        """Test OperationMode enum values."""
        assert OperationMode.Idle == 0
        assert OperationMode.Tuning == 1
        assert OperationMode.AutoTuning == 2
        assert OperationMode.Acquiring == 3
    
    def test_tune_parameter_enum(self):
        """Test TuneParameter enum values."""
        assert TuneParameter.CapillaryTemperature == 0
        assert TuneParameter.CapillaryVoltage == 1
        assert TuneParameter.SourceGasTemperature == 2
        assert TuneParameter.DetectorVoltage == 16
    
    def test_instrument_switch_enum(self):
        """Test InstrumentSwitch enum values."""
        assert InstrumentSwitch.PositiveIon == 0
        assert InstrumentSwitch.FullNebulizationGas == 1
        assert InstrumentSwitch.UsingHelium == 9
    
    def test_binary_readback_enum(self):
        """Test BinaryReadback enum values."""
        assert BinaryReadback.CommunicationOK == 0
        assert BinaryReadback.FirmwareVersionOK == 1
        assert BinaryReadback.UsingHeliumRB == 21
    
    def test_number_readback_enum(self):
        """Test NumberReadback enum values."""
        assert NumberReadback.PiraniPressureRB == 0
        assert NumberReadback.TurboSpeedRB == 1
        assert NumberReadback.DC2RB == 17


class TestAdvionCMSErrorCodes:
    """Test error code handling."""
    
    def test_error_code_enum_values(self):
        """Test AdvionCMSErrorCode enum values."""
        assert AdvionCMSErrorCode.CMS_OK == 0
        assert AdvionCMSErrorCode.CMS_NO_USB_CONNECTION == 1
        assert AdvionCMSErrorCode.CMS_USB_CONNECTED == 2
        assert AdvionCMSErrorCode.CMS_CONTROLLER_ALREADY_STARTED == 40
        assert AdvionCMSErrorCode.CMS_NOT_SUPPORTED == 84
    
    def test_error_code_instantiation(self):
        """Test creating AdvionCMSErrorCode instances."""
        ok_code = AdvionCMSErrorCode(0)
        assert ok_code == AdvionCMSErrorCode.CMS_OK
        
        usb_error = AdvionCMSErrorCode(1)
        assert usb_error == AdvionCMSErrorCode.CMS_NO_USB_CONNECTION


class TestInstrumentCleanup:
    """Test proper cleanup and destructor behavior."""
    
    def test_usb_instrument_cleanup(self, use_real_instrument):
        """Test USBInstrument cleanup."""
        if use_real_instrument:
            instrument = USBInstrument()
            # Cleanup should happen automatically when instrument goes out of scope
            del instrument
        else:
            pytest.skip("Skipping USB instrument test - use --use-real-instrument flag")
    
    def test_simulated_instrument_cleanup(self, use_real_instrument, sim_config_path):
        """Test SimulatedInstrument cleanup."""
        if not use_real_instrument:
            instrument = SimulatedInstrument(sim_config_path)
            # Cleanup should happen automatically when instrument goes out of scope
            del instrument
        else:
            pytest.skip("Skipping simulated instrument test - running with real instrument")


class TestInstrumentControllerIntegration:
    """Integration tests for complete instrument control workflows."""
    
    def test_complete_startup_shutdown_cycle(self, instrument):
        """Test complete instrument startup and shutdown."""
        # Start controller
        start_result = AdvionInstrumentController.start_controller(instrument)
        assert start_result == AdvionCMSErrorCode.CMS_OK
        
        try:
            # Check initial state
            initial_state = AdvionInstrumentController.get_state()
            assert isinstance(initial_state, InstrumentState)
            
            # If we can pump down, do the full cycle
            if AdvionInstrumentController.can_pump_down():
                # Pump down
                pump_result = AdvionInstrumentController.pump_down()
                assert isinstance(pump_result, AdvionCMSErrorCode)
                
                # Wait a moment then check if we can standby
                if AdvionInstrumentController.can_standby():
                    standby_result = AdvionInstrumentController.standby()  
                    assert isinstance(standby_result, AdvionCMSErrorCode)
                    
                    # Check if we can operate
                    if AdvionInstrumentController.can_operate():
                        operate_result = AdvionInstrumentController.operate()
                        assert isinstance(operate_result, AdvionCMSErrorCode)
                        
                        # Verify we're operating
                        operating_state = AdvionInstrumentController.get_state()
                        # State might be Operate or might take time to transition
                        assert isinstance(operating_state, InstrumentState)
            
        finally:
            # Always stop controller
            stop_result = AdvionInstrumentController.stop_controller()
            assert stop_result == AdvionCMSErrorCode.CMS_OK
    
    def test_tune_parameter_workflow(self, instrument):
        """Test a complete tune parameter adjustment workflow."""
        AdvionInstrumentController.start_controller(instrument)
        
        try:
            # Get current capillary temperature settings
            current_temp = instrument.get_tune_parameter(TuneParameter.CapillaryTemperature)
            min_temp = instrument.get_tune_parameter_min(TuneParameter.CapillaryTemperature)
            max_temp = instrument.get_tune_parameter_max(TuneParameter.CapillaryTemperature)
            
            # Verify current temp is within valid range
            assert min_temp <= current_temp <= max_temp
            
            # Set to midpoint of range if different from current
            midpoint = (min_temp + max_temp) / 2
            if abs(current_temp - midpoint) > 1.0:  # Only if significantly different
                instrument.set_tune_parameter(TuneParameter.CapillaryTemperature, midpoint)
                
                # Verify the change (might take time to take effect)
                new_temp = instrument.get_tune_parameter(TuneParameter.CapillaryTemperature)
                assert isinstance(new_temp, float)
            
        finally:
            AdvionInstrumentController.stop_controller()