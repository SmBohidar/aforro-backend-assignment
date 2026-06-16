# Aforro Backend API

This repository contains the backend API for the Aforro assignment. It is built with Django REST Framework and handles inventory management, product search, and order processing across multiple stores. The project is fully containerized using Docker.

## Tech Stack
* **Framework:** Django & Django REST Framework
* **Database:** PostgreSQL
* **Caching:** Redis
* **Task Queue:** Celery + Redis
* **Environment:** Docker & Docker Compose

---

## Setup Instructions and Docker Usage

Make sure you have Docker and Docker Compose installed before proceeding.

### 1. Build and start the containers
Run the following command in the root directory to build the images and start the services:
```bash
docker-compose up -d --build
```

### 2. Run migrations
Apply the database migrations to set up the PostgreSQL tables:
```bash
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate
```

### 3. Generate seed data
Populate the database with dummy data (25 stores, 1200 products, and randomized inventory levels):
```bash
docker-compose exec web python manage.py seed_data
```

---

## Sample API Requests

Here are examples of how to interact with the core endpoints using `curl`. 
*(Note: Replace Store ID `26` and Product ID `1998` with actual IDs from your generated database)*

**1. Fetch Store Inventory (Cached)**
```bash
curl -X GET http://localhost:8000/stores/26/inventory/
```
*Example Response:*
```json
{
    "count": 377,
    "next": "http://localhost:8000/stores/26/inventory/?page=2",
    "previous": null,
    "results": [
        {
            "product_id": 1998,
            "product_title": "Adaptive holistic firmware",
            "price": "52.57",
            "category_name": "Electronics",
            "quantity": 170
        }
    ]
}
```

**2. Search Products (Autocomplete)**
```bash
curl -X GET "http://localhost:8000/api/search/suggest/?q=Ada"
```
*Example Response:*
```json
[
    {
        "id": 1998,
        "title": "Adaptive holistic firmware",
        "price": "52.57",
        "category_name": "Electronics"
    }
]
```

**3. Place an Order**
```bash
curl -X POST http://localhost:8000/orders/ \
-H "Content-Type: application/json" \
-d '{"store_id": 26, "items": [{"product_id": 1998, "quantity_requested": 5}]}'
```
*Example Response:*
```json
{
    "id": 1,
    "store": 26,
    "status": "CONFIRMED",
    "created_at": "2026-06-16T16:03:44.480791Z",
    "items": [
        {
            "product_title": "Adaptive holistic firmware",
            "quantity_requested": 5
        }
    ]
}
```

**4. List Store Orders**
```bash
curl -X GET http://localhost:8000/stores/26/orders/
```
*Example Response:*
```json
{
    "count": 1,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "store": 26,
            "status": "CONFIRMED",
            "created_at": "2026-06-16T16:03:44.480791Z",
            "items": [
                {
                    "product_title": "Adaptive holistic firmware",
                    "quantity_requested": 5
                }
            ]
        }
    ]
}
```

---

## Notes on Caching and Async Logic

* **Caching (Redis):** The Inventory Listing API (`GET /stores/<store_id>/inventory/`) uses Django's `@cache_page` decorator with Redis. This serves high-traffic read requests instantly from memory, bypassing the PostgreSQL database entirely for up to 15 minutes per store.
* **Async Logic (Celery):** The Order Checkout API uses Celery alongside Redis as a message broker. When an order is successfully placed, the API immediately returns a `200 OK` response to the user, while Celery handles post-order tasks (like sending confirmation emails) asynchronously in the background.

---

## Scalability Considerations

1. **Database Bottlenecks:** Currently, inventory deduction relies on database-level row locks (or implicit transaction safety) in PostgreSQL. At extreme scale, this could cause locking contention. Moving inventory reservation to an in-memory datastore (like Redis) using Lua scripts before confirming the database write would massively increase write-throughput.
2. **Search Performance:** The autocomplete search relies on `icontains` (SQL `ILIKE`), which is slow on massive datasets because it cannot always utilize standard B-tree indexes. Implementing Elasticsearch or utilizing PostgreSQL's `pg_trgm` extension (trigram indexing) would be necessary for scaling search.
3. **Horizontal Scaling:** The Docker architecture makes scaling trivial. By separating the web server, Celery worker, and Redis broker, we can horizontally scale the `web` nodes behind a load balancer and independently spin up dozens of `celery` worker nodes to handle massive bursts of order traffic.
