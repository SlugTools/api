# Contributing

The [`main`](https://github.slug.tools/api/tree/main) branch is deployed to production. Any contributions should be wary of and directed towards the [`dev`](https://github.slug.tools/api/tree/dev) branch which will be pushed to `main` branch every now and then.

## Run

Clone this repository, create, and activate a Python virtual environment with:

```bash
python -m venv venv
source venv/bin/activate
```

Install and upgrade the project's dependencies with:

```bash
python -m pip install -r requirements.txt --upgrade
```

Comment out the `init` call for `sentry_sdk` in [`app/__init__.py`](https://github.slug.tools/api/blob/main/app/__init__.py) which is used for production-level deployment monitoring and error tracking. Create an account for [Deta](https://web.deta.sh/) (remote database), create a project, and save its key into an `.env` file as `DETA_KEY` in the directory's root.

```env
DETA_KEY=[ENTER KEY HERE]
```

Run the app once with the following so it can create and save data to Deta. Once finished, exit out and comment out the call to `scrape_data` to avoid repeatedly fetching data from remote sources on edit/save/startup.

```bash
python debug.py
```
