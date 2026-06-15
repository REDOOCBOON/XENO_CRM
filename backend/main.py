import uvicorn
from app.main import app

if __name__ == "__main__":
    # This entry point is automatically detected by Railpack/Railway
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
