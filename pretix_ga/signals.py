import logging
import secrets
from django.dispatch import receiver
from django.urls import resolve, reverse
from django.utils.translation import gettext_lazy as _
from pretix.base.middleware import _merge_csp, _parse_csp, _render_csp
from pretix.control.signals import nav_event_settings
from pretix.presale.signals import html_page_header, process_response

logger = logging.getLogger(__name__)


def generate_nonce(length=12):
    return secrets.token_urlsafe(length)


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
    if measurement_id:
        return f"""
<script async src="https://www.googletagmanager.com/gtag/js?id={measurement_id}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag()\u007bdataLayer.push(arguments);\u007d
  gtag('js', new Date());
  gtag('config', '{measurement_id}');
</script>
        """


@receiver(process_response, dispatch_uid="ga_process_response")
def process_response_presale_csp(sender, request, response, **kwargs):
    measurement_id = sender.settings.get("measurement_id")
    if measurement_id:
        if "Content-Security-Policy" in response:
            headers = _parse_csp(response["Content-Security-Policy"])
        else:
            headers = {}

        _merge_csp(
            headers,
            {
                "script-src": [
                    "'self'",
                    "'unsafe-inline'",
                    "https://www.googletagmanager.com",
                    "https://tagmanager.google.com",
                    "https://*.googletagmanager.com",
                    "https://www.google-analytics.com",
                    "https://ssl.google-analytics.com",
                ],
                "style-src": [
                    "'self'",
                    "https://www.googletagmanager.com",
                    "https://tagmanager.google.com",
                    "https://fonts.googleapis.com",
                ],
                "img-src": [
                    "'self'",
                    "https://www.googletagmanager.com",
                    "https://ssl.gstatic.com",
                    "https://www.gstatic.com",
                    "https://*.google-analytics.com",
                    "https://*.googletagmanager.com",
                    "https://www.google-analytics.com",
                ],
                "font-src": ["'self'", "https://fonts.gstatic.com", "data:"],
                "connect-src": [
                    "'self'",
                    "https://*.google-analytics.com",
                    "https://*.analytics.google.com",
                    "https://*.googletagmanager.com",
                    "https://www.google-analytics.com",
                ],
            },
        )

        if headers:
            response["Content-Security-Policy"] = _render_csp(headers)

    return response
