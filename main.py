"""
WinBatch Video Downloader - Giao diện chính (GUI)
Được phát triển bằng CustomTkinter hỗ trợ đa nền tảng và Dark/Light mode.
Tác giả: DevOps Engineer
Phiên bản: 1.0.0
"""

import os
import sys
import threading
import queue
from datetime import datetime
import customtkinter as ctk
from tkinter import filedialog, messagebox

# Import các module lõi
from scraper import ChannelScraper
from downloader import BatchDownloader

# Cấu hình giao diện CustomTkinter
ctk.set_appearance_mode("Dark")       # Chế độ mặc định: Dark / Light / System
ctk.set_default_color_theme("blue")  # Themes: "blue", "green", "dark-blue"


class WinBatchApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Cấu hình cửa sổ chính
        self.title("WinBatch Video Downloader v1.0.0")
        self.geometry("1100;780")
        self.minsize(980, 680)

        # Biến trạng thái (State Variables)
        self.scraped_videos = []          # Danh sách video đã quét được
        self.checkbox_vars = {}           # Dict lưu trữ trạng thái checkbox của từng video
        self.is_scraping = False
        self.is_downloading = False
        self.ui_queue = queue.Queue()     # Queue giao tiếp thread-safe giữa worker thread và GUI

        # Instances của worker
        self.scraper_worker = None
        self.downloader_worker = None

        # Thư mục lưu mặc định
        default_dl_dir = os.path.join(os.path.expanduser("~"), "Downloads", "WinBatchVideos")
        self.save_dir_var = ctk.StringVar(value=default_dl_dir)

        # Xây dựng bố cục giao diện
        self._build_ui()

        # Bắt đầu vòng lặp kiểm tra queue cập nhật UI
        self.after(100, self._process_ui_queue)

    def _build_ui(self):
        # 1. Header & Controls trên cùng
        self.header_frame = ctk.CTkFrame(self, corner_radius=10)
        self.header_frame.pack(fill="x", padx=15, pady=(15, 10))

        title_label = ctk.CTkLabel(
            self.header_frame,
            text="WinBatch Video Downloader",
            font=ctk.CTkFont(size=22, weight="bold")
        )
        title_label.pack(side="left", padx=15, pady=10)

        # Công tắc Dark / Light Mode
        self.theme_switch = ctk.CTkOptionMenu(
            self.header_frame,
            values=["Dark", "Light", "System"],
            command=self._change_appearance_mode,
            width=110
        )
        self.theme_switch.set("Dark")
        self.theme_switch.pack(side="right", padx=15, pady=10)

        mode_label = ctk.CTkLabel(self.header_frame, text="Giao diện:")
        mode_label.pack(side="right", padx=(10, 5))

        # 2. Khung nhập liệu URL & Cấu hình quét
        self.input_card = ctk.CTkFrame(self, corner_radius=10)
        self.input_card.pack(fill="x", padx=15, pady=5)

        url_label = ctk.CTkLabel(self.input_card, text="URL Kênh / Danh sách phát:", font=ctk.CTkFont(weight="bold"))
        url_label.grid(row=0, column=0, padx=15, pady=(12, 4), sticky="w")

        self.url_entry = ctk.CTkEntry(
            self.input_card,
            placeholder_text="https://www.youtube.com/@channel/videos hoặc link TikTok, Facebook, v.v...",
            width=620,
            height=36
        )
        self.url_entry.grid(row=1, column=0, padx=15, pady=(0, 12), sticky="ew")

        # Cài đặt số lần cuộn tối đa
        self.scroll_limit_label = ctk.CTkLabel(self.input_card, text="Giới hạn cuộn (Scrolls):")
        self.scroll_limit_label.grid(row=0, column=1, padx=5, pady=(12, 4), sticky="w")

        self.scroll_limit_entry = ctk.CTkEntry(self.input_card, width=110, height=36)
        self.scroll_limit_entry.insert(0, "30")
        self.scroll_limit_entry.grid(row=1, column=1, padx=5, pady=(0, 12), sticky="w")

        # Nút Quét / Dừng Quét
        self.btn_scrape = ctk.CTkButton(
            self.input_card,
            text="🔍 Bắt đầu quét",
            command=self._start_scrape_thread,
            fg_color="#1f6aa5",
            hover_color="#144870",
            height=36,
            font=ctk.CTkFont(weight="bold")
        )
        self.btn_scrape.grid(row=1, column=2, padx=10, pady=(0, 12))

        self.btn_stop_scrape = ctk.CTkButton(
            self.input_card,
            text="⏹ Dừng quét",
            command=self._stop_scrape,
            fg_color="#a83232",
            hover_color="#7a2222",
            state="disabled",
            height=36,
            width=90
        )
        self.btn_stop_scrape.grid(row=1, column=3, padx=(0, 15), pady=(0, 12))

        self.input_card.columnconfigure(0, weight=1)

        # 3. Tùy chọn tải & Thư mục đích
        self.options_card = ctk.CTkFrame(self, corner_radius=10)
        self.options_card.pack(fill="x", padx=15, pady=5)

        dir_label = ctk.CTkLabel(self.options_card, text="Thư mục lưu:", font=ctk.CTkFont(weight="bold"))
        dir_label.grid(row=0, column=0, padx=15, pady=8, sticky="w")

        self.dir_entry = ctk.CTkEntry(self.options_card, textvariable=self.save_dir_var, height=32)
        self.dir_entry.grid(row=0, column=1, padx=5, pady=8, sticky="ew")

        self.btn_browse = ctk.CTkButton(
            self.options_card,
            text="📂 Chọn thư mục",
            width=120,
            height=32,
            command=self._browse_directory
        )
        self.btn_browse.grid(row=0, column=2, padx=10, pady=8)

        # Số luồng song song (Multi-threading)
        threads_label = ctk.CTkLabel(self.options_card, text="Số luồng (Threads):")
        threads_label.grid(row=0, column=3, padx=(10, 5), pady=8)

        self.threads_combo = ctk.CTkComboBox(
            self.options_card,
            values=["2", "4", "6", "8", "12", "16"],
            width=75,
            height=32
        )
        self.threads_combo.set("4")
        self.threads_combo.grid(row=0, column=4, padx=5, pady=8)

        # Chất lượng video
        quality_label = ctk.CTkLabel(self.options_card, text="Định dạng:")
        quality_label.grid(row=0, column=5, padx=(10, 5), pady=8)

        self.quality_combo = ctk.CTkComboBox(
            self.options_card,
            values=["Tốt nhất (Best MP4)", "1080p Full HD", "720p HD", "Chỉ âm thanh (MP3)"],
            width=140,
            height=32
        )
        self.quality_combo.set("Tốt nhất (Best MP4)")
        self.quality_combo.grid(row=0, column=6, padx=(5, 15), pady=8)

        self.options_card.columnconfigure(1, weight=1)

        # 4. Khu vực Danh sách Video đã bóc tách (Scrollable Checkbox List)
        self.list_container = ctk.CTkFrame(self, corner_radius=10)
        self.list_container.pack(fill="both", expand=True, padx=15, pady=5)

        # Thanh công cụ bảng (Actions bar)
        self.table_toolbar = ctk.CTkFrame(self.list_container, fg_color="transparent")
        self.table_toolbar.pack(fill="x", padx=10, pady=(8, 4))

        self.list_title = ctk.CTkLabel(
            self.table_toolbar,
            text="Danh sách liên kết quét được (0 mục)",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.list_title.pack(side="left")

        self.btn_select_all = ctk.CTkButton(
            self.table_toolbar,
            text="✔ Chọn tất cả",
            width=100,
            height=28,
            command=self._select_all_items
        )
        self.btn_select_all.pack(side="right", padx=(5, 0))

        self.btn_deselect_all = ctk.CTkButton(
            self.table_toolbar,
            text="✖ Bỏ chọn tất cả",
            width=110,
            height=28,
            fg_color="#555555",
            hover_color="#3e3e3e",
            command=self._deselect_all_items
        )
        self.btn_deselect_all.pack(side="right", padx=5)

        # Khung cuộn chứa danh sách video
        self.scrollable_list = ctk.CTkScrollableFrame(self.list_container, label_text="")
        self.scrollable_list.pack(fill="both", expand=True, padx=10, pady=5)

        # 5. Thanh tiến trình & Trạng thái tải
        self.progress_frame = ctk.CTkFrame(self, corner_radius=10)
        self.progress_frame.pack(fill="x", padx=15, pady=5)

        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, height=14)
        self.progress_bar.pack(fill="x", padx=15, pady=(10, 4))
        self.progress_bar.set(0.0)

        self.status_label = ctk.CTkLabel(
            self.progress_frame,
            text="Sẵn sàng thực hiện. Nhập URL và nhấn 'Bắt đầu quét'.",
            text_color="#888888"
        )
        self.status_label.pack(side="left", padx=15, pady=(0, 8))

        self.btn_download = ctk.CTkButton(
            self.progress_frame,
            text="⬇ Bắt đầu tải các mục đã chọn",
            command=self._start_download_thread,
            fg_color="#2b8a3e",
            hover_color="#237032",
            height=34,
            font=ctk.CTkFont(weight="bold")
        )
        self.btn_download.pack(side="right", padx=15, pady=(0, 8))

        self.btn_stop_download = ctk.CTkButton(
            self.progress_frame,
            text="⏹ Dừng tải",
            command=self._stop_download,
            fg_color="#a83232",
            hover_color="#7a2222",
            state="disabled",
            height=34,
            width=90
        )
        self.btn_stop_download.pack(side="right", padx=(0, 5), pady=(0, 8))

        # 6. Hộp Log giám sát hệ thống (Console logs)
        self.log_frame = ctk.CTkFrame(self, corner_radius=10)
        self.log_frame.pack(fill="x", padx=15, pady=(5, 15))

        log_top = ctk.CTkFrame(self.log_frame, fg_color="transparent")
        log_top.pack(fill="x", padx=10, pady=(6, 2))

        ctk.CTkLabel(log_top, text="Nhật ký hoạt động (System Logs):", font=ctk.CTkFont(weight="bold")).pack(side="left")
        ctk.CTkButton(log_top, text="Xóa log", width=65, height=22, command=self._clear_logs).pack(side="right")

        self.log_textbox = ctk.CTkTextbox(self.log_frame, height=90, font=ctk.CTkFont(family="Consolas", size=11))
        self.log_textbox.pack(fill="x", padx=10, pady=(2, 8))
        self.log_textbox.configure(state="disabled")

        self._log("info", "Ứng dụng WinBatch Video Downloader đã khởi tạo thành công.")

    def _change_appearance_mode(self, new_mode: str):
        ctk.set_appearance_mode(new_mode)

    def _browse_directory(self):
        selected_dir = filedialog.askdirectory(initialdir=self.save_dir_var.get())
        if selected_dir:
            self.save_dir_var.set(selected_dir)
            self._log("info", f"Thư mục lưu được đổi thành: {selected_dir}")

    def _log(self, level: str, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = {
            "info": "[INFO]",
            "success": "[SUCCESS]",
            "warn": "[WARN]",
            "error": "[ERROR]"
        }.get(level, "[LOG]")

        line = f"{timestamp} {prefix} {message}\n"
        self.ui_queue.put(("log", line))

    def _process_ui_queue(self):
        """Hàm rút dữ liệu từ queue để cập nhật an toàn vào Tkinter main thread."""
        try:
            while not self.ui_queue.empty():
                msg_type, payload = self.ui_queue.get_nowait()

                if msg_type == "log":
                    self.log_textbox.configure(state="normal")
                    self.log_textbox.insert("end", payload)
                    self.log_textbox.see("end")
                    self.log_textbox.configure(state="disabled")

                elif msg_type == "video_found":
                    self._add_video_to_ui(payload)

                elif msg_type == "scrape_finished":
                    self.is_scraping = False
                    self.btn_scrape.configure(state="normal")
                    self.btn_stop_scrape.configure(state="disabled")
                    total = len(self.scraped_videos)
                    self.status_label.configure(text=f"Hoàn thành quét: Tìm thấy {total} liên kết.")
                    self._log("success", f"Hoàn tất quét kênh. Tổng cộng: {total} liên kết.")

                elif msg_type == "download_progress":
                    # payload: dict(completed=X, total=Y, current_title=Z)
                    comp = payload["completed"]
                    tot = payload["total"]
                    pct = (comp / tot) if tot > 0 else 0.0
                    self.progress_bar.set(pct)
                    self.status_label.configure(
                        text=f"Đang tải ({comp}/{tot}): {payload.get('current_title', '')}"
                    )

                elif msg_type == "download_finished":
                    self.is_downloading = False
                    self.btn_download.configure(state="normal")
                    self.btn_stop_download.configure(state="disabled")
                    self.progress_bar.set(1.0)
                    self.status_label.configure(
                        text=f"Hoàn thành tải xuống! Thành công: {payload['success']}, Lỗi: {payload['failed']}"
                    )
                    self._log("success", f"Kết thúc tải hàng loạt: {payload['success']} thành công, {payload['failed']} thất bại.")
                    messagebox.showinfo("Hoàn tất", f"Đã tải xong!\nThành công: {payload['success']}\nThất bại: {payload['failed']}")

        except Exception as e:
            print("Lỗi trong xử lý queue UI:", e)
        finally:
            self.after(100, self._process_ui_queue)

    def _start_scrape_thread(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập URL kênh hoặc danh sách phát!")
            return

        try:
            scroll_limit = int(self.scroll_limit_entry.get())
        except ValueError:
            scroll_limit = 30

        self._clear_video_list()
        self.is_scraping = True
        self.btn_scrape.configure(state="disabled")
        self.btn_stop_scrape.configure(state="normal")
        self.status_label.configure(text="Đang khởi chạy trình duyệt Playwright (Headless)...")
        self._log("info", f"Bắt đầu quét: {url} (Giới hạn cuộn: {scroll_limit})")

        self.scraper_worker = ChannelScraper(
            url=url,
            max_scrolls=scroll_limit,
            on_video_found=lambda item: self.ui_queue.put(("video_found", item)),
            on_log=lambda lvl, msg: self._log(lvl, msg),
            on_finished=lambda: self.ui_queue.put(("scrape_finished", None))
        )

        scrape_thread = threading.Thread(target=self.scraper_worker.run, daemon=True)
        scrape_thread.start()

    def _stop_scrape(self):
        if self.scraper_worker:
            self.scraper_worker.stop()
            self._log("warn", "Đang yêu cầu dừng quét...")
            self.btn_stop_scrape.configure(state="disabled")

    def _clear_video_list(self):
        for widget in self.scrollable_list.winfo_children():
            widget.destroy()
        self.scraped_videos.clear()
        self.checkbox_vars.clear()
        self.list_title.configure(text="Danh sách liên kết quét được (0 mục)")

    def _add_video_to_ui(self, item: dict):
        self.scraped_videos.append(item)
        idx = len(self.scraped_videos) - 1

        var = ctk.BooleanVar(value=True)
        self.checkbox_vars[idx] = var

        row_frame = ctk.CTkFrame(self.scrollable_list, corner_radius=6)
        row_frame.pack(fill="x", padx=5, pady=3)

        chk = ctk.CTkCheckBox(
            row_frame,
            text=f"#{idx + 1} - {item.get('title', 'Không có tiêu đề')[:75]}",
            variable=var,
            font=ctk.CTkFont(size=12)
        )
        chk.pack(side="left", padx=10, pady=8, fill="x", expand=True)

        url_short = item.get("url", "")
        if len(url_short) > 40:
            url_short = url_short[:37] + "..."

        url_lbl = ctk.CTkLabel(row_frame, text=url_short, text_color="#718096", font=ctk.CTkFont(size=11))
        url_lbl.pack(side="right", padx=10)

        self.list_title.configure(text=f"Danh sách liên kết quét được ({len(self.scraped_videos)} mục)")

    def _select_all_items(self):
        for var in self.checkbox_vars.values():
            var.set(True)

    def _deselect_all_items(self):
        for var in self.checkbox_vars.values():
            var.set(False)

    def _start_download_thread(self):
        selected_items = [
            self.scraped_videos[i]
            for i, var in self.checkbox_vars.items()
            if var.get()
        ]

        if not selected_items:
            messagebox.showwarning("Thông báo", "Vui lòng chọn ít nhất 1 video để tải xuống!")
            return

        dest_dir = self.save_dir_var.get().strip()
        if not dest_dir:
            messagebox.showwarning("Thông báo", "Vui lòng chỉ định thư mục lưu!")
            return

        try:
            threads = int(self.threads_combo.get())
        except ValueError:
            threads = 4

        quality = self.quality_combo.get()

        self.is_downloading = True
        self.btn_download.configure(state="disabled")
        self.btn_stop_download.configure(state="normal")
        self.progress_bar.set(0.0)
        self._log("info", f"Bắt đầu tải {len(selected_items)} mục với {threads} luồng song song...")

        self.downloader_worker = BatchDownloader(
            items=selected_items,
            dest_dir=dest_dir,
            max_workers=threads,
            quality_mode=quality,
            on_progress=lambda comp, tot, title: self.ui_queue.put(
                ("download_progress", {"completed": comp, "total": tot, "current_title": title})
            ),
            on_log=lambda lvl, msg: self._log(lvl, msg),
            on_finished=lambda stats: self.ui_queue.put(("download_finished", stats))
        )

        dl_thread = threading.Thread(target=self.downloader_worker.run, daemon=True)
        dl_thread.start()

    def _stop_download(self):
        if self.downloader_worker:
            self.downloader_worker.stop()
            self._log("warn", "Đang dừng tiến trình tải xuống...")
            self.btn_stop_download.configure(state="disabled")

    def _clear_logs(self):
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("1.0", "end")
        self.log_textbox.configure(state="disabled")


if __name__ == "__main__":
    app = WinBatchApp()
    app.mainloop()
