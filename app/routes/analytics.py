from datetime import datetime
from fastapi import HTTPException, APIRouter, Depends, Query
from typing import Annotated, List, Optional
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.project_task import ProjectTask
from app.models.task import Task
from app.routes.auth import get_current_admin
from app.models.project import Project, ProjectStatus, ProjectPriority
from app.models.user import User
from app.schemas.analytics import (
    ProjectBudgetResponse,
    ProjectDurationResponse,
    ProjectSummaryResponse,
)

router = APIRouter(tags=["analytics"], prefix="/analytics")
db_dependence = Annotated[Session, Depends(get_db)]


#
@router.post("/duration", response_model=List[ProjectDurationResponse])
async def get_projects_duration_comparison(
    db: db_dependence, current_user: Annotated[User, Depends(get_current_admin)]
):
    db_projects = (
        db.query(Project)
        .filter(
            Project.company_id == current_user.company_id,
            Project.status == ProjectStatus.COMPLETED,  # only completed projects
        )
        .order_by(Project.created_at.desc())  # order by created_at in descending order
        .limit(10)  # limit to 10 projects
        .all()
    )

    if not db_projects:
        raise HTTPException(status_code=404, detail="No projects found")

    result = []
    for project in db_projects:
        actual_duration = None
        if project.actual_end_date and project.start_date:
            actual_duration = (project.actual_end_date - project.start_date).days

        result.append(
            {
                "name": project.name,
                "estimated_duration": project.estimated_duration,
                "actual_duration": actual_duration,
            }
        )

    return result


@router.post("/budget", response_model=List[ProjectBudgetResponse])
async def get_projects_budget_comparison(
    db: db_dependence,
    current_user: Annotated[User, Depends(get_current_admin)],
    start_date: Optional[str] = Query(None, description="Start date in YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="End date in YYYY-MM-DD"),
):
    query = db.query(Project)

    # Filter by start_date and end_date
    if start_date:
        try:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(Project.start_date >= start_date_obj)
        except ValueError:
            raise HTTPException(
                status_code=400, detail="Invalid start_date format. Use YYYY-MM-DD"
            )

    if end_date:
        try:
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
            query = query.filter(Project.start_date <= end_date_obj)
        except ValueError:
            raise HTTPException(
                status_code=400, detail="Invalid end_date format. Use YYYY-MM-DD"
            )

    projects = query.order_by(
        Project.budget.desc()
    ).all()  # order by budget in descending order

    if not projects:
        raise HTTPException(status_code=404, detail="No projects found")

    return [{"name": project.name, "budget": project.budget} for project in projects]


@router.post("/{id}", response_model=ProjectSummaryResponse)
async def get_project_detail_comparison(
    id: int,
    db: db_dependence,
    current_user: Annotated[User, Depends(get_current_admin)],
):
    # get project by id
    project = db.query(Project).filter(Project.id == id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # calculate project completion (percentage)
    total_tasks = db.query(ProjectTask).filter(ProjectTask.project_id == id).count()
    completed_tasks = (
        db.query(ProjectTask)
        .filter(ProjectTask.project_id == id, ProjectTask.status == "completed")
        .count()
    )
    completion = (
        round((completed_tasks / total_tasks) * 100, 2) if total_tasks > 0 else 0
    )

    # get task budgets
    task_budgets = (
        db.query(Task.name, ProjectTask.budget)
        .join(ProjectTask, Task.id == ProjectTask.task_id)
        .filter(ProjectTask.project_id == id)
        .all()
    )

    # get task durations
    task_durations = (
        db.query(
            Task.name,
            ProjectTask.duration,
            ProjectTask.actual_end_date,
            ProjectTask.start_date,
        )
        .join(ProjectTask, Task.id == ProjectTask.task_id)
        .filter(ProjectTask.project_id == id)
        .all()
    )

    return {
        "project_name": project.name,
        "total_budget": project.budget,
        "estimated_duration": project.estimated_duration,
        "actual_duration": (
            (project.actual_end_date - project.start_date).days
            if project.actual_end_date and project.start_date
            else None
        ),
        "completion": completion,
        "task_budgets": [
            {"task_name": name, "budget": budget} for name, budget in task_budgets
        ],
        "task_durations": [
            {
                "task_name": name,
                "duration": (
                    (actual_end_date - start_date).days
                    if actual_end_date and start_date
                    else duration
                ),
            }
            for name, duration, actual_end_date, start_date in task_durations
        ],
    }
