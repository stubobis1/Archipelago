"""
Unit tests for version compatibility functionality in Path of Exile APWorld
"""
import unittest
from unittest.mock import Mock, patch, AsyncMock
import asyncio
import logging

from worlds.poe.test import PoeTestBase


class TestVersionCompatibility(PoeTestBase):
    """Test version compatibility checking functionality"""
    
    def setUp(self):
        super().setUp()
        # Import here to avoid circular imports and ensure modules are loaded
        from worlds.poe.Client import PathOfExileContext
        from worlds.poe.Version import POE_VERSION, BACKWARDS_COMPATIBLE_VERSIONS
        
        self.ctx = Mock()
        self.ctx.logger = Mock(spec=logging.Logger)
        self.ctx.command_processor = Mock()
        self.ctx.command_processor.output = Mock()
        
        self.POE_VERSION = POE_VERSION
        self.BACKWARDS_COMPATIBLE_VERSIONS = BACKWARDS_COMPATIBLE_VERSIONS
        
        # Set up default slot data
        self.slot_data = {
            'game_options': {},
            'client_options': {},
            'generated_version': self.POE_VERSION
        }
        
        # Mock args for on_package
        self.connected_args = {
            'slot_data': self.slot_data
        }
    
    def test_version_exact_match(self):
        """Test when server and client versions match exactly"""
        self.slot_data['generated_version'] = self.POE_VERSION
        
        self.ctx.on_package('Connected', self.connected_args)
        
        # Should not log any warnings
        self.ctx.logger.warning.assert_not_called()
        self.ctx.logger.info.assert_not_called()
    
    def test_version_backwards_compatible(self):
        """Test when server version is in backwards compatible list"""
        compatible_version = "1.0.9"
        
        with patch.dict(self.BACKWARDS_COMPATIBLE_VERSIONS, {compatible_version: True}):
            self.slot_data['generated_version'] = compatible_version
            
            self.ctx.on_package('Connected', self.connected_args)
            
            # Should log info message about backwards compatibility
            self.ctx.logger.info.assert_called_once()
            info_call = self.ctx.logger.info.call_args[0][0]
            self.assertIn("backwards compatible", info_call)
            self.assertIn(compatible_version, info_call)
            
            # Should also output to command processor
            self.ctx.command_processor.output.assert_called_once()
    
    def test_version_incompatible(self):
        """Test when server version is not compatible"""
        incompatible_version = "0.5.0"
        self.slot_data['generated_version'] = incompatible_version
        
        self.ctx.on_package('Connected', self.connected_args)
        
        # Should log warning message
        self.ctx.logger.warning.assert_called_once()
        warning_call = self.ctx.logger.warning.call_args[0][0]
        self.assertIn("unsupported version", warning_call)
        self.assertIn(incompatible_version, warning_call)
        self.assertIn(self.POE_VERSION, warning_call)
        
        # Should also output to command processor
        self.ctx.command_processor.output.assert_called_once()
    
    def test_version_unknown(self):
        """Test when server version is unknown/missing"""
        self.slot_data.pop('generated_version', None)
        
        self.ctx.on_package('Connected', self.connected_args)
        
        # Should have generated_version set to 'unknown'
        self.assertEqual(self.ctx.generated_version, 'unknown')
        
        # Should log warning for unknown version
        self.ctx.logger.warning.assert_called_once()
        warning_call = self.ctx.logger.warning.call_args[0][0]
        self.assertIn("unsupported version", warning_call)
        self.assertIn("unknown", warning_call)


class TestVersionConstants(unittest.TestCase):
    """Test version constants and format"""
    
    def setUp(self):
        from worlds.poe.Version import POE_VERSION, BACKWARDS_COMPATIBLE_VERSIONS
        self.POE_VERSION = POE_VERSION
        self.BACKWARDS_COMPATIBLE_VERSIONS = BACKWARDS_COMPATIBLE_VERSIONS
    
    def test_poe_version_format(self):
        """Test that POE_VERSION follows expected format"""
        # Should be in format "x.y.z" where x, y, z are numbers
        import re
        version_pattern = r'^\d+\.\d+\.\d+$'
        self.assertIsNotNone(re.match(version_pattern, self.POE_VERSION), 
                           f"POE_VERSION '{self.POE_VERSION}' doesn't match expected format 'x.y.z'")
    
    def test_poe_version_not_empty(self):
        """Test that POE_VERSION is not empty"""
        self.assertIsNotNone(self.POE_VERSION)
        self.assertNotEqual(self.POE_VERSION, "")
        self.assertIsInstance(self.POE_VERSION, str)
    
    def test_backwards_compatible_versions_type(self):
        """Test that BACKWARDS_COMPATIBLE_VERSIONS is a dictionary"""
        self.assertIsInstance(self.BACKWARDS_COMPATIBLE_VERSIONS, dict)


class TestVersionIntegration(PoeTestBase):
    """Integration tests for version functionality"""
    
    def test_version_import_chain(self):
        """Test that version imports work correctly across modules"""
        # Test that Version.py can be imported
        from worlds.poe.Version import POE_VERSION, BACKWARDS_COMPATIBLE_VERSIONS
        
        # Test that Client.py can import from Version.py
        from worlds.poe.Client import PathOfExileContext
        
        # Verify the imports succeeded
        self.assertIsInstance(POE_VERSION, str)
        self.assertIsInstance(BACKWARDS_COMPATIBLE_VERSIONS, dict)


if __name__ == '__main__':
    unittest.main()


if __name__ == '__main__':
    unittest.main()
