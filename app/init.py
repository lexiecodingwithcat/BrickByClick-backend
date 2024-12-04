from app.routes.user import pwd_context
import os
from app.models.user import User

# db_dependency = Annotated[Session, Depends(get_db)]
def initial_admin(db):
    db_user = db.query(User).filter(User.email == "test@example.com").first()
    if db_user is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Email already registered")
    # encrypt the password
    hashed_password = pwd_context.hash(os.getenv("ADMIN_PASSWORD"))
    db_users = User(first_name="test", last_name="demo",
                    email="test@example.com", password=hashed_password, is_admin=True)

    db.add(db_users)
    db.commit()
    db.refresh(db_users)
   
    