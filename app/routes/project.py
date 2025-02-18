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

router = APIRouter(tags=['projects'], prefix="/projects")
db_dependence = Annotated[Session,Depends(get_db)]

@router.get("/",response_model=List[ProjectBase])
async def get_projects(db:db_dependence, current_user:Annotated[User, Depends(get_current_user)]):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,detail = "User is not authorized."
        )
    db_projects = (db.query(Project).join(User).join(City).join(Porvince).all())
    return [
    ProjectBase(
        id=project.id,
        company_id=project.company_id,
        name=project.name,
        current_assignee=f"{db_project.user.first_name} {db_project.user.last_name}", 
        priority=project.priority,  
        address=project.address,
        postal_code=project.postal_code,
        city=project.city.name if project.city else None,  
        province=project.province.name if project.province else None, 
        budget=project.budget,
        status=project.status,  
        start_date=project.start_date,
        estimated_duration=project.estimated_duration,
        end_date=project.end_date,
        actual_end_date=project.actual_end_date,
    )
    for project in db_projects
]

@router.get("/{id}", response_model=ProjectBase)
async def get_project(id: int, db:db_dependence, project:ProjectBase):
    db_project = (
        db.query(Project)
        .join(User)  
        .join(City)  
        .join(Province)  
        .filter(Project.id == id)  
        .first()
    )
    if db_project is None:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND, detail ="Project does not exist"
        )
    return ProjectBase(
        id=project.id,
        company_id=project.company_id,
        name=project.name,
        current_assignee=f"{db_project.user.first_name} {db_project.user.last_name}", 
        priority=project.priority,  
        address=project.address,
        postal_code=project.postal_code,
        city=project.city.name if project.city else None,  
        province=project.province.name if project.province else None, 
        budget=project.budget,
        status=project.status,  
        start_date=project.start_date,
        estimated_duration=project.estimated_duration,
        end_date=project.end_date,
        actual_end_date=project.actual_end_date,)

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
            status_code=status.HTTP_409_CONFLICT, details="Project name already exists."
        )
    first_name = project.current_assignee.split(" ")[0]
    last_name = project.current_assignee.split(" ")[1]

    db_user = db.query(User).filter(User.first_name ==project.first_name and User.last_name == project.last_name ).first()
    user_id = db_user.id
    province_id = db.query(Province).filter(Province.name == project.province).first().id
    city_id = db.query(City).filter(City.name == project.city).first().id
    new_project = Project(name= project.name,current_assignee=user_id,priority = project.priority,address = project.address, postal_code = project.postal_code,city_id = city_id, province_id = province_id,budget = project.budget,status= project.status, start_date = project.start_date, estimated_duration = project.estimated_duration )
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    return new_project



