"""
Product — clase con datos hardcodeados y getters
  - PROD-001: camiseta barata (€39.98) — bajo riesgo
  - PROD-002: zapatillas caras (€189.99) — alto valor
"""

class Product:
    def __init__(
        self,
        product_id: str,
        name: str,
        description: str,
        sku: str,
        variant: str,
        unit_price_eur: float,
        quantity: int,
        category: str,
        weight_kg: float,
        is_returnable: bool,
        return_reason: str,
        ecommerce_id: str,
    ):
        self.product_id     = product_id
        self.name           = name
        self.description    = description
        self.sku            = sku
        self.variant        = variant
        self.unit_price_eur = unit_price_eur
        self.quantity       = quantity
        self.total_value_eur = round(unit_price_eur * quantity, 2)
        self.category       = category
        self.weight_kg      = weight_kg
        self.is_returnable  = is_returnable
        self.return_reason  = return_reason
        self.ecommerce_id   = ecommerce_id

    def get_details(self) -> dict:
        return {
            "product_id":      self.product_id,
            "name":            self.name,
            "description":     self.description,
            "sku":             self.sku,
            "variant":         self.variant,
            "unit_price_eur":  self.unit_price_eur,
            "quantity":        self.quantity,
            "total_value_eur": self.total_value_eur,
            "category":        self.category,
            "weight_kg":       self.weight_kg,
            "is_returnable":   self.is_returnable,
            "return_reason":   self.return_reason,
            "ecommerce_id":    self.ecommerce_id,
        }
    

# Datos hardcodeados

PROD_001 = Product(
    product_id    = "PROD-001",
    name          = "Basic White T-Shirt",
    description   = "Classic white t-shirt made from 100% cotton.",
    sku           = "TS-001-XL",
    variant       = "XL",
    unit_price_eur = 19.99,
    quantity      = 2,
    category      = "apparel",
    weight_kg     = 0.5,
    is_returnable = True,
    return_reason = "wrong_size",
    ecommerce_id  = "adidas_es",
)
 
PROD_002 = Product(
    product_id    = "PROD-002",
    name          = "Premium Running Sneakers",
    description   = "High-performance running shoes with carbon fiber sole.",
    sku           = "SN-002-42",
    variant       = "42 EU",
    unit_price_eur = 189.99,
    quantity      = 1,
    category      = "footwear",
    weight_kg     = 1.2,
    is_returnable = True,
    return_reason = "not_as_described",
    ecommerce_id  = "desigual_es",
) 

    
PRODUCTS: dict[str, Product] = {
    "PROD-001": PROD_001,
    "PROD-002": PROD_002,
}

def get_product(product_id: str) -> Product | None:
    return PRODUCTS.get(product_id)