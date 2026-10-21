# 🎓 Smart Attendance Tracker

A modern, responsive, and beginner-friendly Python web application designed for college students to track attendance, monitor minimum criteria, and calculate bunk margins with precision.

Built with **Python**, **Streamlit**, **SQLite**, **Pandas**, and **Plotly**.

---

## 🌟 Key Features

### 1. 📊 Modern Student Dashboard
- **Overall Metrics**: Instant overview of your total attendance percentage, classes attended, classes missed, and safe buffer.
- **Visual Analytics**: Interactive Donut Gauge chart and Plotly bar charts comparing each subject against your target.
- **Shortage Alerts**: Automatic warning banners highlighting subjects below the minimum attendance requirement.
- **Subject Progress Cards**: Dynamic color-coded cards and progress bars for each course.

### 2. 📝 Flexible Attendance Management
- **Single Class Log**: Record individual sessions with date, status (Present/Absent), and optional remarks/topics.
- **⚡ Quick Daily Multi-Log**: Record attendance for all your timetable courses for the day in a single click.
- **Duplicate Prevention**: Prevents accidental duplicate entries for the same subject and date.
- **Record Corrections**: Edit or remove any previous attendance entry anytime to fix mistakes.

### 3. 🧮 Smart Attendance & Bunk Calculator
- **Custom Target**: Configurable minimum target percentage (defaults to **75%**, adjustable up to 100%).
- **Consecutive Classes to Attend**: Exact formula calculating how many classes you must attend in a row to reach your target.
- **Safe Bunk Margin**: Calculates exactly how many consecutive classes you can skip while remaining in the safe zone.
- **🔮 What-If Simulator**: Experiment with hypothetical future attendance numbers and immediately see your projected percentage.
- **Mathematical Breakdown**: Built-in formula explanations and proofs.

### 4. 📚 Curriculum & Subject Management
- Add semester courses with subject names and codes (e.g., `CS201 - Data Structures`).
- Edit existing subjects and delete courses (with automatic cascade deletion of related records).
- Case-insensitive duplicate name prevention.

### 5. 📋 History & CSV Export
- Filter records by subject, status (Present/Absent), or date.
- One-click **CSV export** for offline backup or opening in Excel / Google Sheets.

### 6. 💾 Zero-Configuration Persistent Storage
- Built on **SQLite**.
- Automatically initializes tables (`subjects`, `attendance_records`, `settings`) on startup.
- All data is safely preserved across restarts.

---

## 📁 Project Architecture

```text
smartattendancetracker/
├── app.py                 # Streamlit web application & user interface
├── database.py            # SQLite schema, connection management & CRUD queries
├── calculator.py          # Attendance mathematical formulas & what-if simulator
├── requirements.txt       # Project dependencies
├── test_calculator.py     # Unit tests for attendance & bunk calculations
├── test_db.py             # Unit tests for SQLite database operations
├── test_integration.py    # End-to-end integration test of student semester flow
├── .gitignore             # Git ignore rules for virtual environments and cache
└── README.md              # Comprehensive documentation and project guide
```

---

## 🚀 Quickstart Guide

### 1. Prerequisites
Ensure you have **Python 3.10+** installed on your computer.

### 2. Installation
Open your terminal or PowerShell inside the project directory and run:

```bash
pip install -r requirements.txt
```

### 3. Run the Application
Start the Streamlit application with:

```bash
streamlit run app.py
```

The web dashboard will automatically open in your default browser at:
`http://localhost:8501`

---

## 📱 How to Access from Your Android Phone

You can access and use this dashboard directly on your phone in two ways:

### Method A: Local Wi-Fi (No deployment required)
1. Ensure your laptop and Android phone are connected to the **same Wi-Fi network**.
2. Find your laptop's local IP address:
   - On Windows: Run `ipconfig` in Command Prompt / PowerShell and look for **IPv4 Address** (e.g., `192.168.1.4`).
3. Run the app with:
   ```bash
   streamlit run app.py --server.address 0.0.0.0
   ```
4. Open Chrome or any browser on your Android phone and visit:
   `http://<YOUR_LAPTOP_IP>:8501` (e.g., `http://192.168.1.4:8501`).
5. (Optional) In Chrome on Android, tap the three dots `⋮` and select **"Add to Home screen"** to install it like a native mobile app!

---

