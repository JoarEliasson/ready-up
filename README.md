# ReadyUp Discord Bot

ReadyUp is a lightweight Discord bot designed to enhance the Discord server experience by coordinating and tracking user arrival times for activities.<br>
Users can set an expected arrival time for any group activity, mark their arrival either manually or automatically (via voice channel join), and receive scheduled notifications if they’re late.<br>
The bot also maintains statistics on on-time and late arrivals and persists data between restarts.


## Features

- **Set ETA:**  
  Use the command `!eta HH:MM` (24-hour format) to set your expected arrival time for a group activity.
  
- **Mark Arrival:**  
  Mark your arrival manually with `!ready` or `!rdy`, or automatically by joining a voice channel.
  
- **Scheduled Notifications:**  
  Receive notifications 1 minute before, and 15, 30, 60 minutes late, as well as a 24-hour no-show alert.
  
- **User Stats:**  
  Check your stats using `!stats @User`.
  
- **Rules Display:**  
  Display the rules with `!rules`.

- **Data Persistence:**  
  User data (ETA, on-time count, late count, notifications sent) is stored in a JSON file (`user_data.json`) and automatically loaded and saved.

## Requirements

- Python 3.7+
- A Discord Bot Token (obtainable from the [Discord Developer Portal](https://discord.com/developers/applications))
- Dependencies as listed in `requirements.txt`

## Running the Bot on a Local PC

### For UNIX/Linux/macOS

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/yourusername/readyup-bot.git
   cd readyup-bot
   ```

2. **Create a Virtual Environment and Activate It:**

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install the Dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Create the `.env` File:**

   Create a file named `.env` in the project root with the following content:
   
   ```bash
   echo "DISCORD_TOKEN=your_discord_bot_token_here" > .env
   ```
   
   Alternatively, you can use a text editor to create and edit the file.

5. **Run the Bot:**

   ```bash
   python main.py
   ```

### For Windows

1. **Clone the Repository:**

   Open Command Prompt or PowerShell and run:
   
   ```cmd
   git clone https://github.com/yourusername/readyup-bot.git
   cd readyup-bot
   ```

2. **Create a Virtual Environment and Activate It:**

   ```cmd
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install the Dependencies:**

   ```cmd
   pip install -r requirements.txt
   ```

4. **Create the `.env` File:**

   Create a new file named `.env` in the project directory and add:
   
   ```
   DISCORD_TOKEN=your_discord_bot_token_here
   ```
   
   You can create this file using Notepad or another text editor.

5. **Run the Bot:**

   ```cmd
   python main.py
   ```

## Running the Bot on a DigitalOcean Droplet

### Prerequisites

- A DigitalOcean account with an Ubuntu droplet (LTS version recommended)
- SSH access to your droplet
- Git, Python 3, pip, and virtual environment tools installed on the droplet

### Setup Steps

1. **SSH into Your Droplet:**

   ```bash
   ssh root@your_droplet_ip
   ```

2. **Update and Install Required Packages:**

   ```bash
   sudo apt update && sudo apt upgrade -y
   sudo apt install python3 python3-pip python3-venv git -y
   ```

3. **Clone the Repository:**

   ```bash
   git clone https://github.com/yourusername/readyup-bot.git
   cd readyup-bot
   ```

4. **Set Up a Virtual Environment:**

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

5. **Install the Dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

6. **Create the `.env` File:**

   ```bash
   echo "DISCORD_TOKEN=your_discord_bot_token_here" > .env
   ```

7. **(Optional) Configure Logging:**  
   If desired, modify your logging setup in `main.py` to log to a file.

8. **Set Up Process Management with systemd:**

   Create a systemd service file:
   
   ```bash
   sudo nano /etc/systemd/system/readyup.service
   ```

   Paste the following content (adjust paths and the user if needed):

   ```ini
   [Unit]
   Description=ReadyUp Discord Bot
   After=network.target

   [Service]
   User=root
   WorkingDirectory=/root/readyup-bot
   ExecStart=/root/readyup-bot/venv/bin/python main.py
   Restart=always
   RestartSec=10
   EnvironmentFile=/root/readyup-bot/.env

   [Install]
   WantedBy=multi-user.target
   ```

   Save and exit (press `CTRL+X`, then `Y`, then `Enter`).

9. **Reload systemd and Start the Service:**

   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable readyup.service
   sudo systemctl start readyup.service
   ```

10. **Check the Service Status:**

    ```bash
    sudo systemctl status readyup.service
    ```

11. **View the Logs:**

    ```bash
    sudo journalctl -u readyup.service -f
    ```

### Updating the Code on the Droplet

1. **SSH into Your Droplet and Navigate to the Project Directory:**

   ```bash
   ssh root@your_droplet_ip
   cd /root/readyup-bot
   ```

2. **Pull the Latest Changes from GitHub:**

   ```bash
   git pull origin main
   ```

3. **Restart the Service:**

   ```bash
   sudo systemctl restart readyup.service
   ```

## Additional Notes

- The bot automatically creates and updates `user_data.json` in the project directory.
- Use systemd to manage the bot process for automatic restarts on failure or reboot.
- Logs can be viewed via systemd’s journal or by configuring file logging in `main.py`.

## License

[MIT License]
