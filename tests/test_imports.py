"""
SCORPION Import Tests
=====================

Tests to verify all SCORPION modules can be imported correctly.
Also tests basic functionality of core components.

Run with: pytest tests/test_imports.py -v

Author: SCORPION Commander
Version: 1.0.0 - TESTUDO Formation
"""

import pytest
import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# =============================================================================
# CORE MODULE TESTS
# =============================================================================

class TestCoreImports:
    """Test core module imports."""

    def test_import_core(self):
        """Test core package import."""
        import core
        assert hasattr(core, '__version__')
        assert core.__version__ == "1.0.0"

    def test_import_config(self):
        """Test config module import."""
        from core import config
        assert hasattr(config, 'ScorpionConfig')
        assert hasattr(config, 'get_config')

    def test_import_constants(self):
        """Test constants module import."""
        from core import constants
        assert hasattr(constants, 'PORTS')
        assert hasattr(constants, 'BABIES')
        assert hasattr(constants, 'ACCESS_LEVELS')

    def test_config_defaults(self):
        """Test configuration default values."""
        from core.config import ScorpionConfig
        config = ScorpionConfig()
        assert config.api.port == 8080
        assert config.database.port == 5432
        assert config.redis.port == 6379

    def test_constants_values(self):
        """Test constants have expected values."""
        from core.constants import PORTS, BABIES, ACCESS_LEVELS
        assert PORTS['api'] == 8080
        assert PORTS['chromadb'] == 8000
        assert 'MARCUS' in BABIES
        assert ACCESS_LEVELS['HEAD'] == 100


# =============================================================================
# OTTER MODULE TESTS
# =============================================================================

class TestOtterImports:
    """Test otter (meeting transcription) module imports."""

    def test_import_otter(self):
        """Test otter package import."""
        import otter
        assert otter is not None

    def test_import_transcriber(self):
        """Test transcriber module import."""
        from otter import transcriber
        assert hasattr(transcriber, 'MeetingTranscriber')

    def test_import_summarizer(self):
        """Test summarizer module import."""
        from otter import summarizer
        assert hasattr(summarizer, 'MeetingSummarizer')

    def test_import_notifier(self):
        """Test notifier module import."""
        from otter import notifier
        assert hasattr(notifier, 'MeetingNotifier')


# =============================================================================
# BRIDGE MODULE TESTS
# =============================================================================

class TestBridgeImports:
    """Test bridge (phone-Linux connection) module imports."""

    def test_import_bridge(self):
        """Test bridge package import."""
        import bridge
        assert bridge is not None

    def test_import_phone_server(self):
        """Test phone_server module import."""
        from bridge import phone_server
        assert hasattr(phone_server, 'PhoneBridgeServer')

    def test_import_termux_client(self):
        """Test termux_client module import."""
        from bridge import termux_client
        assert hasattr(termux_client, 'TermuxClient')


# =============================================================================
# J3 MODULE TESTS
# =============================================================================

class TestJ3Imports:
    """Test j3 (quote generator) module imports."""

    def test_import_j3(self):
        """Test j3 package import."""
        import j3
        assert j3 is not None

    def test_import_quote_generator(self):
        """Test quote_generator module import."""
        from j3 import quote_generator
        assert hasattr(quote_generator, 'QuoteGenerator')

    def test_import_client_manager(self):
        """Test client_manager module import."""
        from j3 import client_manager
        assert hasattr(client_manager, 'ClientManager')


# =============================================================================
# NSIPA MODULE TESTS
# =============================================================================

class TestNsipaImports:
    """Test nsipa (call logger) module imports."""

    def test_import_nsipa(self):
        """Test nsipa package import."""
        import nsipa
        assert nsipa is not None

    def test_import_call_logger(self):
        """Test call_logger module import."""
        from nsipa import call_logger
        assert hasattr(call_logger, 'CallLogger')

    def test_import_appointment_tracker(self):
        """Test appointment_tracker module import."""
        from nsipa import appointment_tracker
        assert hasattr(appointment_tracker, 'AppointmentTracker')


# =============================================================================
# CLAW1 MODULE TESTS
# =============================================================================

class TestClaw1Imports:
    """Test claw1 (sales/CRM) module imports."""

    def test_import_claw1(self):
        """Test claw1 package import."""
        import claw1
        assert claw1 is not None

    def test_import_lead_capture(self):
        """Test lead_capture module import."""
        from claw1.sales import lead_capture
        assert hasattr(lead_capture, 'LeadCapture')

    def test_import_pipeline(self):
        """Test pipeline module import."""
        from claw1.crm import pipeline
        assert hasattr(pipeline, 'SalesPipeline')


