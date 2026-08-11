import json
from pathlib import Path
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

BASE_DIR = Path(__file__).resolve().parent.parent
WEB_DIR = BASE_DIR / 'web'
DATA_FILE = BASE_DIR / 'data' / 'prematch_matches.json'

app = Flask(__name__, static_folder=None)
CORS(app)

def load_matches():
    try:
        return json.loads(DATA_FILE.read_text(encoding='utf-8'))
    except Exception:
        return []

def implied(odds):
    vals = {}
    for item in odds or []:
        try:
            n = int(item.get('N'))
            o = float(item.get('O'))
            if o > 1: vals[n] = 1 / o
        except Exception:
            pass
    total = sum(vals.values())
    return {k: v / total for k, v in vals.items()} if total else {}

@app.get('/health')
def health():
    return jsonify(status='ok', service='PredictaIQ')

@app.get('/')
def index():
    return send_from_directory(WEB_DIR, 'index.html')

@app.get('/<path:path>')
def static_file(path):
    return send_from_directory(WEB_DIR, path)

@app.get('/api/matches')
def matches():
    data = []
    for m in load_matches():
        if m.get('home') and m.get('away'):
            ms = next((b.get('oranlar') for b in m.get('oranlar', []) if b.get('bahis_tipi') == 1), None)
            p = implied(ms)
            data.append({'home': m['home'], 'away': m['away'], 'time': m.get('time'), 'probabilities': p})
    return jsonify(data[:50])

@app.post('/predict')
def predict():
    payload = request.get_json(silent=True) or {}
    home = str(payload.get('homeTeam', '')).strip()
    away = str(payload.get('awayTeam', '')).strip()
    if not home or not away:
        return jsonify(error='homeTeam ve awayTeam gerekli'), 400
    for m in load_matches():
        if m.get('home','').strip().lower() == home.lower() and m.get('away','').strip().lower() == away.lower():
            ms = next((b.get('oranlar') for b in m.get('oranlar', []) if b.get('bahis_tipi') == 1), None)
            p = implied(ms)
            if p:
                labels = {1:'MS 1', 2:'MS X', 3:'MS 2'}
                best = max(p, key=p.get)
                return jsonify(prediction=f'{labels.get(best, "Favori")} | %{p[best]*100:.1f} olasilik (oranlardan hesaplanan istatistiksel tahmin)', probabilities={labels.get(k,str(k)):round(v*100,1) for k,v in p.items()})
    return jsonify(prediction='Bu mac icin veri bulunamadi.'), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
