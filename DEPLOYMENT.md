# ReadyUp Bot Deployment Guide

This guide provides step-by-step instructions for deploying the ReadyUp Bot on a DigitalOcean Droplet running Ubuntu 22.04 LTS.

## Step 1: Create and Secure a DigitalOcean Droplet

1.  **Create Droplet:**
    *   Log in to your DigitalOcean account and click "Create" -> "Droplets".
    *   **Image:** Choose **Ubuntu 22.04 (LTS) x64**.
    *   **Plan:** Choose a "Basic" plan. The smallest "Regular" CPU option (e.g., 1 GB RAM / 1 CPU) is more than sufficient for this bot.
    *   **Datacenter Region:** Choose a region geographically close to your server's primary user base.
    *   **Authentication:** Select **SSH Keys** and add your public SSH key. This is significantly more secure than using a password.
    *   **Finalize:** Choose a hostname (e.g., `readyup-bot-server`) and click "Create Droplet".

2.  **Initial Server Setup (Security Best Practices):**
    *   Once the droplet is created, copy its public IP address.
    *   Connect to your server as the `root` user via SSH:
        ```bash
        ssh root@YOUR_DROPLET_IP
        ```
    *   Create a new non-root user (replace `youruser` with a username of your choice):
        ```bash
        adduser youruser
        ```
    *   Give this user `sudo` (administrative) privileges:
        ```bash
        usermod -aG sudo youruser
        ```
    *   Set up a basic firewall (`ufw`) to allow only SSH traffic:
        ```bash
        ufw allow OpenSSH
        ufw enable
        # Press 'y' and Enter to confirm.
        ```
    *   Log out of the root account (`exit`) and log back in as your new, non-root user:
        ```bash
        ssh youruser@YOUR_DROPLET_IP
        ```

## Step 2: Install Bot Dependencies

1.  **Update System Packages:**
    ```bash
    sudo apt update && sudo apt upgrade -y
    ```

2. **Install Python 3.10+ (Ubuntu 22.04 ships with 3.10) plus tooling:**
    ```bash
    sudo apt install python3.10-venv python3-pip -y
    ```

3.  **Install Git:**
    ```bash
    sudo apt install git -y
    ```

## Step 3: Deploy the Bot Code

1.  **Clone Your Repository:**
    ```bash
    git clone https://github.com/JoarEliasson/ready-up.git
    ```

2.  **Navigate into the Project Directory:**
    ```bash
    cd ready-up
    ```

3.  **Set Up the Python Virtual Environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

4.  **Install Project Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

5.  **Create and Configure the Environment File:**
    *   Copy the example: `cp .env.example .env`
    *   Edit the file using a terminal editor like `nano`:
        ```bash
        nano .env
        ```
    *   Fill in all the required values (`DISCORD_TOKEN`, etc.).
    *   Save and exit (`Ctrl+X`, then `Y`, then `Enter`).

## Step 4: Run the Bot as a `systemd` Service

`systemd` is the standard process manager on Ubuntu. This will ensure your bot starts automatically on boot and restarts if it ever crashes.

1. **Edit the `readyup.service` unit file** (full example below).  
   Make sure to update:
   - `User=` / `Group=` – the non-root user you created
   - `WorkingDirectory=` – path to your repo
   - `EnvironmentFile=` – points to your `.env`
   - `ExecStart=` – full path to the venv python and `src/main.py`

2.  **Install and Enable the Service:**
    *   Copy the service file to the systemd system directory:
        ```bash
        sudo cp readyup.service /etc/systemd/system/readyup.service
        ```
    *   Reload the systemd manager to recognize the new service:
        ```bash
        sudo systemctl daemon-reload
        ```
    *   Enable the service to start automatically on system boot:
        ```bash
        sudo systemctl enable readyup.service
        ```
    *   Start the service immediately:
        ```bash
        sudo systemctl start readyup.service
        ```
### Hardened unit file (available in repo `readyup.service`)

```ini
[Unit]
Description=ReadyUp Discord Bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=youruser              # ← change
Group=youruser             # ← change
WorkingDirectory=/home/youruser/ready-up
EnvironmentFile=/home/youruser/ready-up/.env
ExecStart=/home/youruser/ready-up/venv/bin/python3 /home/youruser/ready-up/src/main.py

Restart=on-failure
RestartSec=5s

# ── security hardening ───────────────────────────────────────────────
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full
ProtectHome=true

[Install]
WantedBy=multi-user.target
```

## Step 5: Monitoring and Maintenance

-   **Check Status:** To see if the bot is running correctly:
    ```bash
    sudo systemctl status readyup.service
    ```
-   **View Live Logs:** To watch the bot's console output in real-time:
    ```bash
    sudo journalctl -u readyup.service -f
    ```
-   **Restarting:** If you need to restart the bot for any reason:
    ```bash
    sudo systemctl restart readyup.service
    ```
-   **Updating the Bot Code:**
    1.  SSH into your server: `ssh youruser@YOUR_DROPLET_IP`
    2.  Navigate to the project directory: `cd ready-up`
    3.  Pull the latest changes from your Git repository: `git pull`
    4.  Activate the virtual environment: `source venv/bin/activate`
    5.  Install any new dependencies: `pip install -r requirements.txt`
    6.  Restart the service to apply all changes: `sudo systemctl restart readyup.service`


| Task           | Command                                                                                                             |
|----------------|---------------------------------------------------------------------------------------------------------------------|
| Service status | `sudo systemctl status readyup.service`                                                                             |
| Live logs      | `sudo journalctl -u readyup.service -f`                                                                             |
| Restart        | `sudo systemctl restart readyup.service`                                                                            |
| Update code    | `git pull && source venv/bin/activate && pip install -r requirements.txt && sudo systemctl restart readyup.service` |

No inbound ports (other than SSH) are required; the bot communicates **outbound** to Discord over HTTPS.
