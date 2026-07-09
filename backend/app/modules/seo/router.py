from app.core.crud_router import crud_router
from app.modules.seo.models import SeoPack
from app.modules.seo.schemas import SeoPackCreate, SeoPackRead, SeoPackUpdate

router = crud_router(
    model=SeoPack,
    create_schema=SeoPackCreate,
    read_schema=SeoPackRead,
    update_schema=SeoPackUpdate,
    prefix="/seo",
    tag="seo",
    entity="seo_pack",
)
