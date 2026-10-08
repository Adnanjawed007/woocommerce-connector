#!/usr/bin/env python3
"""
Demo script for WooCommerce Connector.

Run this after starting the server to demonstrate tool functionality.
Requires a running WooCommerce instance with valid credentials in .env
"""

import asyncio
import httpx
import json
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "http://localhost:8000"


async def demo():
    """Run demonstration of all tools."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("=" * 60)
        print("WooCommerce Connector Demo")
        print("=" * 60)
        
        # 1. Health check
        print("\n1. Health Check")
        print("-" * 40)
        resp = await client.get(f"{BASE_URL}/health")
        print(f"Status: {resp.status_code}")
        print(f"Response: {json.dumps(resp.json(), indent=2)}")
        
        if resp.json().get("status") != "healthy":
            print("\n❌ WooCommerce not accessible. Check credentials in .env")
            return
        
        # 2. List available tools
        print("\n2. Available Tools")
        print("-" * 40)
        resp = await client.get(f"{BASE_URL}/mcp/tools")
        tools = resp.json()
        for tool in tools:
            print(f"  • {tool['name']}: {tool['description'][:80]}...")
        
        # 3. Search orders
        print("\n3. Search Orders (latest 5)")
        print("-" * 40)
        resp = await client.post(
            f"{BASE_URL}/mcp/tools/call",
            json={"name": "search_orders", "arguments": {"per_page": 5, "page": 1}}
        )
        result = resp.json()
        if result.get("error"):
            print(f"Error: {result['error']}")
        else:
            data = result["result"]
            print(f"Found {data['total_items']} total orders (page {data['page']}/{data['total_pages']})")
            for order in data["data"][:3]:
                print(f"  #{order['number']} - {order['status']} - {order['total']} {order['currency']} - {order['billing_name']}")
        
        # 4. Get specific order (if any exist)
        print("\n4. Get Order Details")
        print("-" * 40)
        resp = await client.post(
            f"{BASE_URL}/mcp/tools/call",
            json={"name": "search_orders", "arguments": {"per_page": 1}}
        )
        result = resp.json()
        if result.get("result", {}).get("data"):
            order_id = result["result"]["data"][0]["id"]
            print(f"Fetching details for order #{order_id}...")
            resp = await client.post(
                f"{BASE_URL}/mcp/tools/call",
                json={"name": "get_order", "arguments": {"order_id": order_id}}
            )
            result = resp.json()
            if result.get("error"):
                print(f"Error: {result['error']}")
            else:
                order = result["result"]
                print(f"Order #{order['number']} ({order['status']})")
                print(f"  Total: {order['total']} {order['currency']}")
                print(f"  Items: {len(order.get('line_items', []))}")
                print(f"  Payment: {order.get('payment_method_title')}")
        
        # 5. Search products
        print("\n5. Search Products (first 5)")
        print("-" * 40)
        resp = await client.post(
            f"{BASE_URL}/mcp/tools/call",
            json={"name": "search_products", "arguments": {"per_page": 5, "page": 1}}
        )
        result = resp.json()
        if result.get("error"):
            print(f"Error: {result['error']}")
        else:
            data = result["result"]
            print(f"Found {data['total_items']} total products")
            for product in data["data"][:3]:
                print(f"  {product['name']} (SKU: {product.get('sku', 'N/A')}) - {product.get('price', 'N/A')} {product.get('currency', 'INR')}")
        
        # 6. Get inventory (low stock)
        print("\n6. Low Stock Products (threshold: 10)")
        print("-" * 40)
        resp = await client.post(
            f"{BASE_URL}/mcp/tools/call",
            json={"name": "get_inventory", "arguments": {"low_stock_only": True, "low_stock_threshold": 10, "per_page": 10}}
        )
        result = resp.json()
        if result.get("error"):
            print(f"Error: {result['error']}")
        else:
            data = result["result"]
            print(f"Found {data['total_items']} low-stock products")
            for product in data["data"][:5]:
                print(f"  {product['name']} (SKU: {product['sku']}) - Stock: {product['stock_quantity']} - Status: {product['stock_status']}")
        
        print("\n" + "=" * 60)
        print("Demo complete!")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(demo())