from fastapi import APIRouter, HTTPException, Depends
from typing import Annotated,List
from sqlalchemy.orm import Session
from app.database import get_db
from app.routes.auth import get_current_user
from starlette import status
from app.schemas.project_task import ProjectTaskBase, ProjectTaskCreate
from app.models.user import User
from app.models.project import Project
from app.models.project_task import ProjectTask

router = APIRouter(tags=['projects'], prefix="/projects")
db_dependence = Annotated[Session,Depends(get_db)]

# post project details
@router.post('/', response_model=ProjectTaskBase)
async def create_project(db:db_dependence, project: ProjectTaskCreate, current_user:Annotated[User, Depends(get_current_user)]):
    # check proejct existence
    db_project= db.query(Project).filter(Project.name == project.name).first()
    if  db_project:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Project already exists.")
    # create new project and update in the PROJECT table
    new_project = Project(
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
    db.add(new_project)
    db.commit()
    db.refresh(new_project)

    # update PORJECT_TASK TABLE
    for task_id in project.task_ids:
        db_task = db.query(Task).filter(Task.id == task_id).first()
        if db_task is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with id {task_id} not found."
            )
        
        project_task = ProjectTask(
            project_id=new_project.id,
            task_id=db_task.id,
            assignee_id=None,  
            status=TaskStatus.PENDING,  
            start_date=new_project.start_date, 
            end_date=new_project.end_date,
            actual_end_date=None,  
            budget=new_project.budget,  
            amount_due=new_project.amount_due,  
            dependency=None, 
            notes=None  
        ) 
        db.add(project_task)
       
    db.commit() 
    return new_project
