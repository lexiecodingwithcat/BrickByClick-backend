from datetime import timedelta
from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks
from typing import Annotated, List
from sqlalchemy.orm import Session
from app.models.project import Project
from app.models.user import User
from app.models.task import Task
from app.models.project_task import ProjectTask
from app.database import get_db
from app.routes.auth import get_current_admin, get_current_user
from app.schemas.notification import NotificationCreate
from app.schemas.project import ProjectBase, ProjectCreate, ProjectUpdate
from app.schemas.project_task import (
    ProjectTaskBase,
    ProjectTaskCreate,
    ProjectTaskUpdate,
    TaskWithProjectTask,
    ProjectWithTasks,
)
from app.schemas.task import TaskCreate, TaskBase
from starlette import status
from app.models.project import ProjectPriority, ProjectStatus
from app.models.project_task import TaskStatus
from app.models.project_tracking import ProjectTracking
from app.core.email import send_email

router = APIRouter(tags=["projects"], prefix="/projects")
db_dependence = Annotated[Session, Depends(get_db)]


# contractor project list
@router.get("/contractor", response_model=List[ProjectTaskBase])
async def get_contractor_projects(
    db: db_dependence, current_user: Annotated[User, Depends(get_current_user)]
):
    db_projects = (
        db.query(Project)
        .join(ProjectTask, ProjectTask.project_id == Project.id)
        .filter(ProjectTask.assignee_id == current_user.id)
        .all()
    )
    result = []
    for project in db_projects:
        # get project tasks
        tasks = (
            db.query(Task)
            .join(ProjectTask, ProjectTask.task_id == Task.id)
            .filter(ProjectTask.project_id == project.id)
            .all()
        )
        project_data = ProjectTaskBase(
            project=project,
            tasks=tasks,
        )
        result.append(project_data)

    return result


@router.get("/", response_model=List[ProjectBase])
async def get_projects(
    db: db_dependence, current_user: Annotated[User, Depends(get_current_admin)]
):
    db_projects = db.query(Project).all()
    return [ProjectBase.from_orm(project) for project in db_projects]


# projectTask detail: project detail, task list, gantt chart
@router.get("/{id}", response_model=ProjectWithTasks)
async def get_project_detail(
    id: int,
    db: db_dependence,
    current_user: Annotated[User, Depends(get_current_admin)],
):
    db_project = db.query(Project).filter(Project.id == id).first()

    if db_project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project does not exist"
        )

    tasks_with_project_tasks = (
        db.query(Task, ProjectTask)
        .join(ProjectTask, ProjectTask.task_id == Task.id)
        .filter(ProjectTask.project_id == id)
        .all()
    )
    tasks = [
        TaskWithProjectTask(task=task, project_task=project_task)
        for task, project_task in tasks_with_project_tasks
    ]
    response = ProjectWithTasks(project=db_project, tasks=tasks)

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

    # Exclude task_ids from project
    new_project = Project(**project.dict(exclude={"task_ids"}))

    # add project into Project table
    db.add(new_project)
    db.flush()
    # add project id and task_id into project_task table
    if project.task_ids:
        project_tasks = [
            ProjectTask(
                project_id=new_project.id,
                task_id=task_id,
                assignee_id=project.current_assignee,
                status=TaskStatus.PENDING,
                budget=0.0,
                amount_due=0.0,
            )
            for task_id in project.task_ids
        ]
        db.add_all(project_tasks)

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

    # Get only provided fields
    update_data = project.dict(exclude_unset=True)

    # Update the project fields
    for key, value in update_data.items():
        setattr(db_project, key, value)

    db.commit()
    db.refresh(db_project)
    return db_project


# PROJECT_TASK, PROJECT
@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
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
    # delete project tasks
    db_project_tasks = db.query(ProjectTask).filter(ProjectTask.project_id == id).all()
    for project_task in db_project_tasks:
        db.delete(project_task)

    # delete project
    db.delete(db_project)
    db.commit()


# create TASK, PROEJCT_TASK(DEPENDENCY)
@router.post("/{id}/tasks", response_model=ProjectTaskBase)
async def add_task(
    id: int,
    db: db_dependence,
    task: TaskCreate,
    current_user: Annotated[User, Depends(get_current_admin)],
):
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


# PROJECT_TASK
@router.put("/{id}/tasks", response_model=ProjectTaskBase)
async def update_task(
    id: int,
    task_update: ProjectTaskUpdate,
    db: db_dependence,
    current_user: Annotated[User, Depends(get_current_admin)],
):
    # check if the project exists
    db_project = db.query(Project).filter(Project.id == id).first()
    if db_project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project does not exist."
        )

    # check if the project task exists
    db_project_task = (
        db.query(ProjectTask).filter(ProjectTask.task_id == task_update.task_id).first()
    )
    if db_project_task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project task does not exist."
        )

    # update project task
    update_data = task_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_project_task, key, value)

    db.commit()
    db.refresh(db_project_task)

    # add project tracking
    if task_update.assignee_id is not None:
        db_project_tracking = (
            db.query(ProjectTracking).filter(
                ProjectTracking.project_id == id,
                ProjectTracking.user_id == task_update.assignee_id,
            )
        ).first()
        if db_project_tracking is None:
            project_tracking = ProjectTracking(
                project_id=id,
                user_id=task_update.assignee_id,
                start_date=task_update.start_date,
                end_date=task_update.start_date
                + timedelta(days=task_update.estimated_duration),
            )
            db.add(project_tracking)
            db.commit()
        else:
            db_project_tracking.end_date = task_update.start_date + timedelta(
                days=task_update.estimated_duration
            )
            db.commit()

    return db_project_task


# delete project task
@router.delete("/{id}/tasks", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    id: int,
    task_id: int,
    db: db_dependence,
    current_user: Annotated[User, Depends(get_current_admin)],
):
    db_project_task = (
        db.query(ProjectTask)
        .filter(ProjectTask.task_id == task_id, ProjectTask.project_id == id)
        .first()
    )
    if db_project_task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project task does not exist."
        )

    # delete project tracking
    db_project_tracking = (
        db.query(ProjectTracking)
        .filter(
            ProjectTracking.project_id == id,
            ProjectTracking.user_id == db_project_task.assignee_id,
        )
        .first()
    )
    if db_project_tracking is not None:
        db.delete(db_project_tracking)

    # delete project task
    db.delete(db_project_task)
    db.commit()


# send email to assignee
@router.post("/{id}/send-email", status_code=status.HTTP_204_NO_CONTENT)
async def send_email_to_assignee(
    id: int,
    notification: NotificationCreate,
    db: db_dependence,
    background_tasks: BackgroundTasks,
    current_user: Annotated[User, Depends(get_current_admin)],
):
    db_project = db.query(Project).filter(Project.id == id).first()
    if db_project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project does not exist."
        )

    # get assignee email
    assignee_id = notification.to_user_id
    assignee = db.query(User).filter(User.id == assignee_id).first()
    if assignee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Assignee does not exist."
        )

    notification.project_id = id
    db.add(notification)
    db.commit()

    # send email
    background_tasks.add_task(
        send_email,
        assignee.email,
        subject=notification.title,
        template_name="notification.html",
        data={"title": notification.title, "content": notification.content},
    )
