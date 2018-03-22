from django.contrib.sitemaps import Sitemap

from pages.models import Page


class PageSitemap(Sitemap):
    protocol = "https"
    changefreq = "weekly"

    def items(self):
        return Page.objects.filter(draft=False)

    def location(self, obj):
        return obj.get_url()


sitemaps = {'page': PageSitemap}