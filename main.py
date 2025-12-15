from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os
from datetime import datetime, timedelta
from typing import List, Dict
import requests
import feedparser
from urllib.parse import urlparse
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

app = FastAPI()

# Production CORS configuration
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

if ENVIRONMENT == "production":
    origins = [origin.strip() for origin in ALLOWED_ORIGINS if origin.strip()]
else:
    origins = ["*"]

logger.info(f"Environment: {ENVIRONMENT}")
logger.info(f"Allowed origins: {origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Données d'actualités avec de vrais liens
news_data = {
    "Quantique Générale": [
        {"title": "IBM dévoile son processeur quantique Condor", "url": "https://www.ibm.com/quantum"},
        {"title": "Google annonce des avancées en correction d'erreurs quantiques", "url": "https://blog.google/technology/ai/google-willow-quantum-chip/"},
        {"title": "IonQ lève 300 millions de dollars pour l'informatique quantique", "url": "https://ionq.com/"},
        {"title": "Atom Computing construit un ordinateur quantique de 1000 qubits", "url": "https://www.atom-computing.com/"},
    ],
    "PQC": [
        {"title": "NIST finalise les standards de cryptographie post-quantique", "url": "https://csrc.nist.gov/projects/post-quantum-cryptography/"},
        {"title": "Microsoft lance son framework de cryptographie post-quantique", "url": "https://www.microsoft.com/en-us/security/"},
        {"title": "Guide pratique: Migration vers la PQC", "url": "https://blog.cloudflare.com/post-quantum-cryptography/"},
        {"title": "AWS ajoute le support de la cryptographie post-quantique", "url": "https://aws.amazon.com/"},
    ]
}

# Servir les fichiers statiques depuis le dossier static/
app.mount("/static", StaticFiles(directory="static"), name="static")

# Route pour la page d'accueil (index.html reste à la racine)
@app.get("/")
def root():
    return FileResponse("index.html")

# --- RSS SOURCES ---
PQC_RSS_SOURCES = [
    # Standards / Gov
    "https://www.microsoft.com/en-us/security/blog/feed/",# Microsoft Security Blog
    "https://security.googleblog.com/atom.xml",           # Google Security Blog
    "https://research.ibm.com/blog/rss",                  # IBM Research Blog
    # Media / Research
    "https://spectrum.ieee.org/rss/fulltext",             # IEEE Spectrum
    "https://www.futura-sciences.com/rss/actualites.xml", # Futura-Sciences
    # arXiv PQC/crypto/quantum channels (general feed then filtered)
    "https://arxiv.org/rss/cs.CR",
    "https://arxiv.org/rss/quant-ph",
]

QUANTUM_RSS_SOURCES = [
    "https://research.ibm.com/blog/rss",
    "https://blog.google/technology/quantum/rss/",
    "https://spectrum.ieee.org/rss/fulltext",
    "https://www.futura-sciences.com/rss/actualites.xml",
    "https://arxiv.org/rss/quant-ph",
    "https://physicsworld.com/feed/",
]

def _soft_match(title: str, keywords: list[str]) -> bool:
    tl = (title or "").lower()
    return any(k in tl for k in keywords)

def _dedup_items(items: list[Dict]) -> list[Dict]:
    seen = set()
    out = []
    for it in items:
        url = it.get("url")
        if not url or url in seen:
            continue
        seen.add(url)
        out.append(it)
    return out

def fetch_rss_items(urls: list[str], keywords: list[str]) -> List[Dict]:
    results: List[Dict] = []
    for feed_url in urls:
        try:
            logger.info(f"[RSS] Fetching {feed_url}")
            parsed = feedparser.parse(feed_url)
            logger.info(f"[RSS] Found {len(parsed.get('entries', []))} entries")
            for entry in parsed.get("entries", []):
                title = entry.get("title", "").strip()
                link = entry.get("link")
                if not link or not title:
                    continue
                if _soft_match(title, keywords):
                    results.append({"title": title, "url": link})
                    logger.debug(f"[RSS] Match: {title[:50]}...")
        except Exception as e:
            logger.error(f"[RSS] Error parsing {feed_url}: {e}")
            continue
    deduped = _dedup_items(results)
    logger.info(f"[RSS] Total after dedup: {len(deduped)}")
    return deduped

# --- NEWSAPI (SOFT FILTERS) ---
def fetch_newsapi_pqc() -> List[Dict]:
    api_key = os.getenv("NEWSAPI_KEY")
    if not api_key or api_key == "your_api_key_here":
        logger.warning("[NewsAPI PQC] No valid API key found")
        return [{"title": "Configurez NEWSAPI_KEY dans .env pour voir les articles PQC.", "url": "https://newsapi.org/"}]
    url = "https://newsapi.org/v2/everything"
    query = (
        "(post-quantum OR \"post quantum\" OR PQC OR \"quantum-safe\" OR \"quantum resistant\" "
        "OR \"post-quantum cryptography\" OR Kyber OR Dilithium OR ML-KEM OR ML-DSA)"
    )
    params = {
        "q": query,
        "sortBy": "publishedAt",
        "pageSize": 100,
        "language": "en",
        "apiKey": api_key,
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        logger.info(f"[NewsAPI PQC] Found {len(data.get('articles', []))} articles")
        items = []
        soft_keywords = ["post-quantum", "pqc", "quantum-safe", "kyber", "dilithium", "ml-kem", "ml-dsa", "quantum"]
        for a in data.get("articles", []):
            title = (a.get("title") or "").strip()
            link = a.get("url")
            if not link or not title:
                continue
            if _soft_match(title, soft_keywords):
                items.append({"title": title, "url": link})
                logger.debug(f"[NewsAPI PQC] Match: {title[:50]}...")
        deduped = _dedup_items(items)
        logger.info(f"[NewsAPI PQC] Total after dedup: {len(deduped)}")
        return deduped
    except Exception as e:
        logger.error(f"[NewsAPI PQC] Error: {e}")
        return []

def fetch_newsapi_quantum() -> List[Dict]:
    api_key = os.getenv("NEWSAPI_KEY")
    if not api_key or api_key == "your_api_key_here":
        logger.warning("[NewsAPI Quantum] No valid API key found")
        return [{"title": "Configurez NEWSAPI_KEY dans .env pour voir les articles Quantique.", "url": "https://newsapi.org/"}]
    url = "https://newsapi.org/v2/everything"
    query = (
        "(\"quantum computing\" OR \"quantum computer\" OR qubit OR \"quantum processor\" OR \"quantum algorithm\" "
        "OR \"quantum error correction\" OR superconducting OR trapped-ion OR photonic OR spin-qubit "
        "OR \"informatique quantique\" OR \"ordinateur quantique\" OR \"processeur quantique\" OR \"algorithme quantique\" "
        "OR Pasqal OR Quobly OR C12 OR OVHcloud OR CEA OR CNRS)"
    )
    
    def call(lang: str) -> List[Dict]:
        params = {
            "q": query,
            "sortBy": "publishedAt",
            "pageSize": 100,
            "language": lang,
            "apiKey": api_key,
        }
        try:
            r = requests.get(url, params=params, timeout=10)
            r.raise_for_status()
            data = r.json()
            logger.info(f"[NewsAPI Quantum {lang}] Found {len(data.get('articles', []))} articles")
            items = []
            soft_keywords = [
                "quantum", "qubit", "processor", "algorithm", "error correction",
                "informatique quantique", "ordinateur quantique", "processeur quantique",
                "pasqal", "quobly", "c12", "ovhcloud", "cea", "cnrs", "atomes neutres", "photoniques"
            ]
            for a in data.get("articles", []):
                title = (a.get("title") or "").strip()
                link = a.get("url")
                if not link or not title:
                    continue
                if _soft_match(title, soft_keywords):
                    items.append({"title": title, "url": link})
                    logger.debug(f"[NewsAPI Quantum {lang}] Match: {title[:50]}...")
            deduped = _dedup_items(items)
            logger.info(f"[NewsAPI Quantum {lang}] Total after dedup: {len(deduped)}")
            return deduped
        except Exception as e:
            logger.error(f"[NewsAPI Quantum {lang}] Error: {e}")
            return []
    
    items = call("fr")
    if not items:
        items = call("en")
    return items

# Add debug endpoint
@app.get("/debug")
def debug_info():
    api_key = os.getenv("NEWSAPI_KEY")
    return {
        "environment": ENVIRONMENT,
        "api_key_configured": bool(api_key and api_key != "your_api_key_here"),
        "api_key_length": len(api_key) if api_key else 0,
        "allowed_origins": origins
    }

# --- MERGE STRATEGY: RSS first, then NewsAPI, dedup ---
@app.get("/news")
def get_news() -> Dict[str, List[Dict[str, str]]]:
    logger.info("\n[GET /news] Starting aggregation...")
    logger.info(f"API Key configured: {bool(os.getenv('NEWSAPI_KEY'))}")
    
    # PQC
    pqc_keywords = [
        "post-quantum", "post quantum", "pqc", "quantum-safe", "kyber", "dilithium", "ml-kem", "ml-dsa",
        "post-quantum cryptography", "cryptographie post-quantique"
    ]
    pqc_rss = fetch_rss_items(PQC_RSS_SOURCES, pqc_keywords)
    logger.info(f"[PQC] After RSS: {len(pqc_rss)} items")
    
    pqc_api = fetch_newsapi_pqc()
    logger.info(f"[PQC] After NewsAPI: {len(pqc_api)} items")
    
    pqc_all = _dedup_items(pqc_rss + pqc_api)[:100]
    logger.info(f"[PQC] RSS: {len(pqc_rss)}, API: {len(pqc_api)}, Total: {len(pqc_all)}")

    # Quantum générale
    quantum_keywords = [
        "quantum computing", "quantum computer", "qubit", "quantum processor", "quantum algorithm",
        "quantum error correction", "superconducting", "trapped-ion", "photonic", "spin qubit",
        "informatique quantique", "ordinateur quantique", "processeur quantique",
        "atomes neutres", "photoniques", "pasqal", "quobly", "c12", "ovhcloud", "cea", "cnrs"
    ]
    quantum_rss = fetch_rss_items(QUANTUM_RSS_SOURCES, quantum_keywords)
    logger.info(f"[Quantum] After RSS: {len(quantum_rss)} items")
    
    quantum_api = fetch_newsapi_quantum()
    logger.info(f"[Quantum] After NewsAPI: {len(quantum_api)} items")
    
    quantum_all = _dedup_items(quantum_rss + quantum_api)[:100]
    logger.info(f"[Quantum] RSS: {len(quantum_rss)}, API: {len(quantum_api)}, Total: {len(quantum_all)}")

    result: Dict[str, List[Dict[str, str]]] = {}
    result["PQC (Ce mois)"] = pqc_all if pqc_all else [
        {"title": "Aucun article PQC pour l'instant (RSS/API).", "url": "https://csrc.nist.gov/projects/post-quantum-cryptography"}
    ]
    result["Quantique Générale (Ce mois)"] = quantum_all if quantum_all else [
        {"title": "Aucun article Quantique pour l'instant (RSS/API).", "url": "https://arxiv.org/list/quant-ph/recent"}
    ]
    logger.info(f"[GET /news] Returning {len(result)} categories\n")
    return result

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
