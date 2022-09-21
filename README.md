<!-- TODO: dynamic changing pre-commit ci link -->
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/SlugTools/api/main.svg)](https://results.pre-commit.ci/latest/github/SlugTools/api/main)
[![Uptime Robot status](https://img.shields.io/uptimerobot/status/m792610788-ec5bd8ede10c18f96a13393a)](https://status.slug.tools)
# 🔧 SlugTools API
A simple REST API that returns detailed and organized data on services pertaining to the [University of California, Santa Cruz](https://www.ucsc.edu/). Documentation and other information is available [here](https://api.slug.tools).

## Contributing
The [`main`](https://github.slug.tools/api/tree/main) branch is deployed to production. Any contributions should be wary of and directed towards the [`dev`](https://github.slug.tools/api/tree/dev) branch through which the default branch will rebased from every now and then.

## Run
Clone this repository, create, and activate a Python virtual environment.
```bash
python -m venv venv
source venv/bin/activate
```
Install and upgrade the project's dependencies/packages.
```bash
python -m pip install -r requirements.txt --upgrade
```
Comment out the `init` call for `sentry_sdk` in [`app/__init__.py`](https://github.com/SlugTools/api/blob/main/app/__init__.py) which is used for production-level deployment monitoring and error tracking. Create an account for [Deta](https://web.deta.sh/) (remote database), create a project, and save its key into an `.env` file as `DETA_KEY` in the directory's root.
```env
DETA_KEY=[ENTER KEY HERE]
```
Run the app once with the following so it can create and save data to Deta. Once finished, exit out and comment out the call to `scrape_data` to avoid repeatedly fetching data from remote sources on edit/save/startup.
```bash
python debug.py
```
