# 🚀 DEPLOYMENT ANLEITUNG - YouTube Trending Analyzer MVP

## Du bist hier: Schritt-für-Schritt Deployment

**Aktueller Status**: Projekt ist vollständig programmiert ✅  
**Nächster Schritt**: GitHub → Render → Vercel Deployment

---

## **SCHRITT 1: GitHub Repository erstellen** 📁

### 1.1 GitHub Repository erstellen
1. Gehe zu [github.com](https://github.com) und logge dich ein
2. Klicke oben rechts auf **"+"** → **"New repository"**
3. Fülle aus:
   - **Repository name**: `youtube-trending-analyzer-mvp`
   - **Description**: `LLM-powered YouTube trending analysis platform`
   - **Visibility**: **Public** (wichtig für kostenlose Render/Vercel Nutzung)
   - **NICHT** "Initialize with README" anhaken (haben wir schon)
4. Klicke **"Create repository"**

### 1.2 Lokales Projekt mit GitHub verbinden
Öffne Terminal/Kommandozeile in deinem Projektordner und führe diese Befehle aus:

```bash
# Git Repository initialisieren
git init

# Alle Dateien hinzufügen
git add .

# Ersten Commit erstellen
git commit -m "Initial commit - YouTube Trending Analyzer MVP complete"

# Main Branch erstellen
git branch -M main

# GitHub Repository verbinden (ERSETZE "DEIN-USERNAME" mit deinem GitHub Username!)
git remote add origin https://github.com/DEIN-USERNAME/youtube-trending-analyzer-mvp.git

# Code zu GitHub hochladen
git push -u origin main
```

**✅ Nach diesem Schritt**: Dein Code ist auf GitHub verfügbar!

---

## **SCHRITT 2: Backend auf Render deployen** 🖥️

### 2.1 Render Web Service erstellen
1. Gehe zu [render.com Dashboard](https://dashboard.render.com)
2. Klicke **"New"** → **"Web Service"**
3. Klicke **"Connect a repository"**
4. Verbinde GitHub (falls noch nicht geschehen)
5. Wähle dein Repository `youtube-trending-analyzer-mvp`

### 2.2 Service konfigurieren
Fülle das Formular aus:
- **Name**: `youtube-trending-analyzer-api`
- **Runtime**: `Python 3`
- **Region**: `Frankfurt (EU)` oder `Oregon (US)`
- **Branch**: `main`
- **Build Command**: `cd backend && pip install -r requirements.txt`
- **Start Command**: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Plan**: `Free` (Starter)

### 2.3 Environment Variables setzen
Klicke auf **"Advanced"** → **"Add Environment Variable"** und füge diese hinzu:

```
ENVIRONMENT = production
DEBUG = false
SECRET_KEY = [Render generiert automatisch - leer lassen]
YOUTUBE_API_KEY = dein_youtube_api_schlüssel_hier
GEMINI_API_KEY = dein_gemini_api_schlüssel_hier
LLM_PROVIDER = gemini-flash
LLM_BATCH_SIZE = 20
LLM_MONTHLY_BUDGET = 50.0
CACHE_TTL_SEARCH = 7200
CACHE_TTL_VIDEO = 86400
CACHE_TTL_TRENDING = 3600
YOUTUBE_MAX_RESULTS = 50
YOUTUBE_MAX_COMMENTS = 50
MAX_RESPONSE_TIME = 5.0
TARGET_CACHE_HIT_RATE = 0.70
```

### 2.4 Database und Redis verbinden
**WICHTIG**: Du musst deine bereits erstellten Services verbinden:

1. Füge diese Environment Variables hinzu:
```
DATABASE_URL = [PostgreSQL Connection String von deiner DB]
REDIS_URL = [Redis Connection String von deinem Redis Service]
```

2. Um die Connection Strings zu finden:
   - Gehe zu deinem **PostgreSQL Service** → **"Connect"** → kopiere die **External Connection String**
   - Gehe zu deinem **Redis Service** → **"Connect"** → kopiere die **Connection String**

### 2.5 Deploy starten
1. Klicke **"Create Web Service"**
2. Warte ~5-10 Minuten bis Build fertig ist
3. Notiere dir die URL: `https://dein-service-name.onrender.com`

**✅ Backend Test**: Öffne `https://dein-service-name.onrender.com/api/mvp/health`
Sollte zeigen: `{"status": "healthy", ...}`

---

## **SCHRITT 3: Frontend auf Vercel deployen** 🌐

### 3.1 Vercel Projekt erstellen
1. Gehe zu [vercel.com Dashboard](https://vercel.com/dashboard)
2. Klicke **"New Project"**
3. **"Import Git Repository"**
4. Wähle dein GitHub Repository `youtube-trending-analyzer-mvp`

### 3.2 Build Settings konfigurieren
- **Framework Preset**: `Next.js` (automatisch erkannt)
- **Root Directory**: `frontend`
- **Build Command**: `npm run build` (Standard)
- **Output Directory**: `.next` (Standard)
- **Install Command**: `npm install` (Standard)

### 3.3 Environment Variables setzen
Klicke **"Environment Variables"** und füge hinzu:

```
NEXT_PUBLIC_API_BASE_URL = https://dein-render-service.onrender.com
NEXT_PUBLIC_ENVIRONMENT = production
NEXT_PUBLIC_APP_NAME = YouTube Trending Analyzer MVP
NEXT_PUBLIC_APP_VERSION = 1.0.0
```

**WICHTIG**: Ersetze `https://dein-render-service.onrender.com` mit deiner tatsächlichen Render URL!

### 3.4 Deploy starten
1. Klicke **"Deploy"**
2. Warte ~2-5 Minuten bis Build fertig ist
3. Notiere dir die URL: `https://dein-projekt.vercel.app`

**✅ Frontend Test**: Öffne deine Vercel URL - du solltest die Suchoberfläche sehen!

---

## **SCHRITT 4: Integration testen** 🧪

### 4.1 Backend Health Check
Teste diese URLs (ersetze mit deiner Render URL):
- Health: `https://dein-service.onrender.com/api/mvp/health`
- API Docs: `https://dein-service.onrender.com/docs`

### 4.2 Frontend Integration testen
1. Öffne deine Vercel Frontend URL
2. Probiere eine Suche:
   - **Query**: "music"
   - **Country**: "USA"  
   - **Timeframe**: "48 hours"
3. Klicke **"Analyze Trending Videos"**

**✅ Erfolg**: Du solltest Ergebnisse mit YouTube Videos sehen!

### 4.3 Troubleshooting
Falls Fehler auftreten:

**CORS Fehler**: 
- Prüfe ob `NEXT_PUBLIC_API_BASE_URL` korrekt gesetzt ist
- Backend URL muss genau stimmen (ohne Slash am Ende)

**500 Server Error**:
- Prüfe Render Logs: Dashboard → Service → "Logs"
- Überprüfe API Keys sind korrekt gesetzt

**Keine Ergebnisse**:
- Prüfe Budget Status: `https://dein-service.onrender.com/api/mvp/analytics/budget`

---

## **SCHRITT 5: Monitoring einrichten** 📊

### 5.1 Wichtige URLs bookmarken
- **Frontend**: `https://dein-projekt.vercel.app`
- **Backend Health**: `https://dein-service.onrender.com/api/mvp/health`
- **Budget Monitor**: `https://dein-service.onrender.com/api/mvp/analytics/budget`
- **System Analytics**: `https://dein-service.onrender.com/api/mvp/analytics/system`

### 5.2 Budget Überwachung
**WICHTIG**: Überwache regelmäßig die Kosten!
- **Ziel**: <€50/Monat
- **Check täglich**: Budget Status URL
- **Bei >€40/Monat**: Cache TTL erhöhen oder weniger Suchen

---

## **🎉 DEPLOYMENT COMPLETE!**

Wenn alle Schritte erfolgreich waren, hast du:
- ✅ Funktionierendes Backend auf Render
- ✅ Funktionierendes Frontend auf Vercel  
- ✅ Vollständige YouTube Trending Analyse
- ✅ Budget-optimierte LLM Integration
- ✅ Multi-Country Support (DE/US/FR/JP)

**Nächste Schritte**:
1. Teile die Frontend URL mit anderen zum Testen
2. Überwache Budget und Performance
3. Bei Problemen: Logs in Render/Vercel prüfen

**Support**: Bei Fragen schau in die Logs oder teste die Health Endpoints!