#  Copyright (C) 2023 Yesh
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""根据评分给出种子选择结果。"""

import logging
from dataclasses import dataclass

import psutil

from byre.clients.data import LocalTorrent, TorrentInfo
from byre.storage import TorrentStore

_logger = logging.getLogger("byre.planning")
_debug = _logger.debug


@dataclass
class SpaceChange:
    before: float
    to_be_deleted: float
    to_be_downloaded: float
    after: float


@dataclass
class Planner:
    """贪心选择种子。"""

    max_total_size: float
    """种子总大小上限字节数。"""

    max_download_size: float
    """单次下载大小上限字节数。"""

    download_dir: str
    """下载目录，用于计算剩余空间上限。"""

    def plan(self,
             local_torrents: list[LocalTorrent],
             local: list[tuple[LocalTorrent, float]],
             remote: list[tuple[TorrentInfo, float]],
             cache: TorrentStore,
             exists=False,
             ) -> tuple[list[LocalTorrent], list[TorrentInfo], dict[str, list[LocalTorrent]]]:
        # duplicates 用于检查共用文件的种子。
        used, duplicates = self.merge_torrent_info(local_torrents, cache)
        # removable_hashes 用于检查共用文件的种子是否可以移除，以及它们共享分数。
        removable_hashes: dict[str, float] = dict((t.torrent.hash, score) for t, score in local)
        # 以北邮人种子为主
        local = [t for t in local if t[0].site == "byr"]

        disk_remaining = self.get_disk_remaining()
        # 会有误差，所以可能会可用空间出现差一点点的情况……
        max_total_size = used + disk_remaining
        if self.max_total_size > 0:
            max_total_size = min(max_total_size, self.max_total_size)

        remaining = max_total_size - used
        i = 0
        removable, downloadable = [], []
        downloaded = 0.
        for candidate, score in remote:
            if downloaded + candidate.file_size > self.max_download_size:
                continue
            if score == 0.:
                break
            # 能下载就直接下载。
            if candidate.file_size < remaining or exists:
                if not exists:
                    remaining -= candidate.file_size
                    downloaded += candidate.file_size
                downloadable.append(candidate)
                continue
            # 否则尝试移除分数相对低的本地种子。
            removable_size = 0
            j = i
            for j, (torrent, torrent_score) in enumerate(local[i:]):
                # 分数小于零的意味着不可移除（正在下载或上传中等等）。
                if torrent_score >= score or torrent_score < 0:
                    break
                if any(removable_hashes[t.torrent.hash] < 0 for t in duplicates[torrent.torrent.hash]):
                    break
                torrent_score += sum(removable_hashes[t.torrent.hash] for t in duplicates[torrent.torrent.hash])
                # 我们以北邮人为主，其它站点说实话感觉不太活跃，分数不会太高。
                if torrent_score >= score:
                    break
                removable_size += torrent.torrent.size
                if candidate.file_size < removable_size + remaining:
                    break
            if candidate.file_size < removable_size + remaining:
                remaining = remaining + removable_size - candidate.file_size
                removable.extend(t for t, _ in local[i:j + 1])
                i = j + 1
                downloadable.append(candidate)
                downloaded += candidate.file_size
                continue
        return removable, downloadable, duplicates

    def estimate(self, local_torrents: list[LocalTorrent], removable: list[LocalTorrent],
                 downloadable: list[TorrentInfo], cache: TorrentStore, exists=False) -> SpaceChange:
        used, _ = self.merge_torrent_info(local_torrents, cache)
        deleted = sum(t.torrent.size for t in removable)
        downloaded = 0 if exists else sum(t.file_size for t in downloadable)
        return SpaceChange(
            before=used,
            to_be_deleted=deleted,
            to_be_downloaded=downloaded,
            after=used - deleted + downloaded,
        )

    def get_disk_remaining(self):
        remaining = psutil.disk_usage(self.download_dir).free
        return remaining

    @classmethod
    def merge_torrent_info(cls, local_torrents: list[LocalTorrent],
                           cache: TorrentStore) -> tuple[float, dict[str, list[LocalTorrent]]]:
        total = 0.
        path_torrents = {}
        cached = cache.save_extra_torrents(local_torrents)
        for torrent, info in zip(local_torrents, cached):
            if info.path_hash in path_torrents:
                path_torrents[info.path_hash].append(torrent)
            else:
                path_torrents[info.path_hash] = [torrent]
                total += torrent.torrent.size
        duplicates: dict[str, list[LocalTorrent]] = {}
        for _, same_torrents in path_torrents.items():
            if len(same_torrents) > 1:
                hashes = dict((t.torrent.hash, t) for t in same_torrents)
                _debug("共享相同文件的种子：\n%s", "\n".join(t.torrent.name for t in same_torrents))
                for torrent in same_torrents:
                    duplicates[torrent.torrent.hash] = [hashes[h] for h in (hashes.keys() - {torrent.torrent.hash})]
            else:
                duplicates[same_torrents[0].torrent.hash] = []
        return total, duplicates
