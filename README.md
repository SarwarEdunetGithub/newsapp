# AI News Application

A full-stack, responsive news application using Django (Backend) and HTML/Tailwind/JS (Frontend), augmented by Google's Gemini AI.

## Features Built:
- **Responsive UI**: TailwindCSS based responsive card layout, mobile-friendly navigation.
- **News API Integration**: Fetches the latest global/local news across categories (Tech, Business, Sports, Health, Entertainment) dynamically.
- **AI Summaries**: Uses **Gemini API** on the backend to automatically trim long news contents down to 3-4 sentence digests.
- **Multi-language Translation**: Uses **Gemini AI** to translate titles and summaries seamlessly on the fly using API calls (English, Hindi, Telugu available).
- **Background Jobs**: Uses `django_apscheduler` to automatically fetch and save news on an hourly cron schedule, without user interaction.
- **Database**: Django defaults to SQLite 3 as instructed to maintain clean storage of titles, contents, image URLs, categories, etc.

## Setup Instructions
1. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```
2. Set up the `.env` file (A `.env` containing your Gemini key was already created!).
3. Run Database Migrations:
   ```bash
   python manage.py migrate
   ```
4. Initial news fetch (Optional: run this to instantly populute the DB instead of waiting for the cron job to run):
   Make a POST request or, if running the server, press the "Refresh News" button on the UI!
5. Start the server:
   ```bash
   python manage.py runserver
   ```
6. Access the site via: `http://127.0.0.1:8000/`

## Deployment:
- Ensure you set `DEBUG = False` and correct `ALLOWED_HOSTS` in `settings.py`.
- Configure an actual PostgreSQL endpoint in `settings.py` -> `DATABASES` by passing `os.environ` variables in production environments (like Heroku or Render).
- Ensure Redis + Celery / server-specific cron configs are correctly set in high-scale prod scenarios (Currently runs embedded APScheduler which is ideal for single-instance PAAS setups like Render/Railway).
