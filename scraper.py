"""
Module bóc tách liên kết kênh (Scraper Module)
Sử dụng Playwright (headless mode) tự động cuộn trang (Infinite Scroll),
thu thập toàn bộ URL video/shorts, loại bỏ trùng lặp và chuyển dữ liệu tức thì về giao diện.
"""

import time
import re
from typing import Callable, Optional
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


class ChannelScraper:
    def __init__(
        self,
        url: str,
        max_scrolls: int = 30,
        on_video_found: Optional[Callable[[dict], None]] = None,
        on_log: Optional[Callable[[str, str], None]] = None,
        on_finished: Optional[Callable[[], None]] = None
    ):
        self.target_url = url
        self.max_scrolls = max_scrolls
        self.on_video_found = on_video_found
        self.on_log = on_log
        self.on_finished = on_finished

        self.stop_requested = False
        self.discovered_urls = set()

    def log(self, level: str, message: str):
        if self.on_log:
            self.on_log(level, message)
        else:
            print(f"[{level.upper()}] {message}")

    def stop(self):
        """Báo hiệu dừng cuộn và đóng trình duyệt một cách an toàn."""
        self.stop_requested = True

    def _normalize_video_url(self, raw_url: str, base_domain: str) -> Optional[str]:
        """Chuẩn hóa và lọc URL hợp lệ dựa theo domain mạng xã hội/video."""
        if not raw_url:
            return None

        # Xử lý URL tương đối
        if raw_url.startswith("/"):
            if "youtube.com" in base_domain:
                raw_url = "https://www.youtube.com" + raw_url
            elif "tiktok.com" in base_domain:
                raw_url = "https://www.tiktok.com" + raw_url
            elif "facebook.com" in base_domain:
                raw_url = "https://www.facebook.com" + raw_url

        # Kiểm tra pattern YouTube
        if "youtube.com" in raw_url or "youtu.be" in raw_url:
            # Lọc link video thường hoặc shorts
            if "/watch?v=" in raw_url:
                match = re.search(r"watch\?v=([a-zA-Z0-9_-]{11})", raw_url)
                if match:
                    return f"https://www.youtube.com/watch?v={match.group(1)}"
            elif "/shorts/" in raw_url:
                match = re.search(r"shorts/([a-zA-Z0-9_-]{11})", raw_url)
                if match:
                    return f"https://www.youtube.com/shorts/{match.group(1)}"

        # Kiểm tra pattern TikTok
        elif "tiktok.com" in raw_url and "/video/" in raw_url:
            match = re.search(r"/video/(\d+)", raw_url)
            if match:
                return raw_url.split("?")[0]

        # Kiểm tra pattern Facebook Reels / Watch
        elif "facebook.com" in raw_url and ("/reel/" in raw_url or "/watch/" in raw_url or "/videos/" in raw_url):
            return raw_url.split("?")[0]

        # Trả về URL thông thường nếu có định dạng video
        elif any(ext in raw_url.lower() for ext in [".mp4", ".mkv", ".webm", ".m3u8"]):
            return raw_url

        return None

    def run(self):
        self.log("info", "Đang khởi tạo Playwright Chromium headless engine...")
        try:
            with sync_playwright() as p:
                # Khởi chạy Chromium không hiển thị cửa sổ (headless)
                browser = p.chromium.launch(
                    headless=True,
                    args=[
                        "--disable-gpu",
                        "--no-sandbox",
                        "--disable-dev-shm-usage",
                        "--mute-audio"
                    ]
                )

                # Giả lập User-Agent Windows Desktop chân thực
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
                    viewport={"width": 1280, "height": 800}
                )

                page = context.new_page()
                page.set_default_timeout(30000)

                self.log("info", f"Đang điều hướng tới: {self.target_url}")
                page.goto(self.target_url, wait_until="domcontentloaded")

                # Bỏ qua hộp thoại chấp nhận cookie (nếu xuất hiện)
                try:
                    cookie_btn = page.locator("button:has-text('Accept all'), button:has-text('I agree'), button:has-text('Chấp nhận tất cả')").first
                    if cookie_btn.is_visible(timeout=3000):
                        cookie_btn.click()
                        self.log("info", "Đã tự động xác nhận hộp thoại Cookie.")
                except Exception:
                    pass

                time.sleep(2)
                base_domain = urlparse(self.target_url).netloc

                # Bắt đầu vòng lặp cuộn vô tận (Infinite Scroll)
                scroll_count = 0
                no_new_links_streak = 0
                last_page_height = page.evaluate("() => document.body.scrollHeight")

                self.log("info", f"Bắt đầu cuộn trang tự động (Tối đa: {self.max_scrolls} lần cuộn)...")

                while scroll_count < self.max_scrolls and not self.stop_requested:
                    scroll_count += 1

                    # Trích xuất toàn bộ các thẻ liên kết <a> trên trang hiện tại
                    elements = page.query_selector_all("a")
                    new_found_in_step = 0

                    for el in elements:
                        if self.stop_requested:
                            break
                        try:
                            href = el.get_attribute("href")
                            clean_url = self._normalize_video_url(href, base_domain)

                            if clean_url and clean_url not in self.discovered_urls:
                                self.discovered_urls.add(clean_url)
                                new_found_in_step += 1

                                # Lấy tiêu đề nếu có
                                title = el.get_attribute("title") or el.inner_text() or ""
                                title = title.strip().replace("\n", " ")
                                if not title or len(title) < 3:
                                    title = f"Video {len(self.discovered_urls)} ({clean_url.split('/')[-1][:20]})"

                                video_data = {
                                    "url": clean_url,
                                    "title": title[:100],
                                    "scraped_at": time.strftime("%H:%M:%S")
                                }

                                if self.on_video_found:
                                    self.on_video_found(video_data)

                        except Exception:
                            continue

                    self.log("info", f"Lần cuộn #{scroll_count}/{self.max_scrolls}: Bóc tách thêm {new_found_in_step} liên kết mới (Tổng cộng: {len(self.discovered_urls)}).")

                    if new_found_in_step == 0:
                        no_new_links_streak += 1
                        if no_new_links_streak >= 4:
                            self.log("info", "Đã đạt tới đáy trang (không có video mới sau 4 lần cuộn liên tiếp).")
                            break
                    else:
                        no_new_links_streak = 0

                    # Cuộn dần xuống đáy trang (Smooth Scroll)
                    page.evaluate("() => window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1.8)

                    new_page_height = page.evaluate("() => document.body.scrollHeight")
                    if new_page_height == last_page_height and no_new_links_streak >= 3:
                        # Thử ép cuộn thêm một chút
                        page.evaluate("() => window.scrollBy(0, -200);")
                        time.sleep(0.5)
                        page.evaluate("() => window.scrollTo(0, document.body.scrollHeight);")
                    last_page_height = new_page_height

                browser.close()
                if self.stop_requested:
                    self.log("warn", "Quá trình quét đã được dừng bởi người dùng.")

        except PlaywrightTimeoutError:
            self.log("error", "Thời gian chờ trang tải quá lâu (Timeout).")
        except Exception as e:
            self.log("error", f"Lỗi không xác định trong Scraper: {str(e)}")
        finally:
            if self.on_finished:
                self.on_finished()
