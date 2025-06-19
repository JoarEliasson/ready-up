# ReadyUp Discord Bot
![ReadyUp logo](ready-up-logo-small.png "ReadyUp logo")

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10 | 3.11 | 3.12](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue?logo=python)](https://www.python.org/)
[![CI](https://github.com/JoarEliasson/ready-up/actions/workflows/ci.yml/badge.svg)](https://github.com/JoarEliasson/ready-up/actions/workflows/ci.yml)

## Table of Contents
1. [Features](#features)
2. [Commands](#commands)
3. [Project Structure](#project-structure)
4. [Setup & Installation](#setup-and-installation)
5. [Running the Bot Locally](#running-the-bot-locally)
6. [Data and Backups](#data-and-backups)

ReadyUp is a Discord bot designed to help coordinate group activities by tracking user arrival times, sending notifications, and maintaining punctuality statistics.
It uses a "Live Stats" model, ensuring that user statistics are always up-to-date the moment a user arrives or their ETA expires.

## Features

-   **ETA Tracking**: Users can set their ETA in minutes (`/eta minutes <number>`) or by specifying a time (`/eta time <HH:MM>`).
-   **Live Punctuality Tracking**: The bot calculates exactly how late (or on-time) a user is the moment they use the `/arrived` command.
-   **No-Show Detection**: If a user doesn't arrive within a configurable time after their ETA, their status is marked as "Expired," and it's recorded as a no-show in their stats.
-   **Immediate Stat Updates**: User stats are calculated and saved the moment their "journey" for an ETA is complete (either by arriving or by their ETA expiring).
-   **Public Session Status**: View the current status of all participants who are still expected to arrive using `/status`.
-   **Stats**: Check personal or another user's stats (`/stats`), including on-time percentage, average lateness, and total no-shows.
-   **Leaderboard**: Display a server-wide punctuality leaderboard with `/leaderboard`.
-   **Help & Ping Commands**: Onboard new users with `/help` and check bot latency with `/ping`.
-   **Timezone Aware**: All times are localized to a configurable server timezone.
-   **Robust Storage**: Designed with a layered architecture, data validation, and file-locking to prevent data corruption and race conditions.

## Commands

-   `/eta minutes <number>`: Set your ETA in minutes from now (e.g., `/eta minutes 15`).
-   `/eta time <HH:MM>`: Set your ETA to a specific time (e.g., `/eta time 21:00`).
-   `/arrived`: Mark yourself as arrived. You must have an active ETA to use this command.
-   `/status`: Shows who is still expected to arrive in the current session.
-   `/stats [user]`: View your own or another user's punctuality statistics. The `[user]` argument is optional.
-   `/leaderboard`: Displays the server's punctuality leaderboard.
-   `/ping`: Checks if the bot is online and its response time.
-   `/help`: Shows a helpful embed with command information.

| Command             | Example           | Description                                 |
|---------------------|-------------------|---------------------------------------------|
| `/eta minutes <n>`  | `/eta minutes 15` | Set ETA *n* minutes from now                |
| `/eta time <HH:MM>` | `/eta time 21:00` | Set ETA to a specific local time            |
| `/arrived`          | —                 | Mark yourself arrived (requires active ETA) |
| `/status`           | —                 | Show outstanding arrivals                   |
| `/stats [user]`     | `/stats @Alice`   | View punctuality stats (default: yourself)  |
| `/leaderboard`      | —                 | Show server-wide leaderboard                |
| `/ping`             | —                 | Check bot latency                           |
| `/help`             | —                 | Show command help                           |

## Project Structure

The project follows a simplified layered architecture to promote SOLID design principles, maintainability, and testability.

- [`src/main.py`](src/main.py) – main application entry point  
- [`src/config.py`](src/config.py) – loads & validates environment variables  
- [`src/domain`](src/domain) – core business logic and models (Session, UserETA, Stats)  
- [`src/application`](src/application) – application services (use-cases) and repository interfaces  
- [`src/infrastructure`](src/infrastructure) – external concerns, primarily JSON file persistence  
- [`src/bot`](src/bot) – Discord-specific logic, command registration, lifecycle


## Setup and Installation

These steps set up a **local development** environment to test the bot. For full production deployment instructions on a Linux server, see [DEPLOYMENT.md](DEPLOYMENT.md).

### Prerequisites

- Python 3.10 or newer
- A Discord Bot Application (create one on the [Discord Developer Portal](https://discord.com/developers/applications))

#### Discord Developer Portal checklist

1.  **Create an Application** and then a **Bot** within that application.
2.  Under the "Bot" tab, enable the **Server Members Intent**. This is required for the bot to see user information like names and avatars.
3.  Go to the "OAuth2" -> "URL Generator" tab. Select the following scopes:
    -   `bot`
    -   `applications.commands`
4.  Copy the generated URL and use it to invite the bot to your server.

### Local Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/JoarEliasson/ready-up.git
    cd ready-up
    ```

2.  **Create a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables:**
    -   Copy the example file: `cp .env.example .env`
    -   Edit the `.env` file with your specific configuration:
        -   `DISCORD_TOKEN`: Your bot's token.
        -   `GUILD_ID`: Your Discord server's ID for instant command updates.
    ```bash
    nano .env    # set DISCORD_TOKEN, GUILD_ID, etc.
    ```

### Running the Bot Locally

To run the bot directly from your terminal for testing:

```bash
python src/main.py
```

## Data and Backups

The bot stores all its data (active session, user stats) in JSON files within the `data/` directory.

**Back this folder up regularly.** You can set up a simple cron job on your server to copy the `data/` directory to a safe location.

**Example Cron Job for Daily Backups:**
Run `crontab -e` and add the following line to create a daily backup at 2 AM:

```cron
0 2 * * * /usr/bin/rsync -a /path/to/ready-up/data/ /path/to/backups/ready-up/
```

> **Tip — safer rsync:**  
> If you normally include `--delete` in your rsync scripts, omit it here unless you are 100 % sure; a typo could wipe your history of punctuality stats.
