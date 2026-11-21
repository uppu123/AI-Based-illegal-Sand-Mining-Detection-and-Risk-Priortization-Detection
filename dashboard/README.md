# Dashboard — Phase D (not started)

Planned MERN stack, deliberately small so it can run on a laptop:

- **React + Leaflet** — AOI boundary, mining-mask overlay with opacity toggle, segment priority table (risk, hectares, tier; sortable).
- **Node/Express** — endpoints for segments, chips, masks and risk scores.
- **MongoDB** — stores labels, masks and scores. A SQLite/in-memory fallback is planned if MongoDB is unavailable.

MVP scope (needs user sign-off): **map + overlay + priority table only**. No labeling UI in the first release.

The backend API contract will be frozen before model training finishes, so the UI can be built in parallel. Model outputs will be wired in during integration.