# =============================================================================
# CLAW2 MODULE TESTS
# =============================================================================

class TestClaw2Imports:
    """Test claw2 (LCMS) module imports."""

    def test_import_claw2(self):
        """Test claw2 package import."""
        import claw2
        assert claw2 is not None

    def test_import_course_manager(self):
        """Test course_manager module import."""
        from claw2.lcms import course_manager
        assert hasattr(course_manager, 'CourseManager')


# =============================================================================
# TAIL MODULE TESTS
# =============================================================================

class TestTailImports:
    """Test tail (security) module imports."""

    def test_import_tail(self):
        """Test tail package import."""
        import tail
        assert tail is not None

    def test_import_access_control(self):
        """Test access_control module import."""
        from tail.labienus import access_control
        assert hasattr(access_control, 'AccessController')


# =============================================================================
# MOUTH MODULE TESTS
# =============================================================================

class TestMouthImports:
    """Test mouth (API) module imports."""

    def test_import_mouth(self):
        """Test mouth package import."""
        import mouth
        assert mouth is not None

    def test_import_api(self):
        """Test api module import."""
        from mouth import api
        assert hasattr(api, 'app')


# =============================================================================
# INTEGRATION MODULE TESTS
# =============================================================================

class TestIntegrationImports:
    """Test integration module imports."""

    def test_import_integration(self):
        """Test integration package import."""
        import integration
        assert integration is not None

    def test_import_cli(self):
        """Test cli module import."""
        from integration import cli
        assert hasattr(cli, 'main')

    def test_import_scheduler(self):
        """Test scheduler module import."""
        from integration import scheduler
        assert hasattr(scheduler, 'JarvisScheduler')


# =============================================================================
# LEGS MODULE TESTS
# =============================================================================

class TestLegsImports:
    """Test legs (client containers) module imports."""

    def test_import_legs(self):
        """Test legs package import."""
        import legs
        assert legs is not None

    def test_import_client_template(self):
        """Test client_template module import."""
        from legs.template import client_template
        assert hasattr(client_template, 'BaseClientLeg')
        assert hasattr(client_template, 'ClientConfig')


# =============================================================================
# MONITORING MODULE TESTS
# =============================================================================

class TestMonitoringImports:
    """Test monitoring module imports."""

    def test_import_monitoring(self):
        """Test monitoring package import."""
        import monitoring
        assert monitoring is not None

    def test_import_health_check(self):
        """Test health_check module import."""
        from monitoring import health_check
        assert hasattr(health_check, 'HealthChecker')
        assert hasattr(health_check, 'HealthStatus')


# =============================================================================
# FUNCTIONAL TESTS
# =============================================================================

class TestBasicFunctionality:
    """Test basic functionality of core components."""

    def test_config_creation(self):
        """Test ScorpionConfig can be created."""
        from core.config import ScorpionConfig
        config = ScorpionConfig()
        assert config.environment == "development"

    def test_database_url_generation(self):
        """Test database URL is generated correctly."""
        from core.config import DatabaseConfig
        db = DatabaseConfig(
            host="localhost",
            port=5432,
            name="testdb",
            user="testuser",
            password="testpass"
        )
        assert "testuser" in db.url
        assert "testpass" in db.url
        assert "5432" in db.url

    def test_access_level_ordering(self):
        """Test access levels are ordered correctly."""
        from core.constants import AccessLevel
        assert AccessLevel.PUBLIC < AccessLevel.LEG
        assert AccessLevel.LEG < AccessLevel.CLAW
        assert AccessLevel.CLAW < AccessLevel.HEAD

    def test_pipeline_stages_exist(self):
        """Test all pipeline stages are defined."""
        from core.constants import PIPELINE_STAGES
        expected = ['new', 'contacted', 'qualified', 'quoted',
                    'negotiating', 'closed_won', 'closed_lost']
        for stage in expected:
            assert stage in PIPELINE_STAGES

    def test_babies_have_required_fields(self):
        """Test all babies have required configuration fields."""
        from core.constants import BABIES
        required = ['model', 'role', 'temperature', 'max_tokens']
        for baby_name, baby_config in BABIES.items():
            for field in required:
                assert field in baby_config, f"{baby_name} missing {field}"


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
