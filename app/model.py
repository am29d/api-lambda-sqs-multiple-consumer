from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4

class OrderStatus(str, Enum):
    PENDING = "PENDING"
    PAID = "PAID" 
    PROCESSING = "PROCESSING"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"

class PaymentMethod(str, Enum):
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    PAYPAL = "paypal"
    BANK_TRANSFER = "bank_transfer"

@dataclass
class Address:
    street: str
    city: str
    state: str
    postal_code: str  # Validation: ^\d{5}(-\d{4})?$
    country: str

@dataclass
class OrderItem:
    product_id: UUID
    product_name: str
    quantity: int
    unit_price: Decimal
    subtotal: Decimal

@dataclass
class Order:
    customer_id: UUID
    customer_email: str
    customer_name: str
    billing_address: Address
    shipping_address: Address
    items: List[OrderItem]
    total_amount: Decimal
    payment_method: PaymentMethod
    id: UUID = field(default_factory=uuid4)
    status: OrderStatus = OrderStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    payment_id: Optional[str] = None
    tracking_number: Optional[str] = None
    notes: Optional[str] = None

    def __post_init__(self):
        # Validate total matches sum of items
        items_total = sum(item.subtotal for item in self.items)
        if items_total != self.total_amount:
            raise ValueError(f"Total amount {self.total_amount} doesn't match items total {items_total}")
        
        # Validate each item's subtotal
        for item in self.items:
            expected_subtotal = item.quantity * item.unit_price
            if item.subtotal != expected_subtotal:
                raise ValueError(f"Item subtotal {item.subtotal} doesn't match quantity * unit_price {expected_subtotal}")