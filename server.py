import csv, io, os, sqlite3
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

DB_PATH = os.environ.get("DB_PATH", "/tmp/contatti.db")
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "residenze2026")
HEADERS = ["Data","Nome","Cognome","Email","Telefono","Villa","Capitolato","Messaggio"]

db = sqlite3.connect(DB_PATH, check_same_thread=False)
db.row_factory = sqlite3.Row
db.execute("CREATE TABLE IF NOT EXISTS contatti (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, nome TEXT, cognome TEXT, email TEXT, telefono TEXT, villa TEXT, capitolato TEXT, messaggio TEXT)")
db.commit()

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class ContactForm(BaseModel):
    nome: str
    cognome: str
    email: str
    telefono: Optional[str] = ""
    villa: Optional[str] = ""
    capitolato: Optional[str] = ""
    messaggio: Optional[str] = ""

@app.post("/api/contact")
async def contact(data: ContactForm):
    db.execute("INSERT INTO contatti (data,nome,cognome,email,telefono,villa,capitolato,messaggio) VALUES (?,?,?,?,?,?,?,?)",
        (datetime.now().strftime("%Y-%m-%d %H:%M"), data.nome, data.cognome, data.email, data.telefono, data.villa, data.capitolato, data.messaggio))
    db.commit()
    return {"ok": True}

@app.get("/api/health")
def health():
    return {"status": "ok", "contatti": db.execute("SELECT COUNT(*) FROM contatti").fetchone()[0]}

@app.get("/api/contacts/export")
def export(token: str = ""):
    if token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Non autorizzato")
    rows = db.execute("SELECT data,nome,cognome,email,telefono,villa,capitolato,messaggio FROM contatti ORDER BY id").fetchall()
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(HEADERS)
    for r in rows:
        w.writerow(list(r))
    buf.seek(0)
    return StreamingResponse(iter([buf.getvalue()]), media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=contatti.csv"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
