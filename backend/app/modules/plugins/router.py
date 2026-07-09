from app.core.crud_router import crud_router
from app.modules.plugins.models import Plugin
from app.modules.plugins.schemas import PluginCreate, PluginRead, PluginUpdate

router = crud_router(
    model=Plugin,
    create_schema=PluginCreate,
    read_schema=PluginRead,
    update_schema=PluginUpdate,
    prefix="/plugins",
    tag="plugins",
    entity="plugin",
    filter_fields=(),
)
