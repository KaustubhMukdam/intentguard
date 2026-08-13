"""
Rule engine for IntentGuard
Contains regex/pattern definitions for known-catastrophic commands
"""

import re
from .tokenizer import tokenize_command

# Dangerous patterns — caught instantly with zero latency, no API call.
# Commands pass through tokenizer.py first (shlex), which normalizes quoting
# and collapses whitespace to single spaces, so patterns can rely on that form.

# rm -rf (or -r -f / -f -r) targeting root or a system directory
DANGEROUS_RM_PATTERN = (
    r'\brm\b\s+(-(?:r[fF]|[fF]r)\s+|(-r\s+-f\s+|-f\s+-r\s+))'
    r'(/(\s|$)|/\*|/(?:etc|usr|var|bin|sbin|lib|boot|home|root)\b)'
)
# dd writing to a block device (of=/dev/sdX, /dev/hdX, /dev/vdX, /dev/mmcblkN, /dev/nvme)
DANGEROUS_DD_PATTERN = r'\bdd\b.*\bof\s*=\s*/dev/(sd|hd|vd|mmcblk|nvme)'
# shell redirection writing directly to a block device
DANGEROUS_RAW_DEVICE_WRITE = r'(\s|^)>\s*/dev/(sd|hd|vd|mmcblk|nvme)'
# mkfs (any filesystem type) on a block device
DANGEROUS_MKFS_PATTERN = r'\bmkfs(\.[a-z0-9]+)?\b.*/dev/(sd|hd|vd|mmcblk|nvme)'
# chmod -R 777 on root
DANGEROUS_CHMOD_PATTERN = r'\bchmod\s+-r\s+777\s+/\s*(\*)?'
# chown -R on root
DANGEROUS_CHOWN_PATTERN = r'\bchown\s+-r\s+\S+:\S+\s+/'
# fork bomb
DANGEROUS_FORK_BOMB_PATTERN = r':\s*\(\s*\)\s*\{.*:\|:.*\};'
# firewall: disabling ufw or flushing iptables
DANGEROUS_FIREWALL_PATTERN = r'\b(ufw\s+disable|iptables\s+-f\b)'
# find-based recursive deletion on root/system paths
DANGEROUS_FIND_DELETE_PATTERN = r'\bfind\s+/\S*\s+.*(-exec\s+rm\b|delete)'
# force-removing system-critical packages
DANGEROUS_PACKAGE_PATTERN = (
    r'\b(pacman|apt(-get)?|yum|dnf)\s+(-y\s+)*(remove|purge)\s+.*'
    r'\b(linux-image|linux-headers|kernel|systemd|libc6|glibc|grub)\b'
)

# (compiled pattern, description, risk_level)
COMPILED_PATTERNS = [
    (re.compile(DANGEROUS_RM_PATTERN, re.IGNORECASE),
     "rm -rf on root or system directory", "critical"),
    (re.compile(DANGEROUS_DD_PATTERN, re.IGNORECASE),
     "dd writing to a block device", "critical"),
    (re.compile(DANGEROUS_RAW_DEVICE_WRITE, re.IGNORECASE),
     "redirecting output directly to a block device", "critical"),
    (re.compile(DANGEROUS_MKFS_PATTERN, re.IGNORECASE),
     "mkfs formatting a block device", "critical"),
    (re.compile(DANGEROUS_CHMOD_PATTERN, re.IGNORECASE),
     "chmod -R 777 on root", "critical"),
    (re.compile(DANGEROUS_CHOWN_PATTERN, re.IGNORECASE),
     "recursive chown on root", "high"),
    (re.compile(DANGEROUS_FORK_BOMB_PATTERN),
     "fork bomb", "critical"),
    (re.compile(DANGEROUS_FIREWALL_PATTERN, re.IGNORECASE),
     "disabling firewall protection", "high"),
    (re.compile(DANGEROUS_FIND_DELETE_PATTERN, re.IGNORECASE),
     "find-based recursive delete on root/system path", "critical"),
    (re.compile(DANGEROUS_PACKAGE_PATTERN, re.IGNORECASE),
     "force-removing system-critical package", "high"),
]


def check_rule_match(command: str) -> dict:
    """
    Check if command matches any dangerous patterns.

    Args:
        command: Raw command string.

    Returns:
        Dict with match info, or {"matched": False} if no match.
    """
    normalized_command = " ".join(tokenize_command(command))

    for pattern, description, risk_level in COMPILED_PATTERNS:
        if pattern.search(normalized_command):
            return {
                "matched": True,
                "pattern": pattern.pattern,
                "description": description,
                "risk_level": risk_level,
                "layer": "rule_engine",
            }

    return {"matched": False}


def get_dangerous_patterns() -> list:
    """Return list of all dangerous patterns for testing/documentation."""
    return [
        {"pattern": p.pattern, "description": d, "risk_level": r}
        for p, d, r in COMPILED_PATTERNS
    ]
