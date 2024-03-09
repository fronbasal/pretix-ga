from django import forms
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from pretix.base.forms import SettingsForm
from pretix.base.models import Event
from pretix.control.views.event import EventSettingsFormView, EventSettingsViewMixin


class GoogleAnalyticsSettingsForm(SettingsForm):
    container_id = forms.CharField(
        label=_("Google Tag Manager Container ID"),
        required=True,
        help_text=_("The Google Tag Manager Container ID (GTM-XXXXXXXX)."),
        max_length=12,
        min_length=12,
    )


class SettingsView(EventSettingsViewMixin, EventSettingsFormView):
    model = Event
    form_class = GoogleAnalyticsSettingsForm
    template_name = "pretix_ga/settings.html"
    permission = "can_change_event_settings"

    def get_success_url(self):
        return reverse(
            "plugins:pretix_ga:settings",
            kwargs={
                "organizer": self.request.event.organizer.slug,
                "event": self.request.event.slug,
            },
        )
