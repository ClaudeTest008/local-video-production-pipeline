from app.core.crud_router import crud_router
from app.modules.prompts.models import Prompt
from app.modules.prompts.schemas import PromptCreate, PromptRead, PromptUpdate

router = crud_router(
    model=Prompt,
    create_schema=PromptCreate,
    read_schema=PromptRead,
    update_schema=PromptUpdate,
    prefix="/prompts",
    tag="prompts",
    entity="prompt",
)
