from __future__ import absolute_import
from webserver.testing import ServerTestCase
from flask import url_for


class IndexViewsTestCase(ServerTestCase):

    def test_index(self):
        resp = self.client.get(url_for('index.index'))
        self.assert200(resp)

