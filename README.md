# Compass_Purple

> Personal learning project — cybersecurity & full-stack development.

![Status](https://img.shields.io/badge/status-in%20development-purple)
![License](https://img.shields.io/badge/license-MIT-blue)
![Stack](https://img.shields.io/badge/stack-React%20%7C%20FastAPI%20%7C%20Python-informational)

---

## What is compass_purple?

Started in feb.2026, **compass_purple** is an open-source Purple Team dashboard.

It lets you:
- 🔴 **Simulate** basic adversarial techniques (Red side)
- 🔵 **Analyze** logs and detect suspicious events (Blue side)
- 🟣 **Correlate** both sides and visualize your detection coverage against the MITRE ATT&CK framework

---

## Features

### 🔴 Red — Attack Simulation
- Launch [Atomic Red Team](https://github.com/redcanaryco/atomic-red-team) tests directly from the UI
- Browse and filter techniques by ATT&CK tactic
- Guided interface with technique descriptions and risk level

### 🔵 Blue — Detection & Analysis
- Ingest local logs (syslog, Windows Event, flat files)
- Match events against [Sigma](https://github.com/SigmaHQ/sigma) rules
- Timeline view of suspicious activity

### 🟣 Purple — Correlation Engine
- Cross-reference each Red test with Blue alerts
- Result per technique: `Detected` / `Partial` / `Missed`
- ATT&CK heatmap of your detection coverage
- Export exercise reports (JSON)

---

## Architecture

```
compass_purple/
├── frontend/          # React + Tailwind — main dashboard UI
├── backend/           # FastAPI — REST API & orchestration
├── engine/
│   ├── base.py        # Abstract interfaces: RedModule, BlueModule, PurpleModule
│   ├── loader.py      # Auto-discovers and loads modules from subdirectories
│   ├── red/           # Red modules (attack simulation)
│   │   └── atomic_redteam.py
│   ├── blue/          # Blue modules (log ingestion & detection)
│   │   └── sigma_matcher.py
│   └── purple/        # Purple modules (correlation & reporting)
│       └── correlator.py
├── data/
│   ├── atomic/        # Atomic Red Team (git submodule)
│   └── attack/        # Local ATT&CK matrix (JSON)
└── docker-compose.yml
```

### Module system

Each module inherits from a base interface and is **auto-discovered** at startup

```python
# Example: adding a custom Red module
class MyRedModule(RedModule):
    name = "my_module"
    description = "Does something custom maybe"

    def run(self, params: dict) -> dict:
        ...
```

---

## Getting Started

### Prerequisites
- Docker + Docker Compose
- Git

### Run locally

```bash
git clone --recurse-submodules https://github.com/Giremuu/compass_purple.git
cd compass_purple
docker compose up
```

Then open [http://localhost:3000](http://localhost:3000).

---

## Stack

| Layer | Technology |
|---|---|
| Frontend | React + Tailwind CSS |
| Backend | FastAPI (Python) |
| Engine | Python |
| Database | SQLite |
| Deployment | Docker Compose |

---

## Others Projects

| Project | Description |
|---|---|
| [suzune_check](https://github.com/Giremuu/suzune_check) | Security audit tool with Ansible for Debian/Ubuntu |
| [fern_ops](https://github.com/Giremuu/fern_ops) | IaC stack with supervision |
| [ishtar_sound](https://github.com/Giremuu/ishtar_sound) | Just a public blindtest webapp |

---

## License

MIT — see [LICENSE](./LICENSE) for details.