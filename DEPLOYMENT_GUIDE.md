# 📝 Hướng Dẫn Deploy lên Render

Hướng dẫn chi tiết để deploy ứng dụng Todo lên Render.com (nền tảng miễn phí).

## 📋 Yêu Cầu
- Tài khoản GitHub (code đã được push lên repo)
- Tài khoản Render.com (đăng ký miễn phí tại https://render.com)

## 🚀 Các Bước

### 1️⃣ Push Code lên GitHub
```bash
git add .
git commit -m "Prepare for deployment: add Procfile, runtime.txt, gunicorn"
git push origin master
```

### 2️⃣ Đăng Ký Render.com
- Truy cập https://render.com
- Click "Sign up"
- Đăng nhập với GitHub account (nên dùng GitHub để dễ kết nối)

### 3️⃣ Tạo Web Service
1. Từ Dashboard Render, click **"New +"** → **"Web Service"**
2. Chọn GitHub repository của bạn
3. Điền thông tin:
   - **Name**: `todo-app` (hoặc tên bất kỳ)
   - **Environment**: `Python 3`
   - **Region**: Chọn gần bạn nhất (Singapore, Tokyo)
   - **Branch**: `master` (hoặc `main`)
   - **Build Command**: 
     ```
     pip install --upgrade pip && pip install -r requirements.txt
     ```
   - **Start Command**: 
     ```
     gunicorn --workers 4 --bind 0.0.0.0:${PORT} app.main:app
     ```

### 4️⃣ Tạo PostgreSQL Database (Render)
1. Từ Dashboard, click **"New +"** → **"PostgreSQL"**
2. Điền:
   - **Name**: `todo-db`
   - **Region**: Cùng region với Web Service
   - **PostgreSQL Version**: 15 (hoặc mới nhất)
3. Click **"Create Database"**
4. Copy connection string (dạng `postgresql://user:password@host/db`)

### 5️⃣ Cấu Hình Environment Variables
1. Quay lại Web Service, vào tab **"Environment"**
2. Thêm các biến:

| Key | Value |
|-----|-------|
| `DATABASE_URL` | Paste connection string từ bước 4 |
| `SECRET_KEY` | Tạo key ngẫu nhiên (dùng `openssl rand -hex 32`) |
| `ENVIRONMENT` | `production` |
| `ALLOWED_HOSTS` | `your-app-name.onrender.com,localhost` |

### 6️⃣ Deploy & Chờ
1. Render sẽ tự động deploy khi có push mới
2. Xem logs: vào **"Logs"** tab để kiểm tra quá trình
3. Sau khi build thành công, app sẽ có URL: `https://your-app-name.onrender.com`

## 🔄 Cập Nhật Sau Này
Mỗi lần bạn push code lên `master`, Render sẽ tự động rebuild và deploy!

```bash
# Thay đổi code cục bộ
git add .
git commit -m "Update features"
git push origin master
# Render sẽ tự động deploy!
```

## 🐛 Troubleshooting

### Build Fails (Lỗi Build)
- Kiểm tra logs: xem thông báo lỗi cụ thể
- Đảm bảo `requirements.txt` có tất cả dependencies
- Kiểm tra Python version trong `runtime.txt`

### Database Connection Error
- Kiểm tra `DATABASE_URL` trong Environment Variables
- Đảm bảo PostgreSQL instance được tạo cùng region
- Chạy migrations nếu cần: `alembic upgrade head`

### Static Files Not Loading
- Kiểm tra biến `ENVIRONMENT` có đúng không
- BuildCommand phải chạy `pip install -r requirements.txt`

### App Crash Sau Deploy
- Kiểm hawk logs chi tiết
- Đảm bảo `.env` variables đúng
- Test local trước: `python -m uvicorn app.main:app --reload`

## 📱 Truy Cập Ứng Dụng

Sau khi deploy thành công:
- Web: `https://your-app-name.onrender.com`
- Login: `/api/v1/auth/login-page`
- Dashboard: `/dashboard`

## 💡 Tips
- Dùng **Free** plan của Render (Free Web + Free PostgreSQL)
- Project free sẽ sleep nếu không dùng 15 phút, đợi ~30s khi load lại
- Nếu muốn 24/7, upgrade thành Paid Plan
- Backup database thường xuyên nếu data quan trọng

## ❓ Cần Giúp?
- Documentation Render: https://render.com/docs
- FastAPI + Gunicorn: https://fastapi.tiangolo.com/deployment/
- PostgreSQL connection: https://www.postgresql.org/docs/
