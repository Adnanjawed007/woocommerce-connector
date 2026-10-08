"""Mock WooCommerce server for testing without real store."""
from fastapi import FastAPI, Query, Header, HTTPException
from typing import List, Optional
import uvicorn

app = FastAPI(title="Mock WooCommerce API")

# Complete fake data matching WooCommerce API structure
ORDERS = [
    {
        "id": i,
        "parent_id": 0,
        "number": str(1000 + i),
        "order_key": f"wc_order_{i}",
        "created_via": "checkout",
        "version": "9.0",
        "status": ["pending", "processing", "completed", "cancelled"][i % 4],
        "currency": "INR",
        "date_created": "2024-01-15T10:30:00",
        "date_modified": "2024-01-15T10:35:00",
        "discount_total": "0.00",
        "discount_tax": "0.00",
        "shipping_total": "50.00",
        "shipping_tax": "9.00",
        "cart_tax": "180.00",
        "total": str(1000 + i * 500),
        "total_tax": "189.00",
        "prices_include_tax": False,
        "customer_id": 100 + i,
        "billing": {
            "first_name": "John",
            "last_name": "Doe",
            "company": "",
            "address_1": "123 Main St",
            "address_2": "",
            "city": "Mumbai",
            "state": "MH",
            "postcode": "400001",
            "country": "IN",
            "phone": "+91-9876543210",
            "email": f"user{i}@example.com",
        },
        "shipping": {
            "first_name": "John",
            "last_name": "Doe",
            "company": "",
            "address_1": "123 Main St",
            "address_2": "",
            "city": "Mumbai",
            "state": "MH",
            "postcode": "400001",
            "country": "IN",
        },
        "payment_method": "bacs",
        "payment_method_title": "Direct Bank Transfer",
        "transaction_id": f"TXN{i}",
        "date_paid": "2024-01-15T10:30:00",
        "date_completed": "2024-01-15T10:35:00",
        "line_items": [
            {
                "id": 1,
                "name": f"Product {i}",
                "product_id": i,
                "variation_id": 0,
                "quantity": 1,
                "subtotal": str(1000 + i * 500),
                "subtotal_tax": "180.00",
                "total": str(1000 + i * 500),
                "total_tax": "180.00",
                "sku": f"SKU-{i:03d}",
                "price": str(1000 + i * 500),
            }
        ],
        "shipping_lines": [
            {
                "id": 1,
                "method_title": "Flat Rate",
                "method_id": "flat_rate",
                "total": "50.00",
                "total_tax": "9.00",
            }
        ],
        "fee_lines": [],
        "coupon_lines": [],
        "refunds": [],
    }
    for i in range(1, 21)
]

PRODUCTS = [
    {
        "id": i,
        "name": f"Product {i}",
        "slug": f"product-{i}",
        "permalink": f"http://localhost:8888/product/product-{i}/",
        "date_created": "2024-01-01T10:00:00",
        "date_modified": "2024-01-10T10:00:00",
        "type": "simple",
        "status": "publish",
        "featured": False,
        "catalog_visibility": "visible",
        "description": f"<p>Description for product {i}</p>",
        "short_description": f"Short description {i}",
        "sku": f"SKU-{i:03d}",
        "price": str(500 + i * 100),
        "regular_price": str(500 + i * 100),
        "sale_price": None,
        "on_sale": False,
        "purchasable": True,
        "total_sales": i * 2,
        "virtual": False,
        "downloadable": False,
        "downloads": [],
        "download_limit": -1,
        "download_expiry": -1,
        "tax_status": "taxable",
        "tax_class": "",
        "manage_stock": True,
        "stock_quantity": max(0, 100 - i * 3),
        "stock_status": "instock" if i < 30 else "outofstock",
        "backorders": "no",
        "backorders_allowed": False,
        "backordered": False,
        "sold_individually": False,
        "weight": "0.5",
        "dimensions": {"length": "10", "width": "5", "height": "2"},
        "shipping_required": True,
        "shipping_taxable": True,
        "shipping_class": "",
        "shipping_class_id": 0,
        "reviews_allowed": True,
        "average_rating": "4.50",
        "rating_count": 10,
        "upsell_ids": [],
        "cross_sell_ids": [],
        "parent_id": 0,
        "categories": [{"id": 1, "name": "Electronics", "slug": "electronics"}],
        "tags": [{"id": 1, "name": "Popular", "slug": "popular"}],
        "images": [{"id": 1, "src": "https://example.com/image.jpg", "name": f"Product {i}", "alt": ""}],
        "attributes": [],
        "default_attributes": [],
        "variations": [],
        "grouped_products": [],
        "menu_order": 0,
        "meta_data": [],
    }
    for i in range(1, 51)
]

def check_auth(consumer_key: str = Header(None), consumer_secret: str = Header(None)):
    if consumer_key != "ck_test" or consumer_secret != "cs_test":
        raise HTTPException(401, {"code": "woocommerce_rest_authentication_error", "message": "Invalid credentials"})

@app.get("/wp-json/wc/v3/orders")
def list_orders(
    page: int = 1, per_page: int = 20,
    status: Optional[str] = None,
    min_total: Optional[str] = None,
    max_total: Optional[str] = None,
    _auth=check_auth
):
    filtered = ORDERS
    if status:
        filtered = [o for o in filtered if o["status"] == status]
    if min_total:
        filtered = [o for o in filtered if float(o["total"]) >= float(min_total)]
    if max_total:
        filtered = [o for o in filtered if float(o["total"]) <= float(max_total)]
    
    start = (page - 1) * per_page
    end = start + per_page
    return filtered[start:end]

@app.get("/wp-json/wc/v3/orders/{order_id}")
def get_order(order_id: int, _auth=check_auth):
    order = next((o for o in ORDERS if o["id"] == order_id), None)
    if not order:
        raise HTTPException(404, {"code": "woocommerce_rest_shop_order_invalid_id", "message": "Order not found"})
    return order

@app.get("/wp-json/wc/v3/products")
def list_products(
    page: int = 1, per_page: int = 20,
    search: Optional[str] = None,
    stock_status: Optional[str] = None,
    _auth=check_auth
):
    filtered = PRODUCTS
    if search:
        filtered = [p for p in filtered if search.lower() in p["name"].lower() or search.lower() in p["sku"].lower()]
    if stock_status:
        filtered = [p for p in filtered if p["stock_status"] == stock_status]
    
    start = (page - 1) * per_page
    end = start + per_page
    return filtered[start:end]

@app.get("/wp-json/wc/v3/products/{product_id}")
def get_product(product_id: int, _auth=check_auth):
    product = next((p for p in PRODUCTS if p["id"] == product_id), None)
    if not product:
        raise HTTPException(404, {"message": "Product not found"})
    return product

@app.get("/wp-json/wc/v3/system_status")
def system_status(_auth=check_auth):
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8888)