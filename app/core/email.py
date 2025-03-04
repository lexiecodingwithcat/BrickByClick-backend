from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import EmailStr
from jinja2 import Environment, select_autoescape, PackageLoader
from app.core.settings import settings
from datetime import datetime
from starlette.responses import JSONResponse

email_conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
)

fastmail = FastMail(email_conf)

env = Environment(
    loader=PackageLoader("app", "templates/email"),
    autoescape=select_autoescape(["html", "xml"]),
)


# Send email
async def send_email(email_to: EmailStr, subject: str, template_name: str, data: dict):
    template = env.get_template(f"{template_name}.html")
    html = template.render(**data)

    message = MessageSchema(
        subject=subject, recipients=[email_to], body=html, subtype="html"
    )

    await fastmail.send_message(message)
    return JSONResponse(status_code=200, content={"message": "email has been sent"})
