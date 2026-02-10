# 🚂 Deployment Guide - Railway.app

Hướng dẫn chi tiết deploy ứng dụng Todo lên Railway App.

## ✨ Ưu Điểm Railway
- ✅ Tự động detect Python project
- ✅ PostgreSQL included
- ✅ Deploy từ Git (auto-deploy on push)
- ✅ CLI tool (railway CLI)
- ✅ Chính xác hóa tiền gói cước linh hoạt
- ✅ UI/UX tốt

## 🚀 Các Bước

### **Bước 1: Đăng Ký Railway**
1. Vào https://railway.app
2. Click **"Start Project"**
3. Chọn **"GitHub"** (hoặc email)
4. Authorize Railway truy cập GitHub
5. Chọn org/account

### **Bước 2: Tạo Project Mới**
1. Click **"New Project"**
2. Chọn **"Deploy from GitHub repp"**
3. Tìm `maivanquan1406-afk/todo-app`
4. Click **"Deploy"**

### **Bước 3: Configure Application Service**
Railway sẽ tự detect Python project. Kiểm tra:

1. **Service Name**: `todo-app` (hoặc tên tuỳ ý)
2. **Environment**: Python tự detect
3. Check box **"Auto Deploy from GitHub"** ✓

**Xem Logs:**
- Vào tab **"Deployments"**
- Click deployment cuối cùng để xem logs
- Đợi status chuyển sang **"Success ✓"**

### **Bước 4: Thêm PostgreSQL Database**
1. Quay lại Project Dashboard
2. Click **"+ Add"** → **"Database"** → **"PostgreSQL"**
3. Chọn version 14+ (recommend 15)
4. Database được tạo tự động
5. Railway tự thêm `DATABASE_URL` vào environment 🎉

### **Bước 5: Cấu Hình Environment Variables**
Kiểm tra/thêm variables trong tab **"Variables"**:

| Variable | Value | Note |
|----------|-------|------|
| `ENVIRONMENT` | `production` | Tắt DEBUG mode |
| `SECRET_KEY` | Giá trị bảo mật | Tạo từ `python generate_config.py --secret-key` |
| `DATABASE_URL` | Auto từ PostgreSQL | Không cần edit, Railway tự thêm |
| `ALLOWED_HOSTS` | `https://todo-app-xxx.railway.app,localhost` | Thay xxx bằng app name của bạn |

**Lưu ý:** Railway tự thêm `DATABASE_URL` khi kết nối PostgreSQL, bạn không cần copy định nghĩa.

### **Bước 6: Verify Deployment**
1. Xem **"Deployments"** tab - status phải ✅
2. Logs phải có:
   ```
   Database initialized successfully (Environment: production)
   Uvicorn running on 0.0.0.0:PORT
   ```
3. Xem README để lấy app URL:
   ```
   https://todo-app-production-xxxxx.railway.app
   ```

---

## ✅ Testing Deployment

Sau khi deploy xong:

```bash
# Test health
curl https://todo-app-production-xxxxx.railway.app/health

# Test login page
curl https://todo-app-production-xxxxx.railway.app/api/v1/auth/login-page

# Test API docs
https://todo-app-production-xxxxx.railway.app/docs
```

---

## 🔄 Auto-Deploy

Railway tự động deploy mỗi khi bạn push code:

```bash
# Sau khi push lên GitHub
git add .
git commit -m "Feature: improve UI"
git push origin master

# Railway sẽ tự động:
# 1. Nhận push event
# 2. Pull code mới
# 3. Install dependencies từ requirements.txt
# 4. Run start command từ railway.json
# 5. Restart service
```

---

## 🐛 Troubleshooting

### **Build Failed**
- Kiểm tra **Logs** chi tiết
- Đảm bảo `requirements.txt` có tất cả dependencies
- Thử local: `pip install -r requirements.txt`
- Rebuild: Railway > "Rebuild"

### **Database Connection Error**
```
Error: could not connect to server
```
- Chờ PostgreSQL hoàn tất khởi động (~30s)
- Kiểm tra `DATABASE_URL` có đúng không
- Xem PostgreSQL logs
- Rebuild service

### **App không chạy (Port error)**
- Railway tự set `PORT` environment variable
- start command phải dùng `$PORT`
- Kiểm tra `railway.json` có `$PORT` không

### **Static files không load**
- CSS/JS cần từ `/static/` path
- Kiểm tra `app/main.py` mount static folder
- Test: `https://your-app.railway.app/static/style.css`

### **502 Bad Gateway**
- Service crashed, xem logs
- Rebuild service
- Kiểm tra SECRET_KEY có đặt không

---

## 📊 Monitoring

Railway cung cấp:
- **Metrics**: CPU, Memory, Disk usage
- **Logs**: Real-time streaming
- **Deployments**: History of all deploys
- **Integrations**: GitHub webhooks, discord alerts

---

## 💰 Pricing

Railway sử dụng **credit-based pricing**:
- $5 free usage mỗi tháng
- Sau đó tính phí theo usage
- PostgreSQL + Web Service typically $5-15/tháng

---

## 🔐 Security Best Practices

✅ **Làm:**
- [ ] Set `ENVIRONMENT=production`
- [ ] Generate strong `SECRET_KEY`
- [ ] Restrict `ALLOWED_HOSTS`
- [ ] Enable HTTPS (Railway auto enable)
- [ ] Backup database thường xuyên
- [ ] Monitor logs để phát hiện lỗi

❌ **Không làm:**
- Để `DEBUG=True` ở production
- Publish SECRET_KEY lên GitHub
- Dùng default password
- Expose database URL công khai

---

## 📚 Resources

- [Railway Docs](https://railway.app/docs)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [PostgreSQL on Railway](https://docs.railway.app/databases/postgresql)
- [Railway CLI](https://docs.railway.app/cli/commands)

---

**Status:** ✅ Ready for Production
