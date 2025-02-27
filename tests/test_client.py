# Copyright (C) 2023 Yesh
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import shutil
import tempfile
import unittest

from byre.clients.byr import *
# noinspection PyUnresolvedReferences
import context
from byre.clients.data import PROMOTION_FREE


def login(path):
    return ByrClient(os.environ.get("USERNAME", ""), os.environ.get("PASSWORD", ""),
                     cookie_file=os.path.join(path, "dir", "byr.cookies"))


class TestByrClient(unittest.TestCase):
    def test_login(self):
        path = tempfile.mkdtemp()
        client = login(path)
        self.assertFalse(client.is_logged_in())
        client.login(cache=False)
        self.assertTrue(client.is_logged_in())
        client.close()

        # Try to load cookies
        client = ByrClient(os.environ.get("USERNAME", ""), "",
                           cookie_file=os.path.join(path, "dir", "byr.cookies"))
        self.assertTrue(client.is_logged_in())
        client.close()

        shutil.rmtree(path)

    def test_user_info(self):
        path = tempfile.mkdtemp()
        client = ByrClient(os.environ.get("USERNAME", ""), os.environ.get("PASSWORD", ""),
                           cookie_file=os.path.join(path, "dir", "byr.cookies"))
        api = ByrApi(client)
        self.assertNotEqual(0, api.current_user_id())
        self.assertEqual(int(os.environ.get("USER_ID", "0")), api.current_user_id())

        me = api.user_info()
        self.assertEqual(client.username, me.username)
        self.assertEqual(api.current_user_id(), me.user_id)
        self.assertNotEqual(0., me.downloaded)
        self.assertNotEqual(0., me.uploaded)
        self.assertNotEqual(0., me.ratio)

        moderator = api.user_info(311638)
        self.assertEqual("总版主", moderator.level)
        self.assertEqual(311638, moderator.user_id)

        api.close()
        shutil.rmtree(path)

    def test_torrent_table_parsing(self):
        path = tempfile.mkdtemp()
        client = login(path)
        api = ByrApi(client)
        torrents = api.list_torrents()
        self.assertNotEqual(0, len(torrents))
        for torrent in torrents:
            self.assertNotEqual("Others", torrent.category)
        # 大多时候都会有免费种子的吧？
        self.assertTrue(any(PROMOTION_FREE in t.promotions for t in torrents))
        # 大多时候种子都会是比较新的吧？
        self.assertTrue(any(t.live_time < 3 for t in torrents))
        shutil.rmtree(path)

    def test_uploading_listing(self):
        path = tempfile.mkdtemp()
        client = login(path)
        api = ByrApi(client)
        torrents = api.list_user_torrents()
        if len(torrents) != 0:
            self.assertTrue(any(t.uploaded + t.downloaded > 0 for t in torrents))
        shutil.rmtree(path)


if __name__ == "__main__":
    unittest.main()
