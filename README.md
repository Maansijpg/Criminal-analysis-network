# Criminal-analysis-network

# CrimeNet — Criminal Network Analysis System

A prototype investigation platform that helps police officers map suspect networks, track connections between cases, and get real-time alerts when a known suspect is spotted on camera — built for Smart India Hackathon (SIH).

>  **This is a prototype.** All suspects, cases, phone numbers, bank accounts, and Aadhaar-style reference numbers in the seed data are entirely fictional. Face enrollment in this demo uses consenting team members standing in as "suspects," not real surveillance subjects.

## The problem

Investigators working a case often have evidence scattered across systems — call records, bank transactions, vehicle sightings, CCTV footage — with no single view of how suspects in the same case are actually connected to each other. CrimeNet pulls that evidence into one place and visualizes it as a live, interactive network graph, while also watching camera feeds for suspect matches in real time.

## What it does

- **Suspect network graph** — every suspect in a case is a node; shared phone numbers, bank transactions, and case membership become edges. The graph updates live as new evidence comes in, no refresh required.
- **Face-based suspect search** — upload a photo, get back a matching suspect record if one exists.
- **Live camera alerts** — a face detected in CCTV-angle footage that matches an enrolled suspect triggers a real-time alert, pushed to every open dashboard over WebSocket.
- **Add/remove suspects on the fly** — adding a suspect (with photos) immediately enrolls their face and links them into the case graph; removing one cleans up all related records.
- **Simulated bank transactions** — demonstrates how a new financial link between two suspects appears on the graph the moment it's recorded.

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | React + Tailwind CSS, `react-force-graph` for the network visualization |
| Backend | Python + FastAPI |
| Database | SQLite (see `backend/schema_postgres.sql` for the PostgreSQL migration path) |
| Real-time | A single WebSocket channel broadcasting graph updates, transactions, and alerts |
| Face recognition | `face_recognition` (dlib-based), 128-dimension face embeddings stored per suspect |
| Video processing | OpenCV |

## Architecture

```
┌─────────────┐        HTTP (REST)        ┌──────────────┐
│   React     │ ────────────────────────▶ │   FastAPI    │
│  Frontend   │ ◀──────────────────────── │   Backend    │
└─────────────┘                           └──────┬───────┘
      ▲                                          │
      │         WebSocket (live updates)         │
      └──────────────────────────────────────────┘
                                                  │
                                          ┌───────▼────────┐
                                          │  SQLite DB      │
                                          │ cases, suspects,│
                                          │ connections,    │
                                          │ sightings, etc. │
                                          └───────┬────────┘
                                                  │
                                          ┌───────▼────────┐
                                          │  watch.py        │
                                          │ (reads CCTV      │
                                          │  footage, runs   │
                                          │  face matching,  │
                                          │  posts sightings)│
                                          └──────────────────┘
```

The `connections` table is the backbone of the graph tab — every suspect-to-suspect relationship (shared call, shared transaction, same case) is a row here, so the graph is a direct read of the database rather than something computed on the fly.

## Project structure

```
crime-network-demo/
├── backend/
│   ├── main.py                    # FastAPI app entry point, WebSocket endpoint
│   ├── database.py                # SQLite connection helper
│   ├── ws_manager.py              # WebSocket broadcast manager
│   ├── face_utils.py              # Face embedding + matching helpers
│   ├── watch.py                   # Run CCTV footage through face recognition
│   ├── enroll_faces.py            # Bulk face enrollment from a photo folder
│   ├── seed_passwords.py          # Sets demo login passwords
│   ├── migrate_add_embeddings.py  # One-time DB migration for face embeddings
│   ├── schema_postgres.sql        # Production schema reference (PostgreSQL)
│   ├── crime_network.db           # SQLite database (not committed — see below)
│   └── routers/
│       ├── auth_routes.py         # Login
│       ├── cases.py               # Case listing
│       ├── suspects.py            # Suspect CRUD + photo-based enrollment/search
│       ├── graph.py                # Network graph data
│       ├── sightings.py           # Camera sighting → alert pipeline
│       ├── alerts.py              # Alert listing
│       └── transactions.py        # Simulated bank transaction linking
└── frontend/
    └── src/
        ├── api.js                 # Backend API client
        ├── App.jsx                # Routes
        ├── pages/
        │   ├── Login.jsx
        │   ├── Dashboard.jsx      # Case list
        │   ├── CaseGraph.jsx      # Live network graph
        │   ├── Alerts.jsx         # Live alert feed
        │   └── AddSuspect.jsx     # Add a suspect with face photos
        └── components/
```

## Setup

### Prerequisites

- Python 3.10+
- Node.js 18+
- `cmake` (required to install `dlib`, which `face_recognition` depends on)

### Backend

```bash
cd backend
pip install -r requirements.txt

# one-time setup
python3 migrate_add_embeddings.py
python3 seed_passwords.py

# start the server
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

## Demo data

`crime_network.db` (if included) ships with 3 fictional cases and 5 seeded police accounts. Every seeded officer's password is `demo123`.

Enrolling your own faces for a live demo:

```bash
# 1. Add a suspect with photos through the Add Suspect page in the UI —
#    this computes and stores their face embedding automatically.

# 2. Point the watcher at a video file or live webcam:
python3 watch.py cctv_footage/some_clip.mp4 "Main Entrance"
python3 watch.py 0 "Live Webcam"
```

Matches above the alert confidence threshold appear instantly on the **Alerts** and **Case Graph** pages via WebSocket — no page refresh needed.

## Design notes

- **No graph database.** At the scale of a single investigation (tens to low hundreds of suspects), a plain relational `connections` table does everything a graph database would, with zero added infrastructure.
- **Pretrained face recognition, not a custom-trained model.** Face matching uses off-the-shelf embeddings; the engineering effort goes into the ingest → embed → match → alert → broadcast pipeline, not model training.
- **One WebSocket channel, one source of truth.** Every real-time update — sightings, alerts, graph changes, transactions — flows through the same broadcast manager, so the simulated CCTV watcher and the live alert dashboard share one consistent code path.

## Roadmap

- [ ] Migrate SQLite → PostgreSQL with `pgvector` for embedding search at scale
- [ ] Alembic migrations instead of hand-run schema scripts
- [ ] Role-based access control (officer / supervisor / admin)
- [ ] Real OCR-based vehicle plate recognition
- [ ] Audit logging on sensitive lookups
- [ ] Evidence-linked connections (each graph edge points to the specific call/transaction record behind it)

## Ethics & data note

This project processes synthetic case data and, in its demo form, face data from consenting team members only. It is a prototype for demonstrating an investigation-support workflow, not a deployed surveillance system. Any real-world use involving actual case records, biometric data, or camera surveillance would require a formal data-sharing agreement with a law enforcement body, compliance with applicable data protection law, and human oversight of every match before action is taken.

## Team

_Add your team name and members here._

## License

_Add a license if required by the competition (e.g. MIT), or state "For hackathon evaluation purposes only."_
