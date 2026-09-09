from html.parser import HTMLParser
from types import SimpleNamespace

from django.template.loader import render_to_string
from django.test import RequestFactory, SimpleTestCase


class MetricValues(HTMLParser):
    def __init__(self):
        super().__init__()
        self.inside = False
        self.values = []

    def handle_starttag(self, tag, attrs):
        if tag == 'strong' and 'km-metric-val' in dict(attrs).get('class', '').split():
            self.inside = True

    def handle_data(self, data):
        if self.inside and data.strip():
            self.values.append(data.strip())

    def handle_endtag(self, tag):
        if tag == 'strong':
            self.inside = False


class HomePublicMetricsTests(SimpleTestCase):
    def test_empty_partner_metrics_do_not_invent_reviews_or_rating(self):
        request = RequestFactory().get('/ru/')
        request.resolver_match = SimpleNamespace(url_name='home')
        request.LANGUAGE_CODE = 'ru'
        html = render_to_string('pages/home.html', {
            'request': request, 'map_places': [], 'home_categories': [],
            'total_place_reviews_count': 0,
        })
        metrics = MetricValues()
        metrics.feed(html)
        self.assertEqual(metrics.values, ['0', '—', '0'])
