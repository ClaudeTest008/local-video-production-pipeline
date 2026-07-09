from app.core.crud_router import crud_router
from app.modules.publishing.models import PublishJob
from app.modules.publishing.schemas import PublishJobCreate, PublishJobRead, PublishJobUpdate

router = crud_router(
    model=PublishJob,
    create_schema=PublishJobCreate,
    read_schema=PublishJobRead,
    update_schema=PublishJobUpdate,
    prefix="/publishing",
    tag="publishing",
    entity="publish_job",
)
