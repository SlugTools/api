![Uptime Robot status](https://img.shields.io/uptimerobot/status/m792610788-ec5bd8ede10c18f96a13393a)
# 🔧 API
A simple REST API that returns detailed and organized data on services pertaining to UC Santa Cruz. Documentation and other information is available at [api.slug.tools](https://api.slug.tools).

## Run
Clone this repository and create and activate a Python virtual environment in the directory's root with the following.
```bash
python -m venv venv
source venv/bin/activate
```
Install and upgrade the project's dependencies with the following.
```bash
python -m pip install -r requirements.txt --upgrade
```
Comment out all calls for `sentry_sdk` in [`app/__init__.py`](https://github.com/SlugTools/api/blob/main/app/__init__.py), create an account at [Deta](https://web.deta.sh/), create a project, and save its key into an `.env` file as `DETA_KEY` in the directory's root.
```env
DETA_KEY=[key goes here]
```
Run the app once with the following so it can create and save data to Deta. Once finished, exit out and comment out the [data scraping call](https://github.com/SlugTools/api/blob/main/app/__init__.py#L172) to avoid repeatedly fetching data from remote sources on edit/save/startup.
```bash
python debug.py
```
