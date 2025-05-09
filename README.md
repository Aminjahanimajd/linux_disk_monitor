**Disk Usage Monitor (Linux Bash Script)**

** Objective**

Automate the monitoring of disk space on a Linux system and generate alerts if disk usage exceeds a specified threshold.

** Features**

- Monitors root (/) disk usage.
- Configurable usage threshold (default: 80%).
- Logs output to `/var/log/disk_usage_monitor.log`.
- Optional email alert support.

** Usage**

** 1. Clone or download the script**

git clone https://github.com/yourusername/disk-usage-monitor.git
cd disk-usage-monitor

** 2. Make the script executable**

chmod +x disk_monitor.sh

** 3. Run the script manually**

./disk_monitor.sh

**4. Automate with cron (optional)**

To check disk usage every hour, add this line to your crontab (crontab -e):

0 * * * * /path/to/disk_monitor.sh

**Configuration**

You can configure the alert threshold and email by editing the top of the script:

THRESHOLD=80       # Set disk usage threshold percentage
EMAIL="admin@example.com"   # Set to empty string "" to disable email alerts

**Dependencies**

mail (optional, for email alerts)
Install it on Debian/Ubuntu:

sudo apt install mailutils

