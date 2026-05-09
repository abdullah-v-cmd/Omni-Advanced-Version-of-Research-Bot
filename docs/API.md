# OmniSynth API Reference

## Base URL
- Local: `http://localhost:8000/api/v1`
- Docker: `http://backend:8000/api/v1`
- Production: `https://yourdomain.com/api/v1`

## Authentication
All protected endpoints require a Bearer token:
```
Authorization: Bearer <access_token>
```

## Response Format
```json
{
  "data": {},
  "message": "Success",
  "status": 200
}
```

## Error Format
```json
{
  "detail": "Error message here"
}
```
