"""
Module Tải xuống Hàng loạt (Batch Downloader)
Sử dụng yt-dlp với kiến trúc đa luồng (Multi-threading / ThreadPoolExecutor),
kèm cơ chế try-except bắt lỗi từng link để không bao giờ làm sập ứng dụng.
"""

import os
import concurrent.futures
from typing import Callable, List, Dict, Optional
import yt_dlp


class BatchDownloader:
    def __init__(
        self,
        items: List[Dict],
        dest_dir: str,
        max_workers: int = 4,
        quality_mode: str = "Tốt nhất (Best MP4)",
        on_progress: Optional[Callable[[int, int, str], None]] = None,
        on_log: Optional[Callable[[str, str], None]] = None,
        on_finished: Optional[Callable[[Dict], None]] = None
    ):
        self.items = items
        self.dest_dir = dest_dir
        self.max_workers = max_workers
        self.quality_mode = quality_mode
        self.on_progress = on_progress
        self.on_log = on_log
        self.on_finished = on_finished

        self.stop_requested = False
        self.completed_count = 0
        self.success_count = 0
        self.failed_count = 0

        # Đảm bảo thư mục lưu tồn tại
        os.makedirs(self.dest_dir, exist_ok=True)

    def log(self, level: str, message: str):
        if self.on_log:
            self.on_log(level, message)
        else:
            print(f"[{level.upper()}] {message}")

    def stop(self):
        """Yêu cầu hủy các tác vụ tải chưa hoàn thành."""
        self.stop_requested = True

    def _build_ytdl_options(self, target_url: str) -> dict:
        """Thiết lập cấu hình tối ưu cho yt-dlp."""
        outtmpl = os.path.join(self.dest_dir, "%(title).80s [%(id)s].%(ext)s")

        # Cấu hình định dạng chất lượng tải
        if "Chỉ âm thanh" in self.quality_mode:
            format_opt = "bestaudio/best"
            postprocessors = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }]
        elif "1080p" in self.quality_mode:
            format_opt = "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best"
            postprocessors = []
        elif "720p" in self.quality_mode:
            format_opt = "bestvideo[height<=720]+bestaudio/best[height<=720]/best"
            postprocessors = []
        else:
            # Best MP4
            format_opt = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
            postprocessors = []

        ydl_opts = {
            "format": format_opt,
            "outtmpl": outtmpl,
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "ignoreerrors": False,
            "retries": 3,
            "fragment_retries": 3,
            "socket_timeout": 20,
            "postprocessors": postprocessors,
            # Bỏ qua SSL verification nếu gặp sự cố chứng chỉ
            "nocheckcertificate": True,
        }

        return ydl_opts

    def _download_single_item(self, item: Dict, index: int) -> bool:
        """Hàm tải từng video độc lập được gọi trong ThreadPool."""
        if self.stop_requested:
            return False

        url = item.get("url")
        title = item.get("title", f"Video_{index+1}")

        self.log("info", f"[{index+1}/{len(self.items)}] Bắt đầu tải: {title[:50]}...")
        ydl_opts = self._build_ytdl_options(url)

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            self.log("success", f"[{index+1}/{len(self.items)}] Tải thành công: {title[:50]}")
            return True

        except yt_dlp.utils.DownloadError as de:
            self.log("error", f"[{index+1}/{len(self.items)}] Lỗi tải video ({url}): {str(de)[:120]}")
            return False
        except Exception as e:
            self.log("error", f"[{index+1}/{len(self.items)}] Lỗi ngoại lệ không lường trước: {str(e)[:120]}")
            return False

    def run(self):
        total = len(self.items)
        self.log("info", f"Khởi tạo ThreadPool với {self.max_workers} luồng xử lý đồng thời.")

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Đẩy toàn bộ tác vụ tải vào Executor
            future_to_item = {
                executor.submit(self._download_single_item, item, idx): item
                for idx, item in enumerate(self.items)
            }

            for future in concurrent.futures.as_completed(future_to_item):
                if self.stop_requested:
                    self.log("warn", "Tiến trình tải bị ngắt. Đang hủy các tác vụ còn lại...")
                    break

                item = future_to_item[future]
                self.completed_count += 1

                try:
                    success = future.result()
                    if success:
                        self.success_count += 1
                    else:
                        self.failed_count += 1
                except Exception as exc:
                    self.failed_count += 1
                    self.log("error", f"Task sinh lỗi ngoại lệ: {exc}")

                if self.on_progress:
                    self.on_progress(self.completed_count, total, item.get("title", ""))

        summary = {
            "total": total,
            "success": self.success_count,
            "failed": self.failed_count,
            "destination": self.dest_dir
        }

        if self.on_finished:
            self.on_finished(summary)
