from datetime import timedelta
from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks
from typing import Annotated, List
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.notification import Notification
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
@router.post("/contractor", response_model=List[ProjectTaskBase])
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
    # print("result:", result)
    return result


@router.post("/all", response_model=List[ProjectBase])
async def get_all_projects(
    db: db_dependence, current_user: Annotated[User, Depends(get_current_admin)]
):
    db_projects = (
        db.query(Project).filter(Project.company_id == current_user.company_id).all()
    )
    return [ProjectBase.model_validate(project) for project in db_projects]


# projectTask detail: project detail, task list, gantt chart
@router.post("/{id}", response_model=ProjectWithTasks)
async def get_project_detail(
    id: int,
    db: db_dependence,
    current_user: Annotated[User, Depends(get_current_admin)],
):
    db_project = (
        db.query(Project)
        .filter(Project.id == id, Project.company_id == current_user.company_id)
        .first()
    )

    if db_project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project does not exist"
        )

    # Calculate the total budget of the project, it is actual budget of the project
    actual_budget = (
        db.query(func.sum(ProjectTask.budget))
        .filter(ProjectTask.project_id == id)
        .scalar()
    ) or 0  # if there is no budget, set it to 0

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

    db_project.actual_budget = actual_budget

    response = ProjectWithTasks(project=db_project, tasks=tasks)

    return response


# Create PROJECT, PROJECT_TASK
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
    print("project:", project.model_dump())

    # set company_id from current_user
    project.company_id = current_user.company_id

    # Exclude task_ids from project
    new_project = Project(**project.model_dump(exclude={"task_ids"}))

    # add project into Project table
    try:
        db.add(new_project)
        db.commit()
        db.refresh(new_project)
    except Exception as e:
        db.rollback()  # rollback the transaction
        print("Database Commit Error:", str(e))
        raise HTTPException(status_code=500, detail="Database commit failed")

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
                duration=project.estimated_duration,
                start_date=project.start_date,
                end_date=project.start_date
                + timedelta(days=project.estimated_duration),
            )
            for task_id in project.task_ids
        ]
        db.add_all(project_tasks)
        db.commit()

    return new_project


# Project ONLY
@router.put("/{id}", response_model=ProjectBase)
async def update_project(
    id: int,
    project: ProjectUpdate,
    db: db_dependence,
    current_user: Annotated[User, Depends(get_current_admin)],
):
    db_project = db.query(Project).filter(Project.id == id).first()
    if db_project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project does not exist."
        )
    print(project.model_dump())
    # Get only provided fields
    update_data = project.model_dump(exclude_unset=True)

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
    task: TaskCreate,
    db: db_dependence,
    current_user: Annotated[User, Depends(get_current_admin)],
):
    # Check if the project exists
    db_project = db.query(Project).filter(Project.id == id).first()
    if db_project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project does not exist"
        )
    print("task:", task.model_dump())
    # check the existence of the task
    db_task = db.query(Task).filter(Task.name == task.name).first()
    if db_task is None:
        # add new task to TASK table
        new_task = Task(
            parent_id=task.parent_id,
            name=task.name,
            company_id=current_user.company_id,
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
@router.put(
    "/{id}/tasks",
)
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
        db.query(ProjectTask)
        .filter(
            ProjectTask.task_id == task_update.task_id, ProjectTask.project_id == id
        )
        .first()
    )
    if db_project_task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project task does not exist."
        )
    print("db_project_task:", db_project_task)
    if task_update.start_date is None:
        task_update.start_date = db_project_task.start_date
    if task_update.end_date is None:
        task_update.end_date = db_project_task.end_date

    print("db_project:", id)
    print("task_update:", task_update.model_dump())
    # update project task
    update_data = task_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_project_task, key, value)

    db.commit()
    db.refresh(db_project_task)

    # update project status if task.status is updated
    if "status" in update_data:
        all_tasks = db.query(ProjectTask).filter(ProjectTask.project_id == id).all()
        project_status = determine_project_status(
            all_tasks
        )  # Function to get project status
        print("project_status:", project_status)
        # update project status
        if project_status != db_project.status:
            db_project.status = project_status
            db.commit()
            db.refresh(db_project)

    return db_project_task


def determine_project_status(tasks):
    """
    Determines project status based on all task statuses.
    Example rules:
    - If all tasks are "completed", project is "completed".
    - If any task is "in progress", project is "in progress".
    - If all tasks are "pending", project is "pending".
    """

    statuses = {task.status for task in tasks}
    print("statuses:", statuses)

    if TaskStatus.COMPLETED in statuses and len(statuses) == 1:
        return ProjectStatus.COMPLETED

    if TaskStatus.IN_PROGRESS in statuses:
        return ProjectStatus.IN_PROGRESS

    if TaskStatus.DELAYED in statuses:
        return (
            ProjectStatus.DELAYED
        )  # Assuming delayed tasks are still considered in progress

    if TaskStatus.PENDING in statuses and TaskStatus.COMPLETED not in statuses:
        return ProjectStatus.PENDING

    # Fallback: all statuses the same
    if all(status == TaskStatus.COMPLETED for status in statuses):
        return ProjectStatus.COMPLETED
    if all(status == TaskStatus.PENDING for status in statuses):
        return ProjectStatus.PENDING
    if all(status == TaskStatus.DELAYED for status in statuses):
        return ProjectStatus.DELAYED
    if all(status == TaskStatus.IN_PROGRESS for status in statuses):
        return ProjectStatus.IN_PROGRESS

    return ProjectStatus.IN_PROGRESS  # Default case


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

    db_notification = Notification(
        title=notification.title,
        content=notification.content,
        task_id=notification.task_id,
        to_user_id=notification.to_user_id,
        project_id=id,
    )

    db.add(db_notification)
    db.commit()
    print("email:", assignee.email)
    # send email
    background_tasks.add_task(
        send_email,
        assignee.email,
        subject=notification.title,
        template_name="notification",
        data={"title": notification.title, "content": notification.content},
    )
