
<img width="836" height="280" alt="Masterclasses" src="https://github.com/canonical/masterclasses.canonical.com/assets/54525904/852d5f09-1508-4069-a2e5-2338ac863fac">


Masterclasses are a series of talks and workshops on varied topics presented by the amazing people at Canonical.

Canonical is known for its brilliant people, both in terms of intelligence and varied interests. Often these interests are discovered serendipitously when passing conversations. The initiative would like to provide a platform for this to occur company wide. Recordings will provide longevity to the content and allow people to hone their public speaking and presentational skills.

# Local Development

[masterclassses.canonical.com](https://masterclasses.canonical.com) is a [Flask v1](https://flask.palletsprojects.com/_/downloads/en/1.1.x/pdf/) app and uses [Flask-base](https://github.com/canonical/canonicalwebteam.flask-base): This is Canonical's core Flask app that sets default functionality (e.g. redirects.yaml, templates/404.html, robots.txt, favicon, caching headers, security headers).

It uses [dotrun](https://github.com/canonical/dotrun) for local development, defining standard endpoints for `serve`, `build`, `test`, `watch` etc. within the package.json. This allows for a consistent development experience across all Canonical projects.

1. Create a `.env` file locally in the repo head directory, an example configuration can be found in `.env.example`
2. Install dotrun as described in https://github.com/canonical/dotrun#installation
3. Run the docker-compose file to start the database:

```bash
docker compose up -d
```

4. Launch it from the head of this repo by running the following command:

```bash
dotrun
```

5. Once the containers are started, you can visit <http://127.0.0.1:8409> in your browser.

# API Access

To set up API access, configure the API key as an environment variable.

## Endpoints

### **Retrieve All Presenters**
**GET** `/v1/presenters`  
- **Description:** Retrieves all presenters.  
- **Authentication:** Required (API token).  
- **Response:**  
  - Array of presenter objects containing:  
    - `id` (integer)  
    - `name` (string)  
    - `hrc_id` (string)  
    - `email` (string)  
- **Status Codes:**  
  - `200 OK`  

---

### **Retrieve a Specific Presenter by ID**
**GET** `/v1/presenters/{id}`  
- **Description:** Retrieves a specific presenter by ID.  
- **Authentication:** Required (API token).  
- **Parameters:**  
  - `id` (path parameter, integer) – Presenter’s unique identifier.  
- **Response:**  
  - Presenter object containing:  
    - `id` (integer)  
    - `name` (string)  
    - `hrc_id` (string)  
    - `email` (string)  
- **Status Codes:**  
  - `200 OK`  

---

### **Retrieve Talks by Presenter (HRC ID)**
**GET** `/v1/presenters/{hrc_id}/talks`  
- **Description:** Retrieves all talks for a presenter using their HRC ID.  
- **Authentication:** Required (API token).  
- **Parameters:**  
  - `hrc_id` (path parameter, string) – Presenter’s HRC ID.  
- **Response:**  
  - Object containing an array of talk objects with:  
    - `id` (integer)  
    - `title` (string)  
    - `description` (string)  
    - `start_time` (ISO 8601 datetime)  
    - `end_time` (ISO 8601 datetime)  
    - `recording_url` (string, URL)  
    - `slides_url` (string, URL)  
    - `presenters`: Array of objects containing:  
      - `name` (string)  
      - `hrc_id` (string)  
    - `tags`: Array of objects containing:  
      - `name` (string)  
      - `category` (string)  
- **Status Codes:**  
  - `200 OK`  
  - `404 Not Found`  

---

### **Retrieve Talks by Presenter (Email)**
**GET** `/v1/presenters/email/{email}/talks`  
- **Description:** Retrieves all talks for a presenter using their email address.  
- **Authentication:** Required (API token).  
- **Parameters:**  
  - `email` (path parameter, string) – Presenter’s email address.  
- **Response:**  
  - Object containing an array of talk objects with:  
    - `id` (integer)  
    - `title` (string)  
    - `description` (string)  
    - `start_time` (ISO 8601 datetime)  
    - `end_time` (ISO 8601 datetime)  
    - `recording_url` (string, URL)  
    - `slides_url` (string, URL)  
    - `presenters`: Array of objects containing:  
      - `name` (string)  
      - `email` (string)  
    - `tags`: Array of objects containing:  
      - `name` (string)  
      - `category` (string)  
- **Status Codes:**  
  - `200 OK`  
  - `404 Not Found`  
