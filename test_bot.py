#!/usr/bin/env python3
"""Test suite for Cyber Companion Bot"""

import unittest
import os
import sys
import tempfile
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cyber_companion_bot as bot

class TestDatabaseManager(unittest.TestCase):
    """Test DatabaseManager class"""
    
    def setUp(self):
        """Set up test database"""
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.db = bot.DatabaseManager(self.temp_db.name)
    
    def tearDown(self):
        """Clean up test database"""
        self.db.close()
        os.unlink(self.temp_db.name)
    
    def test_init_tables(self):
        """Test database initialization"""
        self.db.init_tables()
        # Check if tables exist
        tables = ['command_history', 'threats', 'scans', 'managed_ips', 'nikto_scans']
        for table in tables:
            self.db.cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            self.assertIsNotNone(self.db.cursor.fetchone())
    
    def test_log_command(self):
        """Test logging commands"""
        self.db.log_command("test command", "test", True, "output", 1.0)
        
        self.db.cursor.execute("SELECT * FROM command_history")
        result = self.db.cursor.fetchone()
        self.assertIsNotNone(result)
        self.assertEqual(result[1], "test command")
    
    def test_add_managed_ip(self):
        """Test adding managed IPs"""
        result = self.db.add_managed_ip("192.168.1.1", "tester", "test note")
        self.assertTrue(result)
        
        ips = self.db.get_managed_ips()
        self.assertEqual(len(ips), 1)
        self.assertEqual(ips[0]['ip_address'], "192.168.1.1")

class TestCommandExecutor(unittest.TestCase):
    """Test CommandExecutor class"""
    
    def setUp(self):
        """Set up test executor"""
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.db = bot.DatabaseManager(self.temp_db.name)
        self.executor = bot.CommandExecutor(self.db)
    
    def tearDown(self):
        """Clean up"""
        self.db.close()
        os.unlink(self.temp_db.name)
    
    def test_execute_simple_command(self):
        """Test executing a simple command"""
        result = self.executor.execute("echo 'test'", "test")
        self.assertTrue(result['success'])
        self.assertIn("test", result['output'])
    
    def test_execute_invalid_command(self):
        """Test executing invalid command"""
        result = self.executor.execute("invalid_command_xyz", "test")
        self.assertFalse(result['success'])

class TestCyberCompanionBot(unittest.TestCase):
    """Test main application class"""
    
    def setUp(self):
        """Set up test app"""
        self.app = bot.CyberCompanionBot()
    
    def test_load_config(self):
        """Test loading configuration"""
        config = self.app.load_config()
        self.assertIsInstance(config, dict)
    
    def test_print_help(self):
        """Test help output"""
        # Just check it doesn't crash
        try:
            self.app.print_help()
        except Exception as e:
            self.fail(f"print_help() raised {e}")

if __name__ == '__main__':
    unittest.main()