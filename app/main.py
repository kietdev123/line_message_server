from fastapi import FastAPI, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import secrets
import json

from . import models
from .database import engine, get_db
from .line_service import LineService

models.Base.metadata.create_all(bind=engine)

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(username: str = Form(...), db: Session = Depends(get_db)):
    # Generate nonce
    nonce = secrets.token_urlsafe(32)
    
    # Save nonce to database
    nonce_record = models.Nonce(nonce=nonce, username=username)
    db.add(nonce_record)
    
    # Create or get user
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        user = models.User(username=username)
        db.add(user)
    
    db.commit()
    
    return RedirectResponse(url="/link", status_code=303)

@app.get("/link")
async def link(db: Session = Depends(get_db)):
    # Get the latest nonce (this is a simplified approach)
    nonce_record = db.query(models.Nonce).order_by(models.Nonce.id.desc()).first()
    if not nonce_record:
        raise HTTPException(status_code=400, detail="No nonce found")
    
    # Get user
    user = db.query(models.User).filter(models.User.username == nonce_record.username).first()
    if not user:
        raise HTTPException(status_code=400, detail="User not found")
    
    if not user.line_user_id:
        # User not linked yet, create link URL
        try:
            link_token = LineService.get_link_token(user.line_user_id)
            link_url = LineService.create_link_url(link_token, nonce_record.nonce)
            return {"link_url": link_url}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    else:
        return {"message": "Account already linked"}

@app.post("/webhook")
async def webhook(request: Request, db: Session = Depends(get_db)):
    body = await request.body()
    signature = request.headers.get("X-Line-Signature")
    
    if not LineService.verify_signature(body, signature):
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    events = json.loads(body)["events"]
    for event in events:
        if event["type"] == "accountLink":
            if event["link"]["result"] == "ok":
                nonce = event["link"]["nonce"]
                line_user_id = event["source"]["userId"]
                
                # Find user by nonce
                nonce_record = db.query(models.Nonce).filter(models.Nonce.nonce == nonce).first()
                if nonce_record:
                    user = db.query(models.User).filter(
                        models.User.username == nonce_record.username
                    ).first()
                    if user:
                        user.line_user_id = line_user_id
                        db.commit()
                        LineService.send_message(line_user_id, "Account linked successfully!")
        
        elif event["type"] == "message":
            line_user_id = event["source"]["userId"]
            user = db.query(models.User).filter(models.User.line_user_id == line_user_id).first()
            
            if user:
                LineService.send_message(line_user_id, "Your account is already linked!")
            else:
                # Create new nonce for linking
                nonce = secrets.token_urlsafe(32)
                nonce_record = models.Nonce(nonce=nonce, username=f"line_{line_user_id}")
                db.add(nonce_record)
                db.commit()
                
                try:
                    link_token = LineService.get_link_token(line_user_id)
                    link_url = LineService.create_link_url(link_token, nonce)
                    LineService.send_message(
                        line_user_id,
                        f"Please link your account using this URL: {link_url}"
                    )
                except Exception as e:
                    print(f"Error creating link URL: {str(e)}")
    
    return {"message": "OK"}

@app.post("/send-message")
async def send_message(user_id: int, message: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user or not user.line_user_id:
        raise HTTPException(status_code=404, detail="User not found or not linked")
    
    success = LineService.send_message(user.line_user_id, message)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send message")
    
    return {"message": "Message sent successfully"}

@app.get("/users")
async def get_users(db: Session = Depends(get_db)):
    users = db.query(models.User).all()
    return [{"id": user.id, "username": user.username, "is_linked": bool(user.line_user_id)} 
            for user in users] 