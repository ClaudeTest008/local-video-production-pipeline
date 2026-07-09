from app.core.crud_router import crud_router
from app.modules.storyboard.models import Scene
from app.modules.storyboard.schemas import SceneCreate, SceneRead, SceneUpdate

router = crud_router(
    model=Scene,
    create_schema=SceneCreate,
    read_schema=SceneRead,
    update_schema=SceneUpdate,
    prefix="/storyboard",
    tag="storyboard",
    entity="scene",
)
