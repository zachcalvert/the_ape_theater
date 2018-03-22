from django.contrib.sitemaps import Sitemap

from classes.models import ApeClass


class ApeClassSitemap(Sitemap):
    protocol = "https"
    changefreq = "monthly"

    def items(self):
        return ApeClass.objects.all()


sitemaps = {
    'class': ApeClassSitemap,
}
