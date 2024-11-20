INPUT = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "title": "Order Schema",
    "description": "Schema for e-commerce order validation",
    "properties": {
        "id": {
            "type": "string",
            "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
            "description": "Unique identifier for the order",
        },
        "customer_id": {
            "type": "string",
            "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
            "description": "Unique identifier for the customer",
        },
        "customer_email": {
            "type": "string",
            "format": "email",
            "description": "Customer's email address",
        },
        "customer_name": {
            "type": "string",
            "minLength": 1,
            "description": "Customer's full name",
        },
        "billing_address": {
            "type": "object",
            "properties": {
                "street": {"type": "string", "minLength": 1},
                "city": {"type": "string", "minLength": 1},
                "state": {"type": "string", "minLength": 2},
                "postal_code": {"type": "string", "pattern": "^\\d{5}(-\\d{4})?$"},
                "country": {"type": "string", "minLength": 2},
            },
            "required": ["street", "city", "state", "postal_code", "country"],
            "additionalProperties": "false",
        },
        "shipping_address": {
            "type": "object",
            "properties": {
                "street": {"type": "string", "minLength": 1},
                "city": {"type": "string", "minLength": 1},
                "state": {"type": "string", "minLength": 2},
                "postal_code": {"type": "string", "pattern": "^\\d{5}(-\\d{4})?$"},
                "country": {"type": "string", "minLength": 2},
            },
            "required": ["street", "city", "state", "postal_code", "country"],
            "additionalProperties": "false",
        },
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "product_id": {
                        "type": "string",
                        "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
                    },
                    "product_name": {"type": "string", "minLength": 1},
                    "quantity": {"type": "integer", "minimum": 1},
                    "unit_price": {"type": "number", "minimum": 0},
                    "subtotal": {"type": "number", "minimum": 0},
                },
                "required": [
                    "product_id",
                    "product_name",
                    "quantity",
                    "unit_price",
                    "subtotal",
                ],
                "additionalProperties": "false",
            },
            "minItems": 1,
        },
        "total_amount": {
            "type": "number",
            "minimum": 0,
            "description": "Total order amount",
        },
        "status": {
            "type": "string",
            "enum": [
                "PENDING",
                "PAID",
                "PROCESSING",
                "SHIPPED",
                "DELIVERED",
                "CANCELLED",
            ],
            "default": "PENDING",
        },
        "created_at": {"type": "string", "format": "date-time"},
        "updated_at": {"type": "string", "format": "date-time"},
        "payment_method": {
            "type": "string",
            "enum": ["credit_card", "debit_card", "paypal", "bank_transfer"],
        },
        "payment_id": {"type": "string"},
        "tracking_number": {"type": "string"},
        "notes": {"type": "string"},
    },
    "required": [
        "customer_id",
        "customer_email",
        "customer_name",
        "billing_address",
        "shipping_address",
        "items",
        "total_amount",
        "payment_method",
    ],
    "additionalProperties": "false",
}
