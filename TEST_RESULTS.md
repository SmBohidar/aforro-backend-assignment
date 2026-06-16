# Automated Test Results

The Aforro backend API includes comprehensive automated tests covering the core business logic, including the Order Checkout endpoint and Inventory decrement validation.

## Test Run Output (June 2026)

```text
Found 4 test(s).
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
....
----------------------------------------------------------------------
Ran 4 tests in 0.338s

OK
Destroying test database for alias 'default'...
```

**Coverage Details:**
- **Order Placement:** Verifies orders are created with `CONFIRMED` status when stock is sufficient.
- **Inventory Deduction:** Verifies that stock is precisely decremented when an order is successful.
- **Out of Stock Validation:** Verifies the API returns a `400 Bad Request` and `REJECTED` status when attempting to purchase more stock than is available.
- **Invalid Products:** Verifies the API rejects orders for products that do not exist at the specified store location.
