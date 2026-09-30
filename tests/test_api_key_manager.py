"""
test_api_key_manager.py — Unit Tests for Multi-API Key Pooling & Rotation
========================================================================
Verifies:
  1. Round-robin rotation across multiple API keys.
  2. Automatic cooldown and rollover when HTTP 429 is reported.
  3. Safe credential masking without plain-text leaks.
  4. Numbered and comma-separated environment variable ingestion.
"""

from __future__ import annotations

import os
import time
import unittest

from ml.security.api_key_manager import APIKeyManager, MultiAPIKeyPool, mask_key


class TestAPIKeyManager(unittest.TestCase):

    def test_key_masking(self):
        self.assertEqual(mask_key("sk-998877665544332211"), "sk-***2211")
        self.assertEqual(mask_key("short"), "***")

    def test_round_robin_rotation(self):
        pool = MultiAPIKeyPool("test_service", keys=["KEY_A", "KEY_B", "KEY_C"])
        k1 = pool.get_key()
        k2 = pool.get_key()
        k3 = pool.get_key()
        k4 = pool.get_key()

        self.assertEqual(k1, "KEY_A")
        self.assertEqual(k2, "KEY_B")
        self.assertEqual(k3, "KEY_C")
        self.assertEqual(k4, "KEY_A")  # Rotates back

    def test_rate_limit_cooldown_fallback(self):
        pool = MultiAPIKeyPool("test_service", keys=["KEY_PRIMARY", "KEY_BACKUP"], cooldown_seconds=2.0)
        
        # Report 429 on KEY_PRIMARY
        pool.report_rate_limit("KEY_PRIMARY")
        
        # Next request must automatically yield KEY_BACKUP
        next_key = pool.get_key()
        self.assertEqual(next_key, "KEY_BACKUP")

        # Status summary check
        status = pool.get_status_summary()
        self.assertEqual(status["keys_in_cooldown"], 1)
        self.assertEqual(status["active_healthy_keys"], 1)

    def test_manager_pool_loading(self):
        os.environ["COPERNICUS_API_KEYS"] = "COP_KEY_1,COP_KEY_2,COP_KEY_3"
        mgr = APIKeyManager()
        cop_key = mgr.get_key("copernicus")
        self.assertIn(cop_key, ["COP_KEY_1", "COP_KEY_2", "COP_KEY_3"])

        # Test report rate limit
        mgr.report_rate_limit("copernicus", "COP_KEY_1")
        status = mgr.get_pool_status()
        self.assertEqual(status["copernicus"]["keys_in_cooldown"], 1)


if __name__ == "__main__":
    unittest.main()
