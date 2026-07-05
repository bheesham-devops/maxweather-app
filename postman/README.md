# Postman Collection — MaxWeather API (via APIM)

This collection tests the Weather API through Azure API Management using
a pre-configured OAuth2 client_credentials flow against Entra ID. Postman
will auto-fetch a fresh bearer token and inject it into the `Authorization`
header on every request.

## Files

| File | Purpose |
| :--- | :--- |
| `MaxWeather-API.postman_collection.json` | Collection: two GET requests + collection-level OAuth2 auth |
| `MaxWeather-Demo.postman_environment.json` | Environment: holds only the `client_secret` (paste yours after import) |

## Quick start

### 1. Grab your client secret from Key Vault

```bash
az keyvault secret show \
  --vault-name kv-maxweather-demo-sea \
  --name entra-client-secret \
  --query value -o tsv
```

### 2. Import into Postman

1. Open Postman → **Import** (top-left button)
2. Drag & drop both json files (or click **Files** → select them)
3. Confirm → **Import**

### 3. Paste the secret into the environment

1. Top-right environment dropdown → select **MaxWeather Demo (SEA)**
2. Click the **eye icon** next to the dropdown → **Edit**
3. Replace `PASTE_YOUR_CLIENT_SECRET_HERE` with the Key Vault value
4. Click **Save**

### 4. Send a request

1. Open the **MaxWeather API (via APIM)** collection
2. Click **Get Current Weather** → **Send**
3. First request triggers a token fetch—Postman caches it for ~60 minutes

Expected response:

```json
{
  "city": "Singapore",
  "country": "SG",
  "temperature_c": 29.4,
  "feels_like_c": 35.9,
  "humidity_pct": 80,
  "condition": "Clouds",
  "description": "overcast clouds",
  "wind_speed_ms": 3.1,
  "visibility_m": 10000,
  "timestamp": "2026-07-05T11:44:18+00:00"
}
```

## Collection contents

| Request | Method | URL | Query Params |
| :--- | :--- | :--- | :--- |
| Get Current Weather | GET | `{{apim_base_url}}/current` | `city` |
| Get Weather Forecast | GET | `{{apim_base_url}}/forecast` | `city`, `days` |

## Collection variables (already set)

| Variable | Value |
| :--- | :--- |
| `apim_base_url` | `https://apim-maxweather-demo-sea.azure-api.net/weather` |
| `tenant_id` | `3b711293-95ed-4377-a2b9-0470f8d77929` |
| `client_id` | `0a2b6552-85d9-4343-8c93-dd3bcb19551d` |
| `api_scope` | `api://3b711293-95ed-4377-a2b9-0470f8d77929/maxweather-api-demo/.default` |

## Environment variables (you fill in)

| Variable | Value |
| :--- | :--- |
| `client_secret` | **Paste from Key Vault** (see step 1 above) |
