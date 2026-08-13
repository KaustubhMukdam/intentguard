"""
BDD specs for the IntentGuard rule engine.

Acceptance criteria (from PRD + tasks.md Days 3-4):
  FEATURE: Rule engine pre-filter
    SCENARIO: Known-catastrophic commands are flagged
    SCENARIO: Everyday safe commands pass with zero false positives
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from intentguard.rules import check_rule_match, get_dangerous_patterns


class RuleEngineSpec(unittest.TestCase):
    """SCENARIO: Known-catastrophic commands are flagged"""

    def test_rm_rf_root_is_caught(self):
        result = check_rule_match("rm -rf /")
        self.assertTrue(result["matched"])
        self.assertEqual(result["layer"], "rule_engine")

    def test_rm_rf_wildcard_root_is_caught(self):
        self.assertTrue(check_rule_match("rm -rf /*")["matched"])

    def test_rm_rf_system_directory_is_caught(self):
        for cmd in ["rm -rf /etc/*", "rm -rf /var/log/*", "rm -rf /usr", "rm -rf /root/"]:
            self.assertTrue(check_rule_match(cmd)["matched"], cmd)

    def test_rm_with_separate_flags_is_caught(self):
        for cmd in ["rm -r -f /home/*", "rm -f -r /"]:
            self.assertTrue(check_rule_match(cmd)["matched"], cmd)

    def test_dd_to_block_device_is_caught(self):
        result = check_rule_match("dd if=/dev/zero of=/dev/sda")
        self.assertTrue(result["matched"])

    def test_dd_to_other_block_devices_is_caught(self):
        for cmd in ["dd if=/dev/random of=/dev/sdb1", "dd if=/dev/zero of=/dev/nvme0n1"]:
            self.assertTrue(check_rule_match(cmd)["matched"], cmd)

    def test_raw_redirect_to_block_device_is_caught(self):
        for cmd in ["> /dev/sda", "cat /dev/zero > /dev/sdb"]:
            self.assertTrue(check_rule_match(cmd)["matched"], cmd)

    def test_mkfs_on_block_device_is_caught(self):
        for cmd in ["mkfs.ext4 /dev/sda1", "mkfs.xfs /dev/sda1", "mkfs /dev/sda1", "mkfs -t ext4 /dev/sdb"]:
            self.assertTrue(check_rule_match(cmd)["matched"], cmd)

    def test_chmod_recursive_777_root_is_caught(self):
        for cmd in ["chmod -R 777 /", "chmod -r 777 /*"]:
            self.assertTrue(check_rule_match(cmd)["matched"], cmd)

    def test_chown_recursive_root_is_caught(self):
        self.assertTrue(check_rule_match("chown -R root:root /")["matched"])

    def test_fork_bomb_is_caught(self):
        for cmd in [":(){ :|:& };:", ":(){:|:&};:"]:
            self.assertTrue(check_rule_match(cmd)["matched"], cmd)

    def test_firewall_disable_is_caught(self):
        for cmd in ["ufw disable", "iptables -F"]:
            self.assertTrue(check_rule_match(cmd)["matched"], cmd)

    def test_find_recursive_delete_is_caught(self):
        for cmd in ["find / -delete", "find /etc -exec rm -rf {} \\;", "find /var -name '*.log' -delete"]:
            self.assertTrue(check_rule_match(cmd)["matched"], cmd)

    def test_system_package_force_remove_is_caught(self):
        for cmd in ["apt remove -y linux-image-generic", "dnf remove kernel-devel"]:
            self.assertTrue(check_rule_match(cmd)["matched"], cmd)

    def test_quoted_dangerous_command_is_caught(self):
        self.assertTrue(check_rule_match("rm -rf '/'")["matched"])


class SafePassThroughSpec(unittest.TestCase):
    """SCENARIO: Everyday safe commands pass with zero false positives"""

    SAFE_COMMANDS = [
        "ls -la",
        "cd /home/user",
        "pwd",
        "cat file.txt",
        "grep -r 'pattern' .",
        "git status",
        "git commit -m 'message'",
        "git push origin main",
        "docker ps",
        "df -h",
        "top",
        "ps aux",
        "systemctl status sshd",
        "python script.py",
        "pip install package",
        "mkdir new_dir",
        "cp file1.txt file2.txt",
        "mv old.txt new.txt",
        "tar -xzf archive.tar.gz",
        "echo 'hello world'",
        "rm -rf /tmp/test_dir",
        "rm file.txt",
        "curl -O https://example.com/file.tar.gz",
        "sudo systemctl restart nginx",
        "find . -name '*.py'",
        "ssh user@server",
    ]

    def test_safe_commands_pass_without_flag(self):
        for cmd in self.SAFE_COMMANDS:
            result = check_rule_match(cmd)
            self.assertFalse(result["matched"], f"False positive on: {cmd}")

    def test_rule_engine_has_patterns(self):
        patterns = get_dangerous_patterns()
        self.assertIsInstance(patterns, list)
        self.assertGreaterEqual(len(patterns), 10)
        for pattern in patterns:
            self.assertIn("pattern", pattern)
            self.assertIn("description", pattern)
            self.assertIn("risk_level", pattern)


if __name__ == "__main__":
    unittest.main()
