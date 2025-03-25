from fastapi import HTTPException, APIRouter, Depends
from typing import Annotated, List
from app.database import get_db
from app.schemas.task import TaskBase, TaskCreate, TaskWithChildren
from app.models.task import Task
from app.models.user import User
from app.routes.auth import get_current_admin
from starlette import status
from sqlalchemy.orm import Session

router = APIRouter(tags=["tasks"], prefix="/tasks")
db_dependence = Annotated[Session, Depends(get_db)]


# get all tasks
@router.post("/all", response_model=List[TaskWithChildren])
async def get_all_tasks(
    db: db_dependence,
    current_user: Annotated[User, Depends(get_current_admin)],
):

    db_tasks = db.query(Task).filter(Task.company_id == current_user.company_id).all()

    # create a dictionary of tasks
    child_tasks = {}

    # get all child tasks for each parent task
    for task in db_tasks:
        if task.parent_id:
            if task.parent_id not in child_tasks:
                child_tasks[task.parent_id] = []
            child_tasks[task.parent_id].append(task)

    # get all top-level tasks
    tasks_with_children = []
    for task in db_tasks:
        if task.parent_id is None:  # if task has no parent
            task_data = TaskWithChildren.model_validate(task)
            task_data.children = [
                TaskBase.model_validate(child) for child in child_tasks.get(task.id, [])
            ]
            tasks_with_children.append(task_data)

    return tasks_with_children


# get only categories
@router.post("/categories", response_model=List[TaskBase])
async def get_categories(
    db: db_dependence, current_user: Annotated[User, Depends(get_current_admin)]
):
    db_categories = (
        db.query(Task)
        .filter(Task.parent_id.is_(None), Task.company_id == current_user.company_id)
        .all()
    )
    return [TaskBase.model_validate(task) for task in db_categories]


# get subtasks based on category
@router.post("/{id}/subtasks", response_model=List[TaskBase])
async def get_subtasks_by_category(id: int, db: db_dependence):
    db_subtasks = db.query(Task).filter(Task.parent_id == id).all()
    return [TaskBase.model_validate(task) for task in db_subtasks]


# add task
@router.post("/", response_model=TaskBase)
async def create_tasks(
    db: db_dependence,
    current_user: Annotated[User, Depends(get_current_admin)],
    task: TaskCreate,
):

    db_task = db.query(Task).filter(Task.name == task.name).first()
    if db_task is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Task already exists."
        )
    new_task = Task(name=task.name, parent_id=task.parent_id)
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task
