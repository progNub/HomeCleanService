from ipaddress import ip_address, ip_network

from django.conf import settings


def get_client_ip(request):
    """Trust Nginx's overwritten X-Real-IP only from explicitly trusted peers."""
    if request is None:
        return None
    try:
        peer = ip_address(request.META.get("REMOTE_ADDR", ""))
    except ValueError:
        return None
    trusted = any(peer in ip_network(cidr, strict=False) for cidr in settings.TRUSTED_PROXY_CIDRS)
    if trusted:
        try:
            return str(ip_address(request.META.get("HTTP_X_REAL_IP", "")))
        except ValueError:
            pass
    return str(peer)
