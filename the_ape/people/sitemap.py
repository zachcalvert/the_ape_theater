from django.contrib.sitemaps import Sitemap

from people.models import HouseTeam, Person


class HouseTeamSitemap(Sitemap):
    protocol = "https"
    changefreq = "monthly"

    def items(self):
        return HouseTeam.objects.all()


class PersonSitemap(Sitemap):
    protocol = "https"
    changefreq = "monthly"

    def items(self):
        return Person.objects.all()


sitemaps = {
    'house_team': HouseTeamSitemap,
    'person': PersonSitemap,
}
