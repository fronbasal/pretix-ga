from django.utils.translation import gettext_lazy

from . import __version__

try:
    from pretix.base.plugins import PluginConfig
except ImportError:
    raise RuntimeError("Please use pretix 4.4.0 or above to run this plugin!")


class PluginApp(PluginConfig):
    default = True
    name = "pretix_ga"
    verbose_name = "Pretix Google Analytics Integration"

    class PretixPluginMeta:
        name = gettext_lazy("Pretix Google Analytics")
        author = "Daniel Malik"
        description = gettext_lazy("Adds Google Analytics tracking to Pretix")
        visible = True
        version = __version__
        category = "INTEGRATION"
        compatibility = "pretix>=4.4.0"

    def ready(self):
        from . import signals  # NOQA
