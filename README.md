[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/SlugTools/api/main.svg)](https://results.pre-commit.ci/latest/github/SlugTools/api/main)
[![Uptime Robot status](https://img.shields.io/uptimerobot/status/m792610788-ec5bd8ede10c18f96a13393a)](https://status.slug.tools)

# SlugTools API

### Access university data with ease!

The SlugTools API provides a standards-compliant interface that developers can use to access UC Santa Cruz data. It serves scraped and organized data across university sites and categories. Report and bugs/errors/issues here.

## How Does it Work?

We're scraping data from different sites, combining them, and serving them in a standardized format. This is done through [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/) and a few other libraries, and then hosted on [Flask](https://flask.palletsprojects.com/en/latest/). Check out [LEARN.md](LEARN.md).

### Scraping

Some data is scraped and stored on startup, simply returned on request. Other data is scraped on request, and then returned. This is to ensure live up-to-date data for things like weather, [Waitz](https://waitz.io/ucsc), catalog, and other data. Other data may be scraped periodically, such as menus and food items.

## Contributing

### Setup

Clone and set up virtual env (or use [PDM](https://pdm-project.org/latest/)):

```bash
git clone https://github.slug.tools/api
cd api && python -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
```

Set up accounts and save keys in `.env`:

- [Deta](https://web.deta.sh/) `DETA_KEY` (database)
- [OpenWeather](https://openweathermap.org/) `OPENWEATHER_KEY`
- [Sentry](https://sentry.io/) `SENTRY_DSN` (analytics; optional)

### Run

Args:

- `--debug` (hot-reload)
- `--noscrape` (no scrape on startup)

```bash
python main.py
```
