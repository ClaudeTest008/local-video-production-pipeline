from app.core.crud_router import crud_router
from app.modules.thumbnail.models import Thumbnail
from app.modules.thumbnail.schemas import ThumbnailCreate, ThumbnailRead, ThumbnailUpdate

router = crud_router(
    model=Thumbnail,
    create_schema=ThumbnailCreate,
    read_schema=ThumbnailRead,
    update_schema=ThumbnailUpdate,
    prefix="/thumbnails",
    tag="thumbnails",
    entity="thumbnail",
)