### Method B: Deploy Free Online (Streamlit Community Cloud)
To access the app anywhere on mobile data without keeping your laptop on:
1. Push this project to a GitHub repository (see instructions below).
2. Go to [share.streamlit.io](https://share.streamlit.io/) and sign in with GitHub.
3. Click **"New app"**, select your repository, branch (`main`), and main file (`app.py`).
4. Click **"Deploy!"**. In 2 minutes, you will receive a public HTTPS link (e.g., `https://smart-attendance.streamlit.app`) accessible 24/7 on your phone.

---

## 🐙 How to Upload to GitHub

Follow these steps to upload your project to your GitHub profile:

1. Open PowerShell / Command Prompt inside the `smartattendancetracker` folder:
   ```bash
   git init
   git add .
   git commit -m "Initial commit: Smart Attendance Tracker application"
   ```
2. Create a new repository on [GitHub](https://github.com/new) named `smart-attendance-tracker`. (Leave "Initialize with README" unchecked).
3. Link your local project to GitHub and push:
   ```bash
   git branch -M main
   git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/smart-attendance-tracker.git
   git push -u origin main
   ```

---

## 🧪 Running Automated Tests

All calculation rules, edge cases, and database transactions are covered with unit tests:

```bash
python -m pytest test_calculator.py test_db.py test_integration.py -v
```

All 11 test cases pass, verifying:
- Zero classes held
- 100% attendance & safe bunk margin
- Attendance shortage & consecutive classes required
- Ceiling handling for fractional classes
- Mathematical impossibility of 100% target once a class is missed
- Database CRUD and duplicate rejection
- End-to-end semester simulation

---

## 🧠 Beginner Learning Mode (How It Works)

### 1. The Attendance Formulas

Let:
- $P$ = Classes attended (**Present**)
- $T$ = Total classes held
- $C$ = Target attendance percentage (e.g., $75\%$)

#### A. How many consecutive classes must I attend? ($x$)
When attendance is below target ($\frac{P}{T} < \frac{C}{100}$), we need:
$$\frac{P + x}{T + x} \ge \frac{C}{100}$$
Solving for $x$:
$$100(P + x) \ge C(T + x)$$
$$100P + 100x \ge CT + Cx$$
$$x(100 - C) \ge CT - 100P$$
$$x = \left\lceil \frac{C \cdot T - 100 \cdot P}{100 - C} \right\rceil$$

> **Python Implementation**: Implemented in [`calculator.py`](file:///c:/Users/Manasa/OneDrive/Desktop/smartattendancetracker/calculator.py) using `math.ceil()`.

#### B. How many classes can I safely miss / bunk? ($y$)
When attendance is at or above target ($\frac{P}{T} \ge \frac{C}{100}$), we find how many future classes $y$ you can miss:
$$\frac{P}{T + y} \ge \frac{C}{100}$$
$$100 \cdot P \ge C(T + y)$$
$$C \cdot y \le 100 \cdot P - C \cdot T$$
$$y = \left\lfloor \frac{100 \cdot P - C \cdot T}{C} \right\rfloor$$

> **Python Implementation**: Implemented in [`calculator.py`](file:///c:/Users/Manasa/OneDrive/Desktop/smartattendancetracker/calculator.py) using `math.floor()`.

---

### 2. How SQLite Stores Records
- SQLite is a serverless, file-based SQL database built into Python's standard library (`import sqlite3`).
- In [`database.py`](file:///c:/Users/Manasa/OneDrive/Desktop/smartattendancetracker/database.py), we use a Python context manager (`@contextmanager def db_session(...)`) to guarantee that:
  - Changes are committed automatically (`conn.commit()`).
  - Foreign keys are enforced (`PRAGMA foreign_keys = ON;`).
  - Connections are closed reliably, preventing file locks on Windows.
- Parameterized queries (`cursor.execute("SELECT ... WHERE key = ?", (key,))`) prevent SQL injection attacks.

---

### 3. How Streamlit Works
- Streamlit transforms Python scripts into interactive web apps.
- When an interactive widget (slider, button, text input) changes, Streamlit reruns the script from top to bottom.
- Data persistence is achieved by reading and writing to SQLite, ensuring no data is lost between script reruns or page reloads.

---

## 🛠️ How to Add New Features Yourself

Here are great ideas for extending this mini-project to make your resume stand out even more:

1. **Timetable / Schedule Integration**:
   - Add a `timetable` table in SQLite linking subjects to days of the week (e.g., Monday has OS, DS, Maths).
2. **Attendance Target per Subject**:
   - Allow setting different targets for theory (e.g., 75%) vs labs (e.g., 85%).
3. **Medical Leave Waiver**:
   - Add an "Excused / Medical" status that excludes specific classes from the total count.
4. **Push / Email Notifications**:
   - Use Python's `smtplib` to send an automated warning email when attendance drops below 75%.

---

## 📄 License
This project is open-source and free to use for educational purposes.
