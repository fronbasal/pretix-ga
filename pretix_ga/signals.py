import logging
import secrets
from base64 import b64encode

from django.dispatch import receiver
from django.urls import resolve, reverse
from django.utils.translation import gettext_lazy as _

from pretix.base.middleware import _merge_csp, _parse_csp, _render_csp
from pretix.control.signals import nav_event_settings
from pretix.presale.signals import html_page_header, process_response

logger = logging.getLogger(__name__)


@receiver(nav_event_settings, dispatch_uid="ga_nav_event_settings")
def navbar_event_settings(sender, request, **kwargs):
    url = resolve(request.path_info)
    return [
        {
            "label": _("Google Analytics"),
            "url": reverse(
                "plugins:pretix_ga:settings",
                kwargs={
                    "event": request.event.slug,
                    "organizer": request.organizer.slug,
                },
            ),
            "active": url.namespace == "plugins:pretix_ga"
                      and url.url_name.startswith("settings"),
        }
    ]


@receiver(html_page_header, dispatch_uid="ga_html_page_header")
def html_page_header_presale(sender, request, **kwargs):
    measurement_id = sender.settings.get("measurement_id")
    if not measurement_id:
        return
    # Generate a sha256 integrity hash for the script tag
    script_content = f"""window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','{measurement_id}');"""
    nonce = b64encode(secrets.token_bytes(16)).decode("utf-8")
    # store integrity hash in request for later csp processing
    request._ga_script_nonce = nonce
    return f"""<script async src="https://www.googletagmanager.com/gtag/js?id={measurement_id}"></script>
    <script nonce="{nonce}">{script_content}</script>"""


@receiver(process_response, dispatch_uid="ga_process_response")
def process_response_presale_csp(sender, request, response, **kwargs):
    measurement_id = sender.settings.get("measurement_id")
    if not measurement_id:
        return response

    headers = {}
    if "Content-Security-Policy" in response:
        headers = _parse_csp(response["Content-Security-Policy"])

    script_nonce = getattr(request, "_ga_script_nonce", None)
    if script_nonce:
        _merge_csp(headers, {"script-src": [f"'nonce-{script_nonce}'"]})

    _merge_csp(
        headers,
        {
            "script-src": [
                "https://www.googletagmanager.com",
                "https://tagmanager.google.com",
                "https://*.googletagmanager.com",
                "https://www.google-analytics.com",
                "https://ssl.google-analytics.com",
                "https://analytics.google.com",
            ],
            "style-src": [
                "https://www.googletagmanager.com",
                "https://tagmanager.google.com",
                "https://fonts.googleapis.com",
            ],
            "img-src": [
                "https://www.googletagmanager.com",
                "https://ssl.gstatic.com",
                "https://www.gstatic.com",
                "https://*.google-analytics.com",
                "https://*.googletagmanager.com",
                "https://www.google-analytics.com",
                "https://analytics.google.com",
                "https://*.google.de",
            ],
            "font-src": ["https://fonts.gstatic.com"],
            "connect-src": [
                "https://*.google-analytics.com",
                "https://*.analytics.google.com",
                "https://*.googletagmanager.com",
                "https://www.google-analytics.com",
                "https://analytics.google.com",
                "https://*.doubleclick.net",
            ],
        },
    )

    if headers:
        response["Content-Security-Policy"] = _render_csp(headers)

    return response
