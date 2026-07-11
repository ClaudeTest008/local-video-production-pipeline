from app.core.crud_router import crud_router
from app.modules.brands.models import Brand
from app.modules.brands.schemas import BrandCreate, BrandRead, BrandUpdate

router = crud_router(
    model=Brand,
    create_schema=BrandCreate,
    read_schema=BrandRead,
    update_schema=BrandUpdate,
    prefix="/brands",
    tag="brands",
    entity="brand",
    filter_fields=(),
)
