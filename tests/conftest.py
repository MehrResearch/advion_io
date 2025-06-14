"""Pytest configuration and fixtures for advion_io tests."""
import pytest


def pytest_addoption(parser):
    """Add command line options for test configuration."""
    parser.addoption(
        "--use-real-instrument", 
        action="store_true", 
        default=False,
        help="Use real USB instrument instead of simulated instrument"
    )
    parser.addoption(
        "--sim-config", 
        action="store", 
        default="test_instrument.xml",
        help="Path to simulated instrument config file"
    )


@pytest.fixture(scope="session")
def use_real_instrument(request):
    """Fixture to determine if real instrument should be used."""
    return request.config.getoption("--use-real-instrument")


@pytest.fixture(scope="session") 
def sim_config_path(request):
    """Fixture for simulated instrument config path."""
    return request.config.getoption("--sim-config")