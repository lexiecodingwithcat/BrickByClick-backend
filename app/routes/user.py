from fastapi import APIRouter, HTTPException, Depends
from passlib.context import CryptContext
from models import User
from schemas import UserBase, userCreate, UserUpdate, UserDelete


#the function of annotated:
# Specify the type: Informs FastAPI and type-checking tools that the type of db_dependency is Session.
# Bind the dependency: Uses Depends(get_db) to tell FastAPI that the Session instance is provided by get_db.
router = APIRouter(tags=["users"], prefix="/users");
db_dependency = Annotated[Session, Depends(get_db)]
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.get("/", response_model=List[UserBase])
async def get_users(db: db_dependency):
    db_users = db.query(User).all()
    return db_users

@router.get("/{id}", response_model=UserBase)
async def get_user(id: int, db: db_dependency):
    db_user = db.query(User).filter(User.id == id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@router.post("/", response_model=UserBase)
async def create_user(user: userCreate, db: db_dependency):
    # encrypt the password
    hashed_password = pwd_context.hash(user.password)
    db_users = User(first_name=user.first_name, last_name=user.last_name, email=user.email, password=hashed_password)
    db.add(db_users)
    db.commit()
    db.refresh(db_users)
    return db_users

@router.put("/{id}", response_model=UserBase)
async def update_user(id:int, user: UserUpdate, db:db_dependency):
    db_user = db.query(User).filter(User.id == id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    db_user.first_name = user.first_name
    db_user.last_name = user.last_name
    db_user.email = user.email
    db_user.password = pwd_context.hash(user.password)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.delete("/{id}", status_code=204)
def delete_user(id:int, db:db_dependency):
    db_user = db.query(User).filter(User.id == id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(db_user)
    db.commit()
    return db_user