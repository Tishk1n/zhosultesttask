"""Validation utilities."""
from ipaddress import IPv4Address, IPv6Address, ip_address
from typing import Final, List, Set
from urllib.parse import urlparse

# Valid URL schemes
VALID_SCHEMES: Final[Set[str]] = {"http", "https"}

# Blocked hostnames
BLOCKED_HOSTS: Final[Set[str]] = {
    "localhost",
    "127.0.0.1",
    "::1",
}

# Private network prefixes
PRIVATE_PREFIXES: Final[List[str]] = [
    "10.",
    "172.16.", "172.17.", "172.18.", "172.19.",
    "172.20.", "172.21.", "172.22.", "172.23.",
    "172.24.", "172.25.", "172.26.", "172.27.",
    "172.28.", "172.29.", "172.30.", "172.31.",
    "192.168."
]


def is_private_ip(ip: str) -> bool:
    """Check if an IP address is private.

    Args:
        ip (str): IP address to check

    Returns:
        bool: True if the IP is private, False otherwise
    """
    try:
        ip_obj = ip_address(ip)
        if isinstance(ip_obj, (IPv4Address, IPv6Address)):
            return ip_obj.is_private
        return False
    except ValueError:
        return False


def is_safe_url(url: str) -> bool:
    """Validate if URL is safe to make requests to.

    Args:
        url (str): URL to validate

    Returns:
        bool: True if the URL is safe, False otherwise
    """
    if not url or not isinstance(url, str):
        return False

    try:
        parsed = urlparse(url)
        hostname = parsed.hostname

        # Check scheme
        if parsed.scheme not in VALID_SCHEMES:
            return False

        # Require hostname
        if not hostname:
            return False

        # Prevent localhost and known internal addresses
        if hostname in BLOCKED_HOSTS:
            return False

        # Try to parse hostname as IP
        try:
            if is_private_ip(hostname):
                return False
        except ValueError:
            pass

        # Check for private network prefixes
        if any(hostname.startswith(prefix) for prefix in PRIVATE_PREFIXES):
            return False

        return True

    except Exception:
        return False
