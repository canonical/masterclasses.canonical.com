
<img width="836" height="280" alt="Masterclasses" src="https://github.com/canonical/masterclasses.canonical.com/assets/54525904/852d5f09-1508-4069-a2e5-2338ac863fac">


Masterclasses are a series of talks and workshops on varied topics presented by the amazing people at Canonical.

Canonical is known for its brilliant people, both in terms of intelligence and varied interests. Often these interests are discovered serendipitously when passing conversations. The initiative would like to provide a platform for this to occur company wide. Recordings will provide longevity to the content and allow people to hone their public speaking and presentational skills.

# Local Development

[masterclassses.canonical.com](https://masterclasses.canonical.com) is a [Flask v1](https://flask.palletsprojects.com/_/downloads/en/1.1.x/pdf/) app and uses [Flask-base](https://github.com/canonical/canonicalwebteam.flask-base): This is Canonical's core Flask app that sets default functionality (e.g. redirects.yaml, templates/404.html, robots.txt, favicon, caching headers, security headers).

It uses [dotrun](https://github.com/canonical/dotrun) for local development, defining standard endpoints for `serve`, `build`, `test`, `watch` etc. within the package.json. This allows for a consistent development experience across all Canonical projects.

1. Create a `.env.local` file locally in the repo head directory with the following contents:

```bash
PRIVATE_KEY_ID=your_private_key_id
PRIVATE_KEY=your_private_key
DATABASE_URL=production_database_url
```

Ask a member of the team for the values of these keys.

these keys are [mastermasterclasses-canonical-com](https://github.com/canonical/masterclasses.canonical.com/blob/main/konf/site.yaml#L12) google drive keys.

2. Install dotrun as described in https://github.com/canonical/dotrun#installation
3. Launch it from the head of this repo by running the following command:

```bash
dotrun
```

4. Once the containers are started, you can visit <http://127.0.0.1:8409> in your browser.
