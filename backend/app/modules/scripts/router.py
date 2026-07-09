from app.core.crud_router import crud_router
from app.modules.scripts.models import Script
from app.modules.scripts.schemas import ScriptCreate, ScriptRead, ScriptUpdate

router = crud_router(
    model=Script,
    create_schema=ScriptCreate,
    read_schema=ScriptRead,
    update_schema=ScriptUpdate,
    prefix="/scripts",
    tag="scripts",
    entity="script",
)
