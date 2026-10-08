"""Official-source downloader: TLS verification, disk cache, shared 1 request/s limit."""
import fcntl
import hashlib
import json
from pathlib import Path
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
ALLOWED = {"www.boe.es", "boe.es", "www.caib.es", "caib.es"}


def official_url(url):
    p = urllib.parse.urlsplit(url)
    if p.scheme != "https" or p.hostname not in ALLOWED or p.username or p.password:
        raise ValueError("Solo se admiten URLs HTTPS de BOE/CAIB")
    return url


class OfficialRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        official_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def download(url, *, accept="application/xml", refresh=False):
    official_url(url)
    cache = ROOT / "data/cache"
    raw = ROOT / "data/raw"
    cache.mkdir(parents=True, exist_ok=True)
    raw.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha256((url + '\n' + accept).encode()).hexdigest()
    manifest = cache / (key + '.json')
    with (cache / '.lock').open('a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if manifest.exists() and not refresh:
            m = json.loads(manifest.read_text())
            path = ROOT / m['archivo']
            if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest() == m['sha256']:
                return path, m
        stamp = cache / 'last_request'
        previous = float(stamp.read_text()) if stamp.exists() else 0
        time.sleep(max(0, 1.05 - (time.time() - previous)))
        request = urllib.request.Request(url, headers={
            'User-Agent': 'PLStudy/0.1 (personal study; official legislation audit)',
            'Accept': accept,
        })
        # Redirects are disallowed here to keep every HTTP request under the limiter.
        opener = urllib.request.build_opener(NoRedirect())
        stamp.write_text(str(time.time()))
        try:
            with opener.open(request, timeout=45) as response:
                body = response.read()
                content_type = response.headers.get('Content-Type', '')
                final = response.url
        except urllib.error.HTTPError as error:
            if error.code in (301, 302, 303, 307, 308):
                target = urllib.parse.urljoin(url, error.headers.get('Location', ''))
                official_url(target)
                # Release lock before the recursive request.
                fcntl.flock(lock, fcntl.LOCK_UN)
                return download(target, accept=accept, refresh=refresh)
            raise
        sha = hashlib.sha256(body).hexdigest()
        suffix = '.pdf' if body.startswith(b'%PDF') else '.xml' if 'xml' in content_type else '.html'
        path = raw / (sha + suffix)
        if not path.exists():
            path.write_bytes(body)
        m = dict(url_solicitada=url, url_final=final, sha256=sha,
                 archivo=str(path.relative_to(ROOT)), content_type=content_type,
                 fecha_descarga=datetime.now(timezone.utc).isoformat())
        manifest.write_text(json.dumps(m, ensure_ascii=False, indent=2) + '\n')
        return path, m


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None
