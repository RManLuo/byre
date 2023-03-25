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

"""北邮人 PT 站的用户、种子等信息。"""

from dataclasses import dataclass


@dataclass
class ByrUser:
    """一位北邮人用户。"""

    user_id = 0
    """用户 ID。"""

    username = ""

    level = ""
    """用户等级。"""

    mana = 0.
    """魔力值。"""

    invitations = 0
    """邀请数量。"""

    ranking = 0
    """上传排行。"""

    ratio = -1.
    """分享率。"""

    uploaded = 0.
    """上传量（GB）。"""

    downloaded = 0.
    """下载量（GB）。"""

    seeding = 0
    """当前活动上传数。"""

    downloading = 0
    """当前活动下载数。"""

    connectable = False
    """用户客户端可连接状态。"""


PROMOTION_THIRTY_DOWN = "thirty_down"

PROMOTION_HALF_DOWN = "half_down"

PROMOTION_TWO_UP = "two_up"

PROMOTION_FREE = "free"


@dataclass
class TorrentInfo:
    """从北邮人上抓取来的种子信息。"""

    title: str
    """种子标题。"""

    sub_title: str
    """种子副标题。"""

    seed_id: int
    """种子 id，最好不要与 transmission 的种子 id 混淆。"""

    cat: str
    """分类（“电影”、“软件”这种）。"""

    category: str
    """英文分类（变成了“Movies”、“Software”这种）。"""

    promotions: list[str]
    """打折标签（免费、2x上传这种，提取成为“free”“two_up”等）。"""

    file_size: float
    """种子总大小（GB 或是 1000 ** 3 字节）。"""

    live_time: float
    """存活时间（天）。"""

    seeders: int
    """上传者人数。"""

    leechers: int
    """下载者人数。"""

    finished: int
    """已完成的下载数。"""

    comments: int
    """评论数。"""

    uploader: ByrUser
    """上传者。"""

    uploaded: float
    """当前用户上传量。"""

    downloaded: float
    """当前用户下载量（GB）。"""

    ratio: float
    """当前用户分享率。"""

    @staticmethod
    def convert_byr_category(cat: str):
        directories = {
            "电影": "Movies",
            "剧集": "TVSeries",
            "动漫": "Anime",
            "音乐": "Music",
            "综艺": "VarietyShows",
            "游戏": "Games",
            "软件": "Software",
            "资料": "Documents",
            "体育": "Sports",
            "纪录": "Documentaries",
        }
        return directories.get(cat, "Others")
