from app.core.crud_router import crud_router
from app.modules.assets.models import Asset
from app.modules.assets.schemas import AssetCreate, AssetRead, AssetUpdate

router = crud_router(
    model=Asset,
    create_schema=AssetCreate,
    read_schema=AssetRead,
    update_schema=AssetUpdate,
    prefix="/assets",
    tag="assets",
    entity="asset",
)
