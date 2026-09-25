# WinBatch Video Downloader (Windows Desktop App)

Ứng dụng Windows Desktop chuyên nghiệp bóc tách (scrape) danh sách liên kết video hàng loạt từ các kênh mạng xã hội/video bằng **Playwright (Headless)** và tải xuống đa luồng siêu tốc bằng **yt-dlp**.

Giao diện đồ họa hiện đại xây dựng trên **CustomTkinter** với khả năng chuyển đổi giao diện Sáng/Tối linh hoạt.

---

## 🚀 Tính năng nổi bật

- **Giao diện hiện đại (CustomTkinter)**: Hỗ trợ Dark/Light/System theme, không bị giật lag UI khi đang xử lý tác vụ nặng nhờ kiến trúc **Thread-Safe Queue**.
- **Playwright Headless Scraper**:
  - Tự động cuộn trang vô tận (Infinite Scroll) giả lập hành vi người dùng thật.
  - Chuẩn hóa URL, loại bỏ trùng lặp bằng thuật toán băm `set()`.
  - Bắt link theo thời gian thực và đẩy ngay lên bảng chọn mà không cần chờ cuộn hết trang.
- **yt-dlp Batch Downloader**:
  - Hỗ trợ tải đa luồng đồng thời qua `ThreadPoolExecutor` (tùy chỉnh 2-16 threads).
  - Cơ chế `try...except` bọc từng link: lỗi 1 video không bao giờ làm gián đoạn cả danh sách.
  - Tùy chọn chất lượng: Best MP4, 1080p, 720p, hoặc Tách MP3.
- **Tự động hóa CI/CD qua GitHub Actions**:
  - Tự động biên dịch ra file `.zip` chứa bộ chạy Windows mỗi khi `git push`.
  - Không cần cài đặt Python trên máy tính người dùng cuối.

---

## 📁 Cấu trúc Dự án

```text
├── .github/
│   └── workflows/
│       └── build_windows.yml   # Kịch bản GitHub Actions tự động build EXE & nén ZIP
├── main.py                     # Giao diện chính CustomTkinter
├── scraper.py                  # Module Playwright Headless scraper
├── downloader.py               # Module yt-dlp đa luồng tải video
├── requirements.txt            # Danh sách thư viện phụ thuộc
├── build.spec                  # Cấu hình đóng gói PyInstaller
├── run.bat                     # Script chạy nhanh cho môi trường dev Windows
└── README.md                   # Tài liệu hướng dẫn
```

---

## 🛠 Hướng dẫn chạy thử nghiệm tại máy cục bộ (Local)

### Yêu cầu:
- Windows 10/11 64-bit
- Python 3.10 hoặc 3.11

### Các bước:
1. Clone hoặc tải mã nguồn về máy:
   ```bash
   git clone https://github.com/<your-username>/<repo-name>.git
   cd <repo-name>
   ```

2. Tạo môi trường ảo và cài đặt thư viện:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Cài đặt trình duyệt Playwright Chromium:
   ```bash
   playwright install chromium
   ```

4. Chạy ứng dụng:
   ```bash
   python main.py
   ```

---

## 📦 Hướng dẫn Tự động Build bằng GitHub Actions (CI/CD)

### Bước 1: Tạo GitHub Repository
1. Đăng nhập [GitHub.com](https://github.com/) -> Nhấn **New Repository**.
2. Đặt tên repository (ví dụ: `winbatch-video-downloader`), chọn **Public** hoặc **Private**.
3. Không cần tích tạo README vì dự án đã có sẵn.

### Bước 2: Đẩy toàn bộ mã nguồn lên GitHub
Mở Terminal hoặc Command Prompt tại thư mục dự án và chạy các lệnh:
```bash
git init
git add .
git commit -m "feat: Initial release with CustomTkinter, Playwright, yt-dlp & CI/CD"
git branch -M main
git remote add origin https://github.com/<your-username>/<repo-name>.git
git push -u origin main
```

### Bước 3: Xem tiến trình Build và Tải file ZIP
1. Truy cập tab **Actions** trên GitHub repository của bạn.
2. Bạn sẽ thấy workflow **Build Windows Desktop App** đang chạy.
3. Khi hoàn tất (khoảng 3 - 5 phút), nhấn vào lần chạy đó.
4. Cuộn xuống mục **Artifacts** và tải file **`WinBatchDownloader-Windows-x64`** (bên trong chứa file `app-windows.zip`).
5. Giải nén trên máy Windows bất kỳ và nhấp đúp vào **`WinBatchDownloader.exe`** để sử dụng ngay mà không cần cài đặt Python!
