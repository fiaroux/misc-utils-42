# Fac Habitat Scraper

An automated Python scraper to monitor Fac Habitat student residence availability in Ile-de-France with email notifications.

## Features

- Automated scraping of all Ile-de-France residences
- Precise availability detection using Selenium for dynamic JavaScript content
- Change tracking with status history storage
- Email notifications for availability changes
- Secure environment variable configuration

## Installation

### Prerequisites
- Python 3.8+
- Chrome/Chromium browser installed

### Steps

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/fac-habitat-scraper.git
   cd fac-habitat-scraper
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # macOS/Linux
   # or
   .venv\Scripts\activate     # Windows
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your real information
   ```

## Configuration

### Environment Variables (.env)

```env
# Gmail configuration for notifications
EMAIL_USER=your.email@gmail.com
EMAIL_PASSWORD=your_gmail_app_password
EMAIL_TO=notification_email@gmail.com
```

### Gmail Setup

1. Enable 2-factor authentication: https://myaccount.google.com/security
2. Generate app password: https://myaccount.google.com/apppasswords
3. Use this password (16 characters) in `EMAIL_PASSWORD`

## Usage

### Quick test
```bash
python main.py
```

### Scheduled execution (cron)
```bash
# Example for Linux/Mac - check every 6 hours
crontab -e
# Add: 0 */6 * * * cd /path/to/project && /path/to/.venv/bin/python main.py
```

### On server/cloud
Use your platform's environment variables:
- **Railway**: Variables in dashboard
- **Heroku**: `heroku config:set EMAIL_USER=...`
- **Vercel**: Environment variables in dashboard

## Project Structure

```
fac-habitat-scraper/
├── main.py                 # Main script
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
├── .gitignore             # Files to ignore
├── README.md              # Documentation
└── availability_status.json # Status history (auto-generated)
```

## Technologies Used

- **Python 3.8+**
- **Selenium**: Browser automation
- **BeautifulSoup**: HTML parsing
- **python-dotenv**: Environment variable management
- **smtplib**: Email sending

## Warnings

- **Academic use**: This script is intended for educational purposes
- **Site respect**: Built-in delays to avoid server overload
- **Terms of use**: Check Fac Habitat's terms and conditions
- **Responsibility**: Author is not responsible for script usage

## Contributing

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Fac Habitat for their student residences
- Open source community for the tools used