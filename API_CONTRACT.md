# API CONTRACT
GrapplingMap backend API specification.
Ready for Supabase Edge Functions implementation.

## Auth
All `/api/me/*` endpoints require Supabase JWT in `Authorization: Bearer <token>` header.
All `/api/aggregate/*` endpoints are public (no auth required).

---

## Private User Endpoints (/api/me/*)

### GET /api/me/profile
Returns current user profile.
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "display_name": "Aaron",
  "membership_status": "member",
  "current_belt": "blue",
  "created_at": "2026-03-24T00:00:00Z"
}
```

### GET /api/me/progress
Returns all tracked technique statuses.
```json
{
  "items": [
    { "technique_key": "guard|j_point|passer|offence|toreando", "status": "drilling", "started_at": "2026-03-20T00:00:00Z" }
  ]
}
```

### POST /api/me/progress
Update technique status.
```json
{ "technique_key": "...", "status": "drilling" }
```

### GET /api/me/success-log
Returns success history (most recent first).
```json
{
  "items": [
    { "technique_key": "...", "logged_at": "2026-03-25T10:00:00Z" }
  ]
}
```

### POST /api/me/success-log
Log a success.
```json
{ "technique_key": "..." }
```

### GET /api/me/notes
Returns all user notes.
```json
{
  "items": [
    { "technique_key": "...", "note_text": "Works when opponent is flat", "updated_at": "..." }
  ]
}
```

### POST /api/me/notes
Save/update a note.
```json
{ "technique_key": "...", "note_text": "..." }
```

### GET /api/me/drills
Returns current drilling queue (status=drilling).
```json
{
  "items": [
    { "technique_key": "...", "started_at": "...", "days_drilling": 5 }
  ]
}
```

### GET /api/me/recommendations
Computed next-move suggestions based on user data + graph edges.
```json
{
  "next_move": { "label": "Leg drag", "reason": "Connected to your most-hit position" },
  "weak_areas": ["Mount", "Back Control"],
  "suggested_drill": { "label": "Kimura", "section": "Dominant Positions" }
}
```

---

## Aggregate Endpoints (/api/aggregate/*)

### GET /api/aggregate/popular-techniques
Most tracked techniques across all users.
```json
{
  "items": [
    { "technique_key": "...", "label": "Toreando", "track_count": 47 }
  ]
}
```

### GET /api/aggregate/common-paths
Most common transitions.
```json
{
  "items": [
    { "from": "J point", "to": "Side Control", "frequency": 23 }
  ]
}
```

### GET /api/aggregate/next-move
What users often track after a given technique.
```json
// GET /api/aggregate/next-move?from=guard|j_point
{
  "items": [
    { "label": "Leg drag", "adoption_rate": 0.34 },
    { "label": "North South pass", "adoption_rate": 0.28 }
  ]
}
```

### GET /api/aggregate/community-stats
Overall product stats.
```json
{
  "total_users": 150,
  "total_tracked": 4200,
  "belt_distribution": { "white": 80, "blue": 45, "purple": 15, "brown": 7, "black": 3 }
}
```

---

## Graph/Structure Endpoints (public)

### GET /api/graph/path
Shortest path between two positions.
```json
// GET /api/graph/path?from=Closed+Guard&to=Back+Control
{
  "path": ["Closed Guard", "Half Guard", "Mount", "Back Control"],
  "hops": 3
}
```

### GET /api/syllabus/:belt
Belt syllabus content.
```json
// GET /api/syllabus/white
{
  "belt": "white",
  "sections": [
    { "title": "Wrestling / Standing", "items": [...] }
  ]
}
```

---

## Implementation Notes
- Edge Functions use Deno runtime (Supabase default)
- RLS policies handle user-scoping automatically
- Aggregate queries should use materialized views or cron jobs, not real-time scans
- Rate limiting: 100 req/min per user for private, 1000 req/min for aggregate
