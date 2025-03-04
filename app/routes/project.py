from fastapi import APIRouter, HTTPException, Depends
from typing import Annotated, List
from sqlalchemy.orm import Session
from app.models.project import Project
from app.models.user import User
from app.models.task import Task
from app.models.project_task import ProjectTask
from app.database import get_db
from app.routes.auth import get_current_admin
from app.schemas.project import ProjectBase, ProjectCreate, ProjectUpdate
from app.schemas.project_task import (
    ProjectTaskBase,
    ProjectTaskCreate,
    ProjectTaskUpdate,
)
from app.schemas.task import TaskCreate, TaskBase
from starlette import status
from app.models.project import ProjectPriority, ProjectStatus
from app.models.project_task import TaskStatus


router = APIRouter(tags=["projects"], prefix="/projects")
db_dependence = Annotated[Session, Depends(get_db)]


@router.get("/", response_model=List[ProjectBase])
async def get_projects(
    db: db_dependence, current_user: Annotated[User, Depends(get_current_admin)]
):
    db_projects = db.query(Project).all()
    return [ProjectBase.from_orm(project) for project in db_projects]


# projectTask detail: project detail, task list, gantt chart
@router.get("/{id}", response_model=ProjectTaskBase)
async def get_project_detail(id: int, db: db_dependence):
    db_project = db.query(Project).filter(Project.id == id).first()

    if db_project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project does not exist"
        )

    # task_ids
    db_task_ids = (
        db.query(ProjectTask.task_id).filter(ProjectTask.project_id == id).all()
    )
    task_ids_list = [task_id[0] for task_id in db_task_ids]
    tasks = []
    if task_ids_list:
        tasks = db.query(Task).filter(Task.id.in_(task_ids_list)).all()
    response = ProjectTaskBase(project=db_project, tasks=tasks)

    return response


# PROJECT, PROJECT_TASK
@router.post("/", response_model=ProjectBase)
async def create_project(
    project: ProjectTaskCreate,
    db: db_dependence,
    current_user: Annotated[User, Depends(get_current_admin)],
):

    # check project existence
    db_project = db.query(Project).filter(Project.name == project.name).first()
    if db_project is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Project name already exists."
        )
    new_project = Project(
        company_id=project.company_id,
        name=project.name,
        current_assignee=project.current_assignee,
        priority=project.priority,
        address=project.address,
        postal_code=project.postal_code,
        city_id=project.city_id,
        province_id=project.province_id,
        budget=project.budget,
        status=project.status,
        start_date=project.start_date,
        estimated_duration=project.estimated_duration,
    )
    # add project into Project table
    db.add(new_project)
    db.flush()
    # add project id and task_id into project_task table
    for task_id in project.task_ids:
        project_task = ProjectTask(
            project_id=new_project.id,
            task_id=task_id,
            assignee_id=project.current_assignee,
            status=TaskStatus.PENDING,
            budget=0.0,
            amount_due=0.0,
        )
        db.add(project_task)

    db.commit()
    db.refresh(new_project)
    return new_project


# Project ONLY
@router.put("/{id}", response_model=ProjectBase)
async def update_project(
    db: db_dependence,
    id: int,
    project: ProjectUpdate,
    current_user: Annotated[User, Depends(get_current_admin)],
):
    db_project = db.query(Project).filter(Project.id == id).first()
    if db_project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project does not exist."
        )
    if project.name is not None:
        db_project.name = project.name
    if project.current_assignee is not None:
        db_project.current_assignee = project.current_assignee
    if project.priority is not None:
        db_project.priority = project.priority
    if project.address is not None:
        db_project.address = project.address
    if project.postal_code is not None:
        db_project.postal_code = project.postal_code
    if project.city_id is not None:
        db_project.city_id = project.city_id
    if project.province_id is not None:
        db_project.province_id = project.province_id
    if project.budget is not None:
        db_project.budget = project.budget
    if project.status is not None:
        db_project.status = project.status
    if project.actual_end_date is not None:
        db_project.actual_end_date = project.actual_end_date
    db.commit()
    db.refresh(db_project)
    return db_project


# PROJECT_TASK, PROJECT
@router.delete("/{id}")
async def delete_project(
    id: int,
    db: db_dependence,
    current_user: Annotated[User, Depends(get_current_admin)],
):

    db_project = db.query(Project).filter(Project.id == id).first()
    if db_project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project does not exist."
        )
    db.delete(db_project)
    db.commit()
    return db_project


# create TASK, PROEJCT_TASK(DEPENDENCY)
@router.post("/{id}/tasks", response_model=ProjectTaskBase)
async def add_task(id: int, db: db_dependence, task: TaskCreate):
    # Check if the project exists
    db_project = db.query(Project).filter(Project.id == id).first()
    if db_project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project does not exist"
        )

    # check the existence of the task
    db_task = db.query(Task).filter(task.name == Task.name).first()
    if db_task is None:
        # add new task to TASK table
        new_task = Task(
            parent_id=task.parent_id,
            name=task.name,
            company_id=task.company_id,
            sort_order=task.sort_order,
        )
        db.add(new_task)
        db.flush()

        new_project_task = ProjectTask(
            project_id=id,
            task_id=new_task.id,
            status=TaskStatus.PENDING,
            budget=0.0,
            amount_due=0.0,
        )
        db.add(new_project_task)
    else:
        existing_link = (
            db.query(ProjectTask)
            .filter(ProjectTask.project_id == id, ProjectTask.task_id == db_task.id)
            .first()
        )
        if existing_link:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Task is already associated with this project",
            )

        project_task = ProjectTask(
            project_id=id,
            task_id=db_task.id,
            status=TaskStatus.PENDING,
            budget=0.0,
            amount_due=0.0,
        )
        db.add(project_task)
    db.commit()

    db.refresh(db_project)
    db_tasks = (
        db.query(Task).join(ProjectTask).filter(ProjectTask.project_id == id).all()
    )

    response = ProjectTaskBase(project=db_project, tasks=db_tasks)
    return response


# PROEJCT_TASK
@router.put("/{id}/tasks")
async def update_task(
    id: int,
    task_update: ProjectTaskUpdate,
    db: db_dependence,
    current_user: Annotated[User, Depends(get_current_admin)],
):
    db_project_task = db.query(ProjectTask).filter(ProjectTask.task_id == id).first()
    if db_project_task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project task does not exist."
        )
    update_data = task_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_project_task, key, value)

    db.commit()
    db.refresh(db_project_task)
    return db_project_task


# delete project task
@router.delete("/{id}/tasks")
async def delete_task(
    id: int,
    db: db_dependence,
    current_user: Annotated[User, Depends(get_current_admin)],
):
    db_project_task = db.query(ProjectTask).filter(ProjectTask.task_id == id).first()
    if db_project_task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project task does not exist."
        )

    db.delete(db_project_task)
    db.commit()
    return db_project_task
