from fastapi import APIRouter, HTTPException, Depends
from typing import Annotated,List
from sqlalchemy.orm import Session
from app.models.project import Project
from app.models.user import User
from app.models.city import City
from app.models.province import Province
from app.database import get_db
from app.routes.auth import get_current_user
from app.schemas.project import ProjectBase, ProjectCreate, ProjectUpdate
from starlette import status
from sqlalchemy import func
from app.models.project import ProjectPriority, ProjectStatus


router = APIRouter(tags=['projects'], prefix="/projects")
db_dependence = Annotated[Session,Depends(get_db)]

@router.get("/",response_model=List[ProjectBase])
async def get_projects(db:db_dependence, current_user:Annotated[User, Depends(get_current_user)]):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,detail = "User is not authorized."
        )
    db_projects = db.query(Project).all()
    return [ProjectBase.from_orm(project)for project in db_projects
]

@router.get("/{id}", response_model=ProjectBase)
async def get_project(id: int, db:db_dependence, project:ProjectBase):
    db_project = db.query(Project).filter(Project.id == id).first()
    
    if db_project is None:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND, detail ="Project does not exist"
        )
    return db_project

@router.post("/", response_model=ProjectBase)
async def create_project(project: ProjectCreate, db:db_dependence, current_user:Annotated[User, Depends(get_current_user)]):
    # check admin
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,detail = "User is not authorized."
        )
    # check project existence
    db_project = db.query(Project).filter(Project.name == project.name).first()
    if db_project is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Project name already exists."
        )

   
    new_project = Project(name= project.name,current_assignee=project.current_assignee,priority = project.priority,address = project.address, postal_code = project.postal_code,city_id = project.city_id, province_id = project.province_id,budget = project.budget,status= project.status, start_date = project.start_date, estimated_duration = project.estimated_duration )
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    return new_project


@router.put("/{id}",response_model = ProjectBase)
async def update_project(db:db_dependence, id:int, project:ProjectUpdate,current_user:Annotated[User, Depends(get_current_user)]):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,detail = "User is not authorized."
        )
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



