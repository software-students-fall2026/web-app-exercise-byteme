# Campus Lost & Found

A mobile-friendly web app for reporting and finding items lost or found on NYU's campus. Built with Flask and MongoDB by Team ByteMe, following an agile development process.

## Product vision statement

Campus Lost & Found helps NYU students and staff quickly report, search for, and reclaim items lost or found anywhere on campus, all from their phone.

## Team members

- [Tracy Wang](https://github.com/TracyWang0904)
- [Emma Ao](https://github.com/emma6594)
- [Jingjing Wang](https://github.com/JingjingWang129)
- [Uuriintuya Ganzorig](https://github.com/Uuriii1003)

## User stories

User stories are tracked as [GitHub Issues](https://github.com/software-students-fall2026/web-app-exercise-byteme/issues).

## Task boards

- [Team ByteMe - Sprint 1](https://github.com/orgs/software-students-fall2026/projects/3)

## Steps necessary to run the software

### 1. Prerequisites

- [Python](https://www.python.org/downloads/) 3.10 or newer
- [Git](https://git-scm.com/downloads)
- Access to a MongoDB database. We use a shared [MongoDB Atlas](https://www.mongodb.com/atlas) cluster; the connection details are in the `.env` file shared privately with team members and course admins.

### 2. Clone the repository

```bash
git clone https://github.com/software-students-fall2026/web-app-exercise-byteme.git
cd web-app-exercise-byteme
```

### 3. Run the course setup script (once per clone)

This activates the repository's git hooks and checks your git name and email, as required by the course instructions.

macOS / Linux:

```bash
python3 .automations/setup.py
```

Windows:

```powershell
python .automations/setup.py
```

Fix any problems it reports before continuing.

### 4. Create a virtual environment and install dependencies

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows (PowerShell):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 5. Configure environment variables

Create a file named `.env` in the project root. Use `env.example` as a template:

```bash
cp env.example .env
```

Then fill in the real values:

| Variable | Description |
|---|---|
| `MONGO_URI` | MongoDB connection string, e.g. `mongodb+srv://<user>:<password>@<cluster-host>/` |
| `MONGO_DBNAME` | Database name: `lost_and_found` |
| `SECRET_KEY` | Any long random string (used by Flask to sign session cookies) |

The `.env` file contains private credentials and must never be committed. It is already listed in `.gitignore`.

### 6. (Optional) Load sample data

```bash
python seed.py          # add 8 sample posts
python seed.py --reset  # delete ALL posts first (asks for confirmation), then add the samples
```

The database is shared by the whole team, so only one person needs to run this, and `--reset` should only be used if everyone agrees. Sample posts have no owner, so nobody can edit or delete them. Log in and create your own post to try editing and deleting.

### 7. Run the app

```bash
python app.py
```

Open http://127.0.0.1:8000 in a browser.

The app is designed for phones. On a computer, use your browser's mobile view: in Chrome, open DevTools (`Cmd + Option + I` / `Ctrl + Shift + I`) and click "Toggle device toolbar".

> If port 8000 is already in use on your machine, change the port in the last line of `app.py`.

### 8. Create an account

Anyone can browse, search and view stats, but you must log in to post, edit or delete. Open `/register` and sign up with an `@nyu.edu` email and a password of at least 8 characters, then log in. You can only edit or delete your own posts.

## Pages

| Page | URL | Description |
|---|---|---|
| Home | `/` | Recent posts, with All / Lost / Found / Claimed tabs |
| Item detail | `/items/<id>` | All information about one post, plus possible matches |
| Post an item | `/items/new` | Form to report a lost or found item (login required) |
| Edit item | `/items/<id>/edit` | Update a post or mark it as claimed (owner only) |
| More matches | `/items/<id>/matches` | Browse open possible matches, ten per page |
| Delete item | `/items/<id>/delete` | Confirm and delete a post (owner only) |
| Search | `/search` | Search by keyword, type, category and building |
| Stats | `/stats` | Post counts, claimed rate, and lost items by building and category |
| Register | `/register` | Create an account with an NYU email |
| Log in | `/login` | Log in to post, edit and delete |

## Data model

All posts are stored in a single MongoDB collection, `items`:

| Field | Type | Description |
|---|---|---|
| `_id` | ObjectId | created automatically by MongoDB |
| `type` | string | `"lost"` or `"found"` |
| `title` | string | short item name, e.g. "Black AirPods case" |
| `description` | string | more details about the item |
| `category` | string | one of `CATEGORIES` in `constants.py` |
| `building` | string | one of `BUILDINGS` in `constants.py` |
| `location` | string | room or spot, e.g. "4th floor" |
| `date` | datetime | when the item was lost or found |
| `contact` | string | email or phone of the poster |
| `status` | string | `"open"` or `"claimed"` |
| `owner_id` | string | id of the user who created the post |
| `author_name` | string | poster's name, taken from their email |
| `created_at` | datetime | when the post was created |
| `updated_at` | datetime | when the post was last edited |

User accounts are stored in a second collection, `users`:

| Field | Type | Description |
|---|---|---|
| `_id` | ObjectId | created automatically by MongoDB |
| `email` | string | NYU email address, unique |
| `password_hash` | string | hashed password (the plain password is never stored) |


## Detail and delete user stories

Three improvements are implemented: claimed posts no longer show match suggestions; open posts show five recent matches with a paginated View more page; deletion requires a session token as well as login and ownership.

See [the user stories and implementation guide](docs/detail-delete-user-stories.md).

### Run the focused tests

With your Python environment activated:

```sh
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Tests use an in-memory MongoDB substitute and do not load `.env` or access the shared database. Keep a valid `SECRET_KEY` in your ignored `.env` when running the real application, as required for sessions and login.
