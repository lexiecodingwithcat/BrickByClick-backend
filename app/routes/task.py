from fastapi import HTTPException, APIRouter, Depends
from typing import Annotated,List
from app.database import get_db
from app.schemas.task import TaskBase, TaskCreate
from app.models.task import Task
from app.models.user import User
from app.routes.auth import get_current_user
from starlette import status
from sqlalchemy.orm import Session

router = APIRouter(tags=["tasks"], prefix="/tasks")
db_dependence = Annotated[Session, Depends(get_db)]

# get all tasks
@router.get("/", response_model= List[TaskBase])
async def get_tasks(db:db_dependence):
    db_tasks = db.query(Task).all()
    return [TaskBase.from_orm(task)for task in db_tasks]
    
# get only categories
@router.get("/categories", response_model=List[TaskBase])
async def get_categories(db:db_dependence):
    db_categories = db.query(Task).filter(Task.parent_id.is_(None)).all()
    return [TaskBase.from_orm(task)for task in db_categories]

# get subtasks based on category 
@router.get("/{id}/subtasks", response_model=List[TaskBase])
async def get_subtasks_by_category(id:int, db:db_dependence):
    db_subtasks = db.query(Task).filter(Task.parent_id==id).all()
    return [TaskBase.from_orm(task)for task in db_subtasks]

# add task
@router.post("/", response_model= TaskBase)
async def create_tasks(db: db_dependence,current_user:Annotated[User, Depends(get_current_user)], task: TaskCreate):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,detail = "User is not authorized."
        )
    db_task = db.query(Task).filter(Task.name == task.name).first()
    if db_task is not None:
        raise HTTPException(
            status_code= status.HTTP_409_CONFLICT, detail="Task already exists."
        )
    new_task = Task(name = task.name, parent_id = task.parent_id)
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task

