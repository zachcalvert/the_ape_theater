from django.contrib.sitemaps import Sitemap

from events.models import Event


class EventSitemap(Sitemap):
    protocol = "https"
    changefreq = "monthly"

    def items(self):
        return Event.objects.all()


sitemaps = {
    'event': EventSitemap,
}
