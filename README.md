# Disk Usage Monitor (Bash)  

A small Bash script that checks disk usage for specified mount points and logs or sends an alert when usage exceeds a configured threshold.  

## Features  

- Monitor multiple mount points (e.g., `/`, `/home`, `/boot`)  
- Log status to a file  
- Optional email alerts (requires `mail` / `mailutils` configured)  
- Suitable for lightweight system monitoring on Linux  

## Usage  

1. Make the script executable:  

   ```bash
   chmod +x disk_monitor.sh
   ```

2. Edit the configuration variables at the top of `disk_monitor.sh`:  

- `THRESHOLD` — percentage (e.g., 80)  
- `EMAIL` — email address to send alerts to (leave blank to disable)  
- `LOG_FILE` — path to log file (default `/var/log/disk_usage_monitor.log`)  
- `MOUNT_POINTS` — list of mount points  

3. Run manually:  

   ```bash
   sudo ./disk_monitor.sh
   ```

4. Schedule with cron (example: run every hour):  

   ```bash
   0 * * * * /path/to/disk_monitor.sh
   ```

## Email alerts  

To enable email alerts you may need to install `mailutils` and configure Postfix or another MTA:  

```bash
sudo apt install mailutils
sudo dpkg-reconfigure postfix
```

Set `EMAIL` at the top of the script to your email address.  

## Notes  

- This project is a compact utility aimed at learning shell scripting and basic system monitoring. It should be adapted for production use (logging rotation, better error handling, secure mail configuration).  

## Author  

Mohammadamin (Amin) Jahanimajd — BSc Data Analysis
