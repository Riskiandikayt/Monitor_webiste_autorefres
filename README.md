# 🌐 WebMonitor — 24/7 URL Monitor for Termux
> Auto Refresh & Website Health Checker | v2.0 ELITE Edition

```
 ██╗    ██╗███████╗██████╗ ███╗   ███╗ ██████╗ ███╗   ██╗██╗████████╗ ██████╗ ██████╗ 
 ██║    ██║██╔════╝██╔══██╗████╗ ████║██╔═══██╗████╗  ██║██║╚══██╔══╝██╔═══██╗██╔══██╗
 ██║ █╗ ██║█████╗  ██████╔╝██╔████╔██║██║   ██║██╔██╗ ██║██║   ██║   ██║   ██║██████╔╝
 ██║███╗██║██╔══╝  ██╔══██╗██║╚██╔╝██║██║   ██║██║╚██╗██║██║   ██║   ██║   ██║██╔══██╗
 ╚███╔███╔╝███████╗██████╔╝██║ ╚═╝ ██║╚██████╔╝██║ ╚████║██║   ██║   ╚██████╔╝██║  ██║
  ╚══╝╚══╝ ╚══════╝╚═════╝ ╚═╝     ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚═╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝
```

---

## ✨ Fitur Lengkap

| Fitur | Status |
|---|---|
| Auto refresh 24/7 tanpa henti | ✅ |
| Multi URL (monitor banyak website) | ✅ |
| HTTP Status Code | ✅ |
| Page Title & Meta Description | ✅ |
| Server Info | ✅ |
| Response Time + Speed Bar | ✅ |
| Last Check Time | ✅ |
| IP Address resolver | ✅ |
| SSL Info (valid, issuer, expiry) | ✅ |
| Full HTTP Headers | ✅ |
| Auto-retry jika koneksi error | ✅ |
| Notifikasi DOWN/RECOVERED | ✅ |
| Simpan log ke file .txt | ✅ |
| Background mode (nohup) | ✅ |
| Interval custom (1s / 5s / 10s / 30s / bebas) | ✅ |
| Tampilan terminal modern + warna | ✅ |
| Uptime percentage per URL | ✅ |
| Auto-install dependencies | ✅ |

---

## 🚀 Quick Start

### 1. Install semua dependency
```bash
bash install.sh
```

### 2. Jalankan monitor
```bash
python3 monitor.py
```

### 3. Ikuti prompt interaktif
```
› URL #1: https://google.com
› URL #2: https://github.com
› URL #3:              ← kosongkan untuk selesai

Pilih interval refresh:
  [1] 1 detik   (aggressive)
  [2] 5 detik   (normal)      ← default
  [3] 10 detik  (moderate)
  [4] 30 detik  (light)
  [5] Custom

› Tekan Ctrl+C untuk berhenti kapan saja
```

---

## 📱 Background Mode (Termux)

Agar tetap berjalan setelah Termux diminimalkan:

```bash
# Step 1 — Acquire wakelock agar Android tidak kill proses
termux-wake-lock

# Step 2 — Jalankan di background dengan nohup
nohup python3 monitor.py > session_output.log 2>&1 &

# Step 3 — Lihat PID proses
echo "PID: $!"

# Cek apakah masih berjalan
ps aux | grep monitor.py

# Baca output realtime
tail -f session_output.log

# Stop background process
kill $(pgrep -f monitor.py)

# Release wakelock saat selesai
termux-wake-unlock
```

---

## 📊 Contoh Output

```
╭─ 1/2  https://example.com ─────────────────────────────────╮
│                                                              │
│  🌐  URL              https://example.com                   │
│  📊  Status           ✔ 200 OK                              │
│  ⚡  Response Time    ██░░░ 245ms                           │
│  🕐  Last Check       2025-01-15 14:32:01                   │
│  🔢  Check #          42                                    │
│  📡  IP Address       93.184.216.34                         │
│  📄  Page Title       Example Domain                        │
│  📝  Meta Desc        This domain is for use in examples... │
│  🖥️  Server           ECS (nyb/1D20)                        │
│  🔒  SSL              ✔ Valid — 287d left — DigiCert Inc    │
│                                                              │
│  ── HTTP Headers ──                                          │
│  Content-Type         text/html; charset=UTF-8              │
│  Cache-Control        max-age=604800                        │
│  ...                                                         │
│                                                              │
╰──────────────────────────────────────────────────────────────╯
  Uptime: 100.0% | OK 42 | ERR 0 | Next check in 5s
```

---

## 📁 File Output

```
webmonitor/
├── monitor.py                    ← Script utama
├── install.sh                    ← Auto-installer
├── README.md                     ← Dokumentasi ini
└── webmonitor_log_YYYYMMDD_HHMMSS.txt   ← Log otomatis (dibuat saat run)
```

### Format Log (.txt)
```
[2025-01-15 14:32:01] Session started | URLs: [...] | interval: 5.0s
[2025-01-15 14:32:06] [CHECK] https://example.com | status=200 | ms=245.3 | title=Example Domain | error=None
[2025-01-15 14:32:11] [ALERT] DOWN: https://example.com — Connection Error
[2025-01-15 14:32:21] [RECOVERED] https://example.com
[2025-01-15 14:35:00] Session ended by user.
```

---

## ⚙️ Requirements

| Package | Versi | Kegunaan |
|---|---|---|
| Python | 3.8+ | Runtime |
| requests | latest | HTTP request |
| beautifulsoup4 | latest | HTML parsing |
| rich | latest | Terminal UI |

> **Auto-install:** Semua dependency terinstall otomatis saat pertama kali menjalankan `monitor.py` atau `install.sh`

---

## 🛠️ Manual Install (jika auto-install gagal)

```bash
# Update Termux packages
pkg update && pkg upgrade -y

# Install Python
pkg install python -y

# Install pip packages
pip install requests beautifulsoup4 rich lxml
```

---

## ❓ Troubleshooting

**Q: `pkg: command not found`**  
A: Pastikan dijalankan di Termux, bukan terminal lain.

**Q: SSL Error untuk beberapa website**  
A: Normal untuk website dengan sertifikat self-signed. Monitor akan tetap berjalan.

**Q: Proses mati saat layar mati**  
A: Gunakan `termux-wake-lock` sebelum menjalankan.

**Q: Output terlalu banyak di terminal**  
A: Redirect ke log: `python3 monitor.py 2>&1 | tee output.log`

**Q: Ingin reset statistik tanpa restart**  
A: Tekan `Ctrl+C` dan jalankan ulang.

---

## 📜 License
Free to use — WebMonitor v2.0 ELITE | Built for Termux
