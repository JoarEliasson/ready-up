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

2.  **Initial Server Setup:**
    *   Connect to your new server as the `root` user:
        ```bash
        ssh root@YOUR_DROPLET_IP
        ```
    *   Update all system packages to patch any security vulnerabilities:
        ```bash
        apt update && apt upgrade -y
        ```
    *   Create a new non-root user for running the bot (replace `youruser`):
        ```bash
        adduser youruser
        ```
    *   Give this user administrative privileges:
        ```bash
        usermod -aG sudo youruser
        ```

3.  **Authorize SSH Key for the New User (CRITICAL STEP):**
    *   While still logged in as `root`, copy the authorized SSH key to your new user's account. This allows you to log in directly as that user.
        ```bash
        # This command copies the keys and sets the correct ownership and permissions.
        rsync --archive --chown=youruser:youruser /root/.ssh /home/youruser
        ```

4.  **Harden and Finalize Setup:**
    *   Enable the Uncomplicated Firewall (`ufw`) to allow only SSH traffic:
        ```bash
        ufw allow OpenSSH
        ufw enable
        ```
        *(Press 'y' and Enter to confirm.)*
    *   Log out of the `root` account (`exit`). From now on, you will work as your new user.

5.  **Log in as Your New User:**
    ```bash
    ssh youruser@YOUR_DROPLET_IP
    ```
    *If the login fails with a permission error, it's likely because your home directory permissions are too strict. Run this command on your local machine to fix it, then try logging in again:*
    ```bash
    # This command is run on your LOCAL machine, not the server.
    ssh root@YOUR_DROPLET_IP "chmod 755 /home/youruser"
    ```

## Step 2: Install Dependencies and Deploy Code

1.  **Install Python and Git:**
    ```bash
    sudo apt install python3-pip python3.10-venv git -y
    ```

2.  **Deploy the Bot to `/opt`:**
    *The `/opt` directory is the standard location for optional, third-party software on Linux, which avoids potential home directory permission issues with `systemd` services.*
    *   Clone the repository directly into `/opt`:
        ```bash
        sudo git clone https://github.com/JoarEliasson/ready-up.git /opt/ready-up
        ```
    *   Give your user ownership of the new directory so you can edit files without `sudo`:
        ```bash
        sudo chown -R youruser:youruser /opt/ready-up
        ```

3.  **Navigate to the Project and Set Up Environment:**
    ```bash
    cd /opt/ready-up
    ```
    *   Create the Python virtual environment:
        ```bash
        python3 -m venv venv
        ```
    *   Activate the virtual environment:
        ```bash
        source venv/bin/activate
        ```
    *   Install the project's Python packages:
        ```bash
        pip install -r requirements.txt
        ```

4.  **Configure Environment Variables:**
    *   Copy the example file: `cp .env.example .env`
    *   Edit the file using `nano`:
        ```bash
        nano .env
        ```
    *   Fill in all required values (especially `DISCORD_TOKEN`).
    *   Save and exit (`Ctrl+X`, `Y`, `Enter`).

## Step 3: Run the Bot as a `systemd` Service

`systemd` will manage the bot process, ensuring it starts on boot and restarts if it fails.

1.  **Create the Service File:**
    *   Use `nano` to create and edit the service file with `sudo`:
        ```bash
        sudo nano /etc/systemd/system/readyup.service
        ```
    *   Copy and paste the entire block below into the editor. **Ensure `User` and `Group` match the username you created.**

        ```ini
        [Unit]
        Description=ReadyUp Discord Bot
        After=network-online.target
        Wants=network-online.target
        
        [Service]
        # The user and group that will run the service.
        # Replace 'youruser' with the actual user and group you want to run the bot as.
        # This should preferably be a non-root user for security.
        Type=simple
        User=youruser   # ← change
        Group=youruser  # ← change
        
        # The full path to the project's root directory.
        WorkingDirectory=/opt/ready-up
        
        # The full command to start the bot.
        ExecStart=/opt/ready-up/venv/bin/python /opt/ready-up/src/main.py
        
        # Restart policy
        Restart=on-failure
        RestartSec=5s
        
        # Redirect output to the system journal
        StandardOutput=journal
        StandardError=journal

        # Security hardening options
        NoNewPrivileges=true
        PrivateTmp=true
        ProtectSystem=full
        
        [Install]
        WantedBy=multi-user.target
        ```
    *   Save and exit (`Ctrl+X`, `Y`, `Enter`).

2.  **Enable and Start the Service:**
    *   Reload `systemd` to make it aware of the new file:
        ```bash
        sudo systemctl daemon-reload
        ```
    *   Enable the service to start automatically on boot:
        ```bash
        sudo systemctl enable readyup.service
        ```
    *   Start the service immediately:
        ```bash
        sudo systemctl start readyup.service
        ```


## Step 4: Troubleshooting

If the service fails to start, use these commands to diagnose the issue.

-   **Check the High-Level Status:**
    ```bash
    sudo systemctl status readyup.service
    ```
    *Look for lines that say `Active: active (running)` (success) or `Active: failed` (failure).*

-   **View Detailed Logs:**
    *This is the most useful command for seeing Python errors.*
    ```bash
    sudo journalctl -u readyup.service --no-pager -n 50
    ```
    *(`-n 50` shows the last 50 lines. `--no-pager` prints directly to the console.)*

-   **Test the Command Manually:**
    *If `systemd` fails with an obscure error, running the startup command yourself often gives a clearer error message. Make sure you are in the project directory and the venv is active.*
    ```bash
    cd /opt/ready-up
    source venv/bin/activate
    python src/main.py
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
