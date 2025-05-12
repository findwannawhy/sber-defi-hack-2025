import uvicorn
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.db import init_db
from app.auth.routes import router as auth_router
from app.users.routes import router as users_router
from app.contracts.routes import router as contracts_router
from app.audit.routes import router as audit_router
from app.visualise.routes import router as visualise_router
from app.notification.routes import router as notification_router
#from fastapi.middleware.forwarded import ForwardedHeadersMiddleware


app = FastAPI(title="Smart-Contract Tracker API")

#app.add_middleware(ForwardedHeadersMiddleware, trusted_hosts=["http://147.45.66.207.nip.io:3000"])


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SessionMiddleware, secret_key=settings.SESSION_SECRET, domain=".nip.io", same_site='lax', https_only=False)

app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(users_router, prefix="/users", tags=["users"])
app.include_router(contracts_router, prefix="/contracts", tags=["contracts"])
app.include_router(audit_router, prefix="/audit", tags=["audit"])
app.include_router(visualise_router, prefix="/visualise", tags=["visualise"])
app.include_router(notification_router, prefix="/notification", tags=["notification"])

@app.on_event("startup")
async def on_startup():
    await init_db()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
