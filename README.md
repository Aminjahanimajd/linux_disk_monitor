# 🚀 Disk Usage Monitor  

A Bash script that monitors disk usage and sends alerts when usage exceeds a configured threshold.  

![Bash](https://img.shields.io/badge/-Bash-%234EAA25?logo=gnu-bash&logoColor=white)  
![Linux](https://img.shields.io/badge/-Linux-%23FCC624?logo=linux&logoColor=black)  
![Ubuntu](https://img.shields.io/badge/-Ubuntu-%23E95420?logo=ubuntu&logoColor=white)  

---

## 📖 Overview  

This script periodically checks disk usage on specified mount points (e.g., `/`, `/home`, `/boot`) and logs the status. If usage exceeds a predefined threshold, it can send email alerts.  

### Features  
✅ Monitors multiple mount points  
✅ Logs disk usage to `/var/log/disk_usage_monitor.log`  
✅ Optional email alerts  
✅ Lightweight and easy to configure  

---

## ⚙️ Installation  

### 1. Clone the Repository  

git clone https://github.com/your-username/disk-usage-monitor.git
cd disk-usage-monitor
2. Make the Script Executable
chmod +x disk_monitor.sh
3. (Optional) Install mailutils for Email Alerts
If you want email alerts, install mailutils:

sudo apt install mailutils
🔧 Configuration
Edit the script (disk_monitor.sh) to configure:

Variable	Description	Default
THRESHOLD	Disk usage percentage threshold (alerts if exceeded)	80
EMAIL	Email address for alerts (leave empty to disable)	""
LOG_FILE	Path to log file	/var/log/disk_usage_monitor.log
MOUNT_POINTS	Disk partitions to monitor	"/ /home /boot"
🚦 Usage
Run Manually
sudo ./disk_monitor.sh
Schedule with Cron (Automated Monitoring)
Add to crontab (crontab -e) to run every hour:

0 * * * * /path/to/disk_monitor.sh
Check Logs
tail -f /var/log/disk_usage_monitor.log
📧 Email Alerts Setup
Install mailutils (if not already installed):

sudo apt install mailutils
Configure Postfix (if needed):

sudo dpkg-reconfigure postfix
(Select "Internet Site" and follow prompts.)

Set EMAIL in the script to your desired address.

🤝 Contributing
Feel free to submit issues or PRs!
