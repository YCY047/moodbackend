from fastapi import FastAPI, Form, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from datetime import date, datetime
import os, json

app = FastAPI()

os.makedirs("uploads", exist_ok=True)
os.makedirs("static", exist_ok=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_FILE = "moods.json"

def read_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def write_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@app.post("/mood")
async def post_mood(user: str = Form(...), mood: str = Form(...), score: int = Form(...)):
    today = str(date.today())
    data = read_data()

    if today not in data:
        data[today] = {}
    if user not in data[today]:
        data[today][user] = []

    entry = {
        "mood": {
            "text": mood,
            "score": score
        },
        "time": datetime.now().isoformat()
    }
    data[today][user].append(entry)

    write_data(data)
    return {"message": "心情已儲存"}

@app.post("/photo")
async def upload_photo(
    user: str = Form(...),
    description: str = Form(...),
    file: UploadFile = File(...)
):
    filename = f"{user}_{file.filename}"
    file_path = os.path.join("uploads", filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())

    today = str(date.today())
    data = read_data()

    if today not in data:
        data[today] = {}
    if user not in data[today]:
        data[today][user] = []

    # 嘗試找到最後一筆沒有 photo 的 entry
    for entry in reversed(data[today][user]):
        if "photo" not in entry:
            entry["photo"] = {
                "file": filename,
                "description": description
            }
            break
    else:
        # 若沒有找到，新增新的 entry 並加上時間
        data[today][user].append({
            "photo": {
                "file": filename,
                "description": description
            },
            "time": datetime.now().isoformat()
        })

    write_data(data)
    return {"message": "照片已上傳"}

@app.get("/uploads/{filename}")
async def get_image(filename: str):
    return FileResponse(os.path.join("uploads", filename))

@app.get("/", response_class=HTMLResponse)
async def index():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/mood_list", response_class=HTMLResponse)
async def mood_list():
    with open("static/mood_list.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/summary/all")
async def get_all_summary():
    return read_data()

@app.delete("/clear/today")
async def clear_today():
    today = str(date.today())
    data = read_data()
    if today in data:
        del data[today]
        write_data(data)
        return {"message": f"已清除 {today} 的心情日記"}
    else:
        return {"message": f"{today} 沒有心情日記可清除"}

@app.delete("/clear/all")
async def clear_all():
    write_data({})
    return {"message": "已清除所有心情日記"}

# 掛載 static 資料夾作為網站根目錄
app.mount("/", StaticFiles(directory="static", html=True), name="static")
