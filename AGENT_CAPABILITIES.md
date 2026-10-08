
**AGENT_CAPABILITIES.md**
```markdown
# Agent Capabilities Document

## Supported Operations

### `search_orders`
Search and list WooCommerce orders with flexible filtering.

**Can:**
- Filter by order status (pending, processing, completed, cancelled, etc.)
- Filter by minimum/maximum order amount
- Filter by date range (orders created after/before specific dates)
- Filter by customer ID or product ID
- Paginate results (page, per_page up to 100)
- Return agent-friendly summaries (order number, status, total, customer name, item count)

**Returns:** Paginated list of order summaries with `has_more` indicator

### `get_order`
Retrieve complete details for a specific order by ID.

**Can:**
- Return full order information including line items, shipping, billing, payments
- Show order timeline (created, paid, completed dates)
- Include refund information if any

**Returns:** Full order object with all readable fields

### `search_products`
Search and list WooCommerce products with filtering.

**Can:**
- Search by name or SKU
- Filter by product type (simple, variable, grouped, external)
- Filter by status (publish, draft, private)
- Filter by category/tag ID
- Filter by price range
- Filter by stock status
- Paginate results

**Returns:** Paginated list of full product objects

### `get_inventory`
Get inventory/stock information for products.

**Can:**
- Get stock details for a specific product by ID
- List all products with their stock quantities and statuses
- Filter for low-stock items (configurable threshold)
- Filter for out-of-stock items
- Return: product ID, name, SKU, stock quantity, stock status, price

**Returns:** Paginated list of inventory summaries

---

## Unsupported Operations

The following operations are **intentionally not implemented** to maintain read-only security:

| Category | Operations |
|----------|------------|
| **Order Modifications** | Create orders, update orders, cancel orders, change order status |
| **Financial Operations** | Process refunds, capture payments, modify payment methods |
| **Inventory Changes** | Update stock quantities, manage stock settings, adjust inventory |
| **Product Management** | Create products, update products, delete products, manage variations |
| **Customer Data** | Create/update/delete customers, modify addresses |
| **System Operations** | Change settings, manage webhooks, modify coupons, generate reports |
| **Arbitrary Access** | Raw API proxy, custom endpoints, GraphQL queries |

---

## Data Boundaries

### Exposed to Agent

**Orders:**
- Order ID, number, status, totals, currency
- Creation/payment/completion timestamps
- Customer ID and billing name (first + last)
- Payment method title
- Line items (product names, quantities, prices, SKUs)
- Shipping method and cost
- Refund history

**Products:**
- Product ID, name, slug, permalink
- Type, status, featured flag
- Prices (regular, sale, current)
- SKU, descriptions
- Stock quantity, stock status, manage_stock flag
- Categories, tags, images, attributes
- Dimensions, weight, shipping class

**Inventory (subset of product data):**
- Product ID, name, SKU
- Stock quantity, stock status
- Price information
- Product type

### NOT Exposed to Agent

- Customer IP addresses and user agents
- Customer notes (private merchant notes)
- Payment gateway internal IDs/tokens
- Webhook delivery logs
- System status internals
- API credentials or authentication tokens
- WooCommerce internal meta_data not relevant to orders/inventory

---

## Security Boundaries

### Read-Only by Design

1. **No Write Methods**: The `WooCommerceClient` class only implements `GET` requests
2. **No Mutation Tools**: MCP tool definitions only include read operations
3. **Credential Isolation**: API keys never exposed to agents or logs
4. **Permission Enforcement**: Relies on WooCommerce API key permissions (should be Read-only)

### Authentication

- Uses WooCommerce Consumer Key/Secret (API Key auth)
- Credentials loaded from environment variables only
- No OAuth, no token storage, no credential rotation
- Keys transmitted via HTTP Basic Auth over HTTPS

### Error Handling

- Structured errors with codes (no stack traces to agents)
- Rate limit errors include `retry_after` guidance
- Authentication errors clearly separated from data errors

---

## Known Limitations

1. **Pagination**: WooCommerce max `per_page` is 100. Large catalogs require multiple requests.
2. **Low Stock Filtering**: Performed client-side after fetching products (WC API lacks native filter).
3. **Rate Limits**: Depends on WooCommerce/WordPress hosting configuration. Connector implements retry but cannot bypass limits.
4. **Variable Products**: Inventory for variations requires separate API calls not yet implemented.
5. **Date Filtering**: Uses `after`/`before` parameters (WC v3). Timezone handling depends on store settings.
6. **Search Performance**: WC product search can be slow on large catalogs.
7. **Single Tenant**: One connector instance = one WooCommerce store.
8. **No Webhooks**: Real-time updates not supported; agent must poll.
9. **Currency**: Assumes store currency; no conversion performed.
10. **Dependencies**: Requires network access to WooCommerce store.

---