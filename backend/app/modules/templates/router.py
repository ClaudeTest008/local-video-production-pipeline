from app.core.crud_router import crud_router
from app.modules.templates.models import Template
from app.modules.templates.schemas import TemplateCreate, TemplateRead, TemplateUpdate

router = crud_router(
    model=Template,
    create_schema=TemplateCreate,
    read_schema=TemplateRead,
    update_schema=TemplateUpdate,
    prefix="/templates",
    tag="templates",
    entity="template",
    filter_fields=(),
)
