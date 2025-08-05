# ⚡ E-Bill Tracker

A sleek, dark-themed desktop application to track and visualize your electricity meter readings and costs. Designed for individuals and households who want control over their power consumption — with elegant visuals and insightful analytics.

---

## 🚀 Features

- 🔢 **Meter Reading Entry** – Log new electricity meter readings with ease.
- 💰 **Bill Estimation** – Auto-calculates your monthly electricity cost (₹12/unit default).
- 📅 **Date Filters** – View data from all time, this month, this year, or a custom range.
- 📊 **Analytics Dashboard** – Visual insights into daily, weekly, monthly, and yearly usage.
- 🌙 **Dark Mode UI** – Clean, modern design with smooth visuals.
- 💾 **Local Storage** – No internet required. All data is saved locally.
- 🔐 **Data Reset with Password** – Prevents accidental deletion.

---

## 💻 How to Use

### 🧊 Option 1: Run the `.exe` (Recommended for most users)

1. Download the file from the GitHub Repo.

2. Double-click the `.exe` to launch the app – no installation needed.

> ⚠️ If Windows shows a SmartScreen warning, click **"More Info" → "Run Anyway"**. This is common for unsigned apps.

---

### 🛠️ Option 2: Run from Source (For Developers)

#### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/e-bill-tracker.git
cd e-bill-tracker
```

#### 2. Install Dependencies

```bash
pip install PyQt5 matplotlib
```

#### 3. Run the App

```bash
python electricity_bill.py
```

---

## 🧑‍💻 Developer

**Developed by:** Firoz Al Amin  
📧 Email: [firoz@xtilestudio.com](mailto:firoz@xtilestudio.com)  
🌐 Website: [imfro.vercel.app](https://imfro.vercel.app)

---

## 📄 License

MIT License — Free for personal and commercial use.

---

## 📦 Optional: Create Your Own `.exe`

If you'd like to build the app yourself:

```bash
pip install pyinstaller
pyinstaller --onefile --windowed electricity_bill.py --icon=icon.ico
```

The `.exe` will be inside the `dist/` folder.

---
