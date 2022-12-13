# 📜 Learn

Although not a full detailed guide, here are the technologies and brief summaries to help you kick off your project idea. The current infrastructure map is available [here](https://github.com/SlugTools/api/blob/main/layouts/current.dio.png).

- [📜 Learn](#-learn)
  - [☁️ Cloudflare](#%EF%B8%8F-cloudflare)
  - [🌊 DigitalOcean](#-digitalocean)
  - [🌶️ Flask](#%EF%B8%8F-flask)
  - [🟣 Deta](#-deta)
  - [🎒 GitHub Student Pack](#-github-student-pack)

## ☁️ [Cloudflare](https://www.cloudflare.com/)

This is the domain management system this app uses through pointed nameservers on the original domain handler/purchasing website. Here's an example [migration guide](https://youtu.be/XQKkb84EjNQ).

## 🌊 [DigitalOcean](https://www.digitalocean.com)

This is the hosting platform or web service this app uses to run. If you're setting up continuous deployment (CD), the [App Platform](https://www.digitalocean.com/products/app-platform) service is the easiest route to avoid manually configuring your infrastructure. Here's an example [setup guide](https://youtu.be/0xsPqOi_XpM) for deploying a Flask app with [Gunicorn](https://gunicorn.org/), a popular Python production-level web server.

## 🌶️ [Flask](https://flask.palletsprojects.com/en/latest/)

This is the Python web framework this app is built with. For a very minimal setup, use the [quickstart guide](https://flask.palletsprojects.com/en/latest/quickstart/). There are many alternatives and counterparts to this framework that have their own pros/cons.

## 🟣 [Deta](https://www.deta.sh/)

This is the database/storage service this app uses. Constantly fetching fresh information through raw operations is not necessary/viable. Fetching and storing this data on startup or timed loops ensures a reasonable response time. Here's the [documentation](https://docs.deta.sh/docs/base/sdk) to set up JSON storage within your app.

## 🎒 [GitHub Student Pack](https://education.github.com/pack)

You can set up such an app at no cost with the amount of resources offered by the student pack. You can register domains up to a year with promotions from services like Namecheap. There are cloud services such as DigitalOcean and Azure to choose from for your web server that offer a timely balance that might be renewable. You can opt for advanced databases such as MongoDB and a plethora of other resources in exchange for a screenshot of your proof of enrollment at almost any educational establishment.
