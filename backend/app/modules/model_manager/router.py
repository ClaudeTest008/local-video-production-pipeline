from app.core.crud_router import crud_router
from app.modules.model_manager.models import ManagedModel
from app.modules.model_manager.schemas import (
    ManagedModelCreate,
    ManagedModelRead,
    ManagedModelUpdate,
)

router = crud_router(
    model=ManagedModel,
    create_schema=ManagedModelCreate,
    read_schema=ManagedModelRead,
    update_schema=ManagedModelUpdate,
    prefix="/models",
    tag="models",
    entity="managed_model",
    filter_fields=(),
)
