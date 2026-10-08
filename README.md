# WooCommerce Connector for Agent Studio

A read-only Python connector that exposes WooCommerce orders, products, and inventory through a small FastAPI service. It provides agent-facing tool definitions and JSON tool-call endpoints, and uses WooCommerce REST API v3 with a store-specific consumer key and secret.

## What it supports

| Tool | Purpose |
|---|---|
| `search_orders` | List orders with status, amount, date, customer, and product filters. |
| `get_order` | Retrieve an order by ID, including its readable details and line items. |
| `search_products` | List or search products with product, price, category, tag, and stock filters. |
| `get_inventory` | Read inventory for one product or list inventory with low-stock and stock-status filters. |

Results are paginated. WooCommerce's `X-WP-Total` and `X-WP-TotalPages` headers are used when present. See [AGENT_CAPABILITIES.md](AGENT_CAPABILITIES.md) for the exposed data, unsupported operations, and known limitations.

The connector only makes WooCommerce `GET` requests. It cannot create, update, or cancel orders; issue refunds; change stock; or manage products or customers. Low-stock filtering is applied to the products returned for the requested page, so it does not scan an entire large catalog in one call. Variable product variation inventory is not fetched separately.

## Requirements

- Python 3.10 or newer
- WooCommerce REST API v3 enabled on the store
- A WooCommerce REST API key with **Read** permission

## Configure the connection

Create a WooCommerce REST API key in the store administration panel and select **Read** permission. Copy the environment template and edit it with the store URL and key values:

```powershell
Copy-Item .env.example .env
```

Set these values in `.env`:

```dotenv
WOOCOMMERCE_URL=https://your-store.example.com
WOOCOMMERCE_CONSUMER_KEY=ck_your_key
WOOCOMMERCE_CONSUMER_SECRET=cs_your_secret

# Optional settings
REQUEST_TIMEOUT=30
MAX_RETRIES=3
BASE_RETRY_DELAY=1.0
```

The connector uses the consumer key and secret for HTTP Basic authentication **from the connector to WooCommerce**. Use HTTPS for a real store connection. `.env` is excluded from Git; do not commit or share it.

The FastAPI service does **not** authenticate incoming callers. Keep it on a trusted network or protect it with an authenticated gateway before allowing other systems or users to reach it. The WooCommerce Read permission limits what the connector can do at the store, but does not control who can call the connector service.

## Install and run

Run these commands from the project directory. On Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m app.main
```

On macOS or Linux, use `python3 -m venv .venv` and `source .venv/bin/activate` in place of the Windows virtual environment commands. Configure `.env` before starting the service. It listens on `http://localhost:8000` by default.

Useful endpoints:

- `GET /health` — checks whether the configured WooCommerce API is reachable and authenticated.
- `GET /info` — connector name, mode, and tool names.
- `GET /mcp/tools` — tool definitions with parameter and return schemas.
- `POST /mcp/tools/call` — invoke a tool.
- `GET /docs` — interactive FastAPI documentation.

The health endpoint reports the WooCommerce connection state; it is not an authentication check for callers of this service.

## Run without a WooCommerce store

The repository includes a local mock WooCommerce API for a demo. Start it in one terminal:

```powershell
python mock_wc_server.py
```

In `.env`, set the connector to the mock server and use placeholder credentials (the mock is local and does not validate them):

```dotenv
WOOCOMMERCE_URL=http://localhost:8888
WOOCOMMERCE_CONSUMER_KEY=ck_test
WOOCOMMERCE_CONSUMER_SECRET=cs_test
```

Then start the connector in another terminal:

```powershell
python -m app.main
```

The mock server is for local demonstration only. It does not represent WooCommerce authentication, hosting, or rate-limit behavior.

## Call a tool

List the available definitions:

```powershell
Invoke-RestMethod http://localhost:8000/mcp/tools
```

Example call:

```powershell
Invoke-RestMethod -Method Post `
  -Uri http://localhost:8000/mcp/tools/call `
  -ContentType 'application/json' `
  -Body '{"name":"search_orders","arguments":{"status":"processing","per_page":5}}'
```

Other request bodies:

```json
{"name":"get_order","arguments":{"order_id":123}}
{"name":"search_products","arguments":{"search":"shirt","per_page":10}}
{"name":"get_inventory","arguments":{"low_stock_only":true,"low_stock_threshold":10}}
```

Successful calls return a `result`; tool failures return an `error`. Unknown tool names return HTTP 404. The service also exposes direct convenience routes under `/tools/`, such as `GET /tools/get_order/123` and `GET /tools/search_products?search=shirt`.

## Agent integration note

`/mcp/tools` and `/mcp/tools/call` provide a lightweight JSON tool-definition and invocation interface. This project does **not** implement the MCP transport/session protocol. An Agent Studio integration must be able to call these HTTP endpoints and adapt the request and response envelope, or place an appropriate adapter in front of this service.

## Rate limits and retries

The connector retries HTTP `429` and `5xx` responses and network exceptions. It honors a numeric `Retry-After` header when available; otherwise it uses exponential backoff based on `BASE_RETRY_DELAY`. Retries are bounded by `MAX_RETRIES`, and delays are capped at 60 seconds. Exhausted requests return a tool error. Actual rate limits are controlled by WooCommerce and the store's hosting environment.

## Demo

With the connector running (and either a configured store or the local mock), open another terminal and run:

```powershell
python demo.py
```

The demo calls the local HTTP service and prints sample order, product, and inventory data. Use test data when capturing or sharing its output.

## Tests

Run the test suite from the project directory:

```powershell
python -m pytest -q
```

The tests use mocked WooCommerce responses and do not require a live store. The current suite contains 33 tests.

## Project layout

```text
app/
  config.py                 Environment-based settings
  main.py                   Uvicorn entry point
  mcp/server.py             FastAPI tool-call and health endpoints
  models/                   WooCommerce response and input models
  services/wc_client.py     WooCommerce REST client
  services/rate_limiter.py  Retry and backoff handling
  tools/                    Order/product tools and schemas
tests/                      Automated tests
mock_wc_server.py           Local mock WooCommerce API
demo.py                     Example client for the running connector
.env.example                Environment variable template
AGENT_CAPABILITIES.md       Data boundaries and agent capabilities
```
