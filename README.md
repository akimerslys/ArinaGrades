Sister Performance Monitor Bot

This is a Telegram bot that helps you monitor your sister's performance and allows her to track her own progress. The bot uses Redis for data storage and requires minimal setup.

Features:

Track and log performance metrics

Provide insights and reminders

Allow both you and your sister to view progress


Setup:

1. Clone the repository

git clone https://github.com/your-repo.git
cd your-repo


2. Install dependencies

pip install -r requirements.txt

with poetry

pip install poetry

poetry check


3. Edit config.py.template

Rename config.py.template to config.py

Add your Telegram bot token, Redis connection details and ID's of admins.



4. Run the bot

python bot.py


5. OPTIONAL Run a scheduling messaging service using arc redis.

