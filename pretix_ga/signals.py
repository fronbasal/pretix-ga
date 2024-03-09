# Register your receivers here
import logging
import secrets
from django.dispatch import receiver
from django.urls import resolve, reverse
from django.utils.translation import gettext_lazy as _
from pretix.base.middleware import _merge_csp, _parse_csp, _render_csp
from pretix.control.signals import nav_event_settings
from pretix.presale.signals import html_head, html_page_header, process_response

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


@receiver(html_head, dispatch_uid="ga_html_head")
def html_head_presale(sender, request, **kwargs):
    container_id = sender.settings.get("container_id")
    if container_id:
        return """
<script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':
new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],
j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
})(window,document,'script','dataLayer','%container');</script>
        """.replace(
            "%container", container_id
        )


@receiver(html_page_header, dispatch_uid="ga_html_page_header")
def html_page_header_presale(sender, request, **kwargs):
    container_id = sender.settings.get("container_id")
    if container_id:
        return f"""
<noscript><iframe src="https://www.googletagmanager.com/ns.html?id={container_id}"
height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>
        """


@receiver(process_response, dispatch_uid="ga_process_response")
def process_response_presale_csp(sender, request, response, **kwargs):
    container_id = sender.settings.get("container_id")
    if container_id:
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
