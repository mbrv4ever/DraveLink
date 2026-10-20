#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DraveLink — chat & bestanden delen op je lokale netwerk (LAN).
Onderdeel van de Dravenlock-reeks.

Model: één pc draait DraveLink = ALLEEN de server (deze app toont het webadres en
wie er verbonden is). Iedereen die wil chatten — ook jij — doet dat via de BROWSER
met een gekozen naam. Alles blijft lokaal; er gaat niets over het internet.

Huisstijl: donker + zilver, Nederlands met OS-taaldetectie, Snelgids + Donatie
in de app. Gemaakt voor een onefile .exe (alleen PyQt6 nodig).
"""

import os
import sys
import json
import time
import uuid
import socket
import shutil
import threading
import getpass
import mimetypes
import base64
import html as _html
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QUrl
from PyQt6.QtGui import QPixmap, QPainter, QColor, QBrush, QPen, QIcon, QDesktopServices
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QLineEdit,
    QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, QTextBrowser,
    QFileDialog, QMessageBox, QDialog, QStatusBar, QSpinBox, QComboBox,
)

# ----------------------------------------------------------------------------- constanten
APP_NAME = "DraveLink"
APP_VERSION = "0.6"
CONTACT = "service@dravenlock.nl"
DONATE_URL = "https://paypal.me/roger076"
WEB_PORT = 8080
PEER_TIMEOUT = 30.0

BG = "#0e0e11"; PANEL = "#15151b"; PANEL2 = "#0a0a0c"
SILVER = "#d4d4d4"; ACCENT = "#6fa3d6"; MUTE = "#8b909a"

# ----------------------------------------------------------------------------- config
DEFAULT_CONFIG = {
    "lang": "", "name": "", "uuid": "", "web_port": WEB_PORT, "access_code": "",
    "download_dir": "", "share_dir": "",
}


def _app_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def _config_path():
    return os.path.join(_app_dir(), "dravelink_config.json")


def load_config():
    cfg = dict(DEFAULT_CONFIG)
    try:
        with open(_config_path(), "r", encoding="utf-8") as f:
            cfg.update(json.load(f))
    except Exception:
        pass
    if not cfg.get("uuid"):
        cfg["uuid"] = uuid.uuid4().hex
    return cfg


def save_config(cfg):
    try:
        with open(_config_path(), "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def default_name():
    try:
        return getpass.getuser() or "Mijn pc"
    except Exception:
        return "Mijn pc"


def default_download_dir():
    return os.path.join(os.path.expanduser("~"), "Downloads", "DraveLink")

# ----------------------------------------------------------------------------- taal
TRANSLATIONS = {
    "en": {
        "Groep": "Group", "Iedereen op het netwerk": "Everyone on the network",
        "Typ een bericht…": "Type a message…", "Versturen": "Send",
        "Bestand sturen…": "Send file…", "Online": "Online",
        "Niemand gevonden — wacht op apparaten…": "No one yet — waiting for devices…",
        "Snelgids": "Quick guide", "Sluiten": "Close", "Over": "About",
        "♥ Donatie": "♥ Donate", "Steun Dravenlock": "Support Dravenlock",
        "Donatie": "Donation", "Steun Dravenlock — bedankt!": "Support Dravenlock — thank you!",
        "Instellingen": "Settings", "Instellingen…": "Settings…",
        "Weergavenaam:": "Display name:", "Webpoort:": "Web port:",
        "Map voor ontvangen bestanden:": "Folder for received files:",
        "Map kiezen…": "Choose folder…", "Taal:": "Language:",
        "Automatisch (systeem)": "Automatic (system)", "Opslaan": "Save", "Annuleren": "Cancel",
        "Sommige instellingen gaan pas in na herstarten.": "Some settings take effect after a restart.",
        "Openen": "Open", "Map openen": "Open folder", "Downloaden": "Download",
        "Bestand ontvangen": "File received", "Kies een bestand om te sturen": "Choose a file to send",
        "Anderen doen mee via de browser:": "Others join via the browser:",
        "Kopieer link": "Copy link", "Gekopieerd!": "Copied!",
        "Webserver gestart op poort": "Web server started on port",
        "Open in browser": "Open in browser", "Activiteit": "Activity",
        "kwam binnen": "joined", "ging weg": "left", "deelde": "shared",
        "Map voor gedeelde bestanden:": "Folder for shared files:",
        "Kies je naam:": "Choose your name:", "Meedoen": "Join",
        "Toegangscode (voor toegang van buitenaf):": "Access code (for outside access):",
        "leeg = open (alleen veilig op je eigen netwerk)": "empty = open (only safe on your own network)",
        "🔒 Beveiligd met toegangscode": "🔒 Protected with access code",
        "⚠ Geen code — open voor iedereen die het adres kent": "⚠ No code — open to anyone who knows the address",
    }
}
_LANG = "nl"


def detect_lang(cfg):
    if cfg.get("lang") in ("nl", "en"):
        return cfg["lang"]
    env = (os.environ.get("LANG") or os.environ.get("LC_ALL")
           or os.environ.get("LANGUAGE") or "")
    if not env:
        try:
            import locale
            env = (locale.getdefaultlocale()[0] or "")
        except Exception:
            env = ""
    return "nl" if env.lower().startswith("nl") else ("en" if env else "nl")


def t(s, lang=None):
    lang = lang or _LANG
    if lang == "nl":
        return s
    return TRANSLATIONS.get(lang, {}).get(s, s)


def local_ips():
    ips = set()
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80)); ips.add(s.getsockname()[0]); s.close()
    except Exception:
        pass
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            ips.add(info[4][0])
    except Exception:
        pass
    ips.discard("127.0.0.1")
    return sorted(ips)


IMAGE_EXT = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg")


def is_image(name):
    return os.path.splitext(name)[1].lower() in IMAGE_EXT


def fmt_size(n):
    n = float(n)
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return ("%.0f %s" % (n, unit)) if unit == "B" else ("%.1f %s" % (n, unit))
        n /= 1024
    return "%.1f GB" % n

# ----------------------------------------------------------------------------- de hub (gedeelde kern)


class Hub:
    """Houdt deelnemers, berichten en gedeelde bestanden bij. Praat zowel met de
    pc-app (in-process) als met browsers (via de webserver)."""

    def __init__(self, share_dir):
        self.share_dir = share_dir
        self.participants = {}        # uuid -> {name,last,kind}
        self.messages = []            # [{seq,type,scope,frm,name,to,text,file,ts}]
        self.files = {}               # fid -> {name,size,path}
        self.seq = 0
        self.cond = threading.Condition()
        self.listeners = []           # callables(msg) voor de pc-app
        os.makedirs(self.share_dir, exist_ok=True)

    def add_listener(self, cb):
        self.listeners.append(cb)

    def join(self, uid, name, kind="web"):
        with self.cond:
            self.participants[uid] = {"name": name, "last": time.time(), "kind": kind}
            self.cond.notify_all()

    def touch(self, uid):
        with self.cond:
            if uid in self.participants:
                self.participants[uid]["last"] = time.time()

    def leave(self, uid):
        with self.cond:
            self.participants.pop(uid, None)
            self.cond.notify_all()

    def name_of(self, uid):
        with self.cond:
            p = self.participants.get(uid)
            return p["name"] if p else "?"

    def post(self, frm, scope, to, text=None, file=None):
        name = self.name_of(frm)
        with self.cond:
            self.seq += 1
            m = {"seq": self.seq, "type": "file" if file else "chat", "scope": scope,
                 "frm": frm, "name": name, "to": to, "text": text or "", "file": file,
                 "ts": time.time()}
            self.messages.append(m)
            if len(self.messages) > 1000:
                self.messages = self.messages[-1000:]
            self.cond.notify_all()
        for cb in list(self.listeners):
            try:
                cb(m)
            except Exception:
                pass
        return m

    def file_dest(self, name):
        fid = uuid.uuid4().hex
        dest = os.path.join(self.share_dir, fid + "_" + os.path.basename(name))
        return fid, dest

    def register_file(self, fid, name, path):
        size = os.path.getsize(path)
        self.files[fid] = {"name": os.path.basename(name), "size": size, "path": path}
        return size

    def get_file(self, fid):
        return self.files.get(fid)

    def peers(self):
        with self.cond:
            return [{"uuid": u, "name": p["name"]} for u, p in self.participants.items()]

    @staticmethod
    def _visible(m, uid):
        if m["scope"] == "group":
            return True
        return m["frm"] == uid or m["to"] == uid

    def events_since(self, uid, since, timeout=25.0):
        deadline = time.time() + timeout
        with self.cond:
            while True:
                evs = [m for m in self.messages if m["seq"] > since and self._visible(m, uid)]
                if evs or time.time() >= deadline:
                    peers = [{"uuid": u, "name": p["name"]} for u, p in self.participants.items()]
                    return evs, self.seq, peers
                self.cond.wait(timeout=max(0.1, deadline - time.time()))

    def prune_loop(self, running_flag):
        while running_flag():
            time.sleep(2.0)
            now = time.time(); gone = False
            with self.cond:
                for u in list(self.participants):
                    p = self.participants[u]
                    if p["kind"] != "app" and now - p["last"] > PEER_TIMEOUT:
                        del self.participants[u]; gone = True
                if gone:
                    self.cond.notify_all()

# ----------------------------------------------------------------------------- webclient (browser)
WEB_HTML = r"""<!doctype html><html lang="nl"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{{APP}}</title>
<style>
 :root{--bg:{{BG}};--panel:{{PANEL}};--panel2:{{PANEL2}};--silver:{{SILVER}};--accent:{{ACCENT}};--mute:{{MUTE}};}
 *{box-sizing:border-box;font-family:system-ui,Segoe UI,Roboto,Arial,sans-serif;}
 html,body{margin:0;height:100%;background:var(--bg);color:var(--silver);}
 #app{display:none;height:100%;grid-template-rows:auto 1fr auto;}
 header{display:flex;align-items:center;gap:10px;padding:12px 14px;background:var(--panel);border-bottom:1px solid #20202a;}
 header .logo{width:26px;height:26px;border-radius:6px;background:var(--accent);}
 header b{font-size:18px;}
 #wrap{display:flex;min-height:0;}
 #side{width:38%;max-width:280px;background:var(--panel2);border-right:1px solid #20202a;overflow:auto;padding:8px;}
 .pitem{padding:11px 12px;border-radius:9px;cursor:pointer;margin-bottom:4px;}
 .pitem:hover{background:#16161d;} .pitem.sel{background:var(--accent);color:#07121d;}
 #main{flex:1;display:flex;flex-direction:column;min-width:0;}
 #title{padding:10px 14px;font-weight:600;border-bottom:1px solid #20202a;}
 #log{flex:1;overflow:auto;padding:12px;}
 .msg{margin:8px 0;} .msg .who{font-weight:700;} .msg.me{text-align:right;} .msg.me .who{color:var(--accent);}
 .msg .tm{color:var(--mute);font-size:12px;margin-left:6px;}
 .bubble{display:inline-block;background:#16161d;padding:8px 11px;border-radius:12px;max-width:80%;
         word-break:break-word;white-space:pre-wrap;margin-top:3px;}
 .msg.me .bubble{background:#1d2a38;}
 a{color:var(--accent);}
 #bar{display:flex;gap:8px;padding:10px;border-top:1px solid #20202a;background:var(--panel);}
 #txt{flex:1;background:var(--panel2);border:1px solid #2a2a36;border-radius:10px;padding:11px;color:var(--silver);font-size:16px;}
 button{background:#1b1b22;border:1px solid #2a2a36;border-radius:10px;padding:11px 14px;color:var(--silver);font-size:15px;cursor:pointer;}
 button.cta{background:var(--accent);color:#07121d;border:none;font-weight:700;}
 #join{position:fixed;inset:0;display:flex;align-items:center;justify-content:center;background:var(--bg);}
 #joinbox{background:var(--panel);border:1px solid #20202a;border-radius:16px;padding:24px;width:min(92vw,360px);text-align:center;}
 #joinbox h1{margin:0 0 4px;font-size:22px;} #joinbox p{color:var(--mute);margin:0 0 16px;}
 #nm{width:100%;background:var(--panel2);border:1px solid #2a2a36;border-radius:10px;padding:12px;color:var(--silver);font-size:16px;margin-bottom:12px;}
</style></head><body>
<div id="join"><div id="joinbox">
  <h1>{{APP}}</h1><p>Kies een naam om mee te doen</p>
  <input id="nm" placeholder="Jouw naam" autofocus>
  <button class="cta" style="width:100%" onclick="doJoin()">Meedoen</button>
</div></div>
<div id="app">
  <header><div class="logo"></div><b>{{APP}}</b></header>
  <div id="wrap">
    <div id="side"></div>
    <div id="main">
      <div id="title">Groep</div>
      <div id="log"></div>
      <div id="bar">
        <input id="txt" placeholder="Typ een bericht…" onkeydown="if(event.key==='Enter')send()">
        <button onclick="pickFile()">📎</button>
        <button class="cta" onclick="send()">Versturen</button>
        <input id="file" type="file" style="display:none" onchange="upload()">
      </div>
    </div>
  </div>
</div>
<script>
var SID=null, NAME=null, since=0, target="group", peers=[], byKey={group:[]};
function esc(s){var d=document.createElement('div');d.textContent=s;return d.innerHTML;}
function keyFor(m){ if(m.scope==='group')return 'group'; return (m.frm===SID)?m.to:m.frm; }
function doJoin(){
  var n=document.getElementById('nm').value.trim(); if(!n)return;
  fetch('/api/join',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:n})})
   .then(r=>r.json()).then(d=>{ SID=d.sid; NAME=n;
     document.getElementById('join').style.display='none';
     document.getElementById('app').style.display='grid';
     document.getElementById('app').style.height='100%';
     poll(); });
}
function renderPeers(){
  var s=document.getElementById('side'); s.innerHTML='';
  var g=document.createElement('div'); g.className='pitem'+(target==='group'?' sel':'');
  g.textContent='👥  Groep'; g.onclick=function(){target='group';draw();renderPeers();}; s.appendChild(g);
  peers.forEach(function(p){ if(p.uuid===SID)return;
    var d=document.createElement('div'); d.className='pitem'+(target===p.uuid?' sel':'');
    d.textContent='🟢  '+p.name; d.onclick=function(){target=p.uuid;draw();renderPeers();}; s.appendChild(d); });
}
function nameOf(uid){ for(var i=0;i<peers.length;i++)if(peers[i].uuid===uid)return peers[i].name; return '?'; }
function draw(){
  var titleEl=document.getElementById('title');
  titleEl.textContent = target==='group' ? '👥  Groep — iedereen' : ('💬  '+nameOf(target));
  var log=document.getElementById('log'); log.innerHTML='';
  (byKey[target]||[]).forEach(function(m){
    var me=(m.frm===SID); var div=document.createElement('div'); div.className='msg'+(me?' me':'');
    var tm=new Date(m.ts*1000).toTimeString().slice(0,5);
    var head='<span class="who">'+esc(me?'Ik':m.name)+'</span><span class="tm">'+tm+'</span>';
    var body;
    if(m.file){
      var url='/api/file/'+m.file.id;
      if(/\.(png|jpe?g|gif|webp|bmp|svg)$/i.test(m.file.name)){
        body='<div class="bubble"><a href="'+url+'" target="_blank">'
          +'<img src="'+url+'" style="max-width:240px;max-height:240px;border-radius:8px;display:block"></a>'
          +'<div class="tm">'+esc(m.file.name)+' · '+fmtSize(m.file.size)
          +' · <a href="'+url+'" download>Downloaden</a></div></div>';
      } else {
        body='<div class="bubble">📎 '+esc(m.file.name)+' <span class="tm">'+fmtSize(m.file.size)
          +'</span><br><a href="'+url+'" download>Downloaden</a></div>';
      }
    }
    else { body='<div class="bubble">'+esc(m.text)+'</div>'; }
    div.innerHTML=head+'<br>'+body; log.appendChild(div);
  });
  log.scrollTop=log.scrollHeight;
}
function fmtSize(n){var u=['B','KB','MB','GB'],i=0;n=Number(n);while(n>=1024&&i<3){n/=1024;i++;}return (i===0?n.toFixed(0):n.toFixed(1))+' '+u[i];}
function poll(){
  fetch('/api/events?sid='+SID+'&since='+since).then(r=>r.json()).then(d=>{
    peers=d.peers; 
    d.events.forEach(function(m){ var k=keyFor(m); (byKey[k]=byKey[k]||[]).push(m); });
    if(d.events.length){ since=d.seq; draw(); }
    renderPeers();
    poll();
  }).catch(function(){ setTimeout(poll,1500); });
}
function send(){
  var el=document.getElementById('txt'); var v=el.value.trim(); if(!v)return; el.value='';
  var scope = target==='group'?'group':'private';
  fetch('/api/send',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({sid:SID,scope:scope,to:target,text:v})});
}
function pickFile(){ document.getElementById('file').click(); }
function upload(){
  var f=document.getElementById('file').files[0]; if(!f)return;
  var scope=target==='group'?'group':'private';
  fetch('/api/upload?sid='+SID+'&scope='+scope+'&to='+encodeURIComponent(target)+'&name='+encodeURIComponent(f.name),
    {method:'POST',body:f}).then(function(){ document.getElementById('file').value=''; });
}
window.addEventListener('beforeunload',function(){ if(SID)navigator.sendBeacon('/api/leave?sid='+SID); });
</script></body></html>"""


def build_web_html():
    h = WEB_HTML
    for k, v in (("{{APP}}", APP_NAME), ("{{BG}}", BG), ("{{PANEL}}", PANEL),
                 ("{{PANEL2}}", PANEL2), ("{{SILVER}}", SILVER), ("{{ACCENT}}", ACCENT),
                 ("{{MUTE}}", MUTE)):
        h = h.replace(k, v)
    return h

# ----------------------------------------------------------------------------- webserver


class HttpHub:
    def __init__(self, hub, port, access_code=""):
        self.hub = hub
        self.port = port
        self.access_code = access_code or ""
        self.httpd = None
        self.web_html = build_web_html()

    def start(self):
        hub = self.hub
        web_html = self.web_html
        last_err = None
        for p in range(self.port, self.port + 12):
            try:
                handler = self._make_handler(hub, web_html, self.access_code)
                httpd = ThreadingHTTPServer(("0.0.0.0", p), handler)
                self.httpd = httpd; self.port = p
                break
            except Exception as e:
                last_err = e; continue
        if not self.httpd:
            raise RuntimeError("Geen poort vrij: %s" % last_err)
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
        return self.port

    def stop(self):
        try:
            if self.httpd:
                self.httpd.shutdown()
        except Exception:
            pass

    @staticmethod
    def _make_handler(hub, web_html, access_code=""):
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def _auth_ok(self):
                if not access_code:
                    return True
                hdr = self.headers.get("Authorization", "")
                if hdr.startswith("Basic "):
                    try:
                        raw = base64.b64decode(hdr[6:]).decode("utf-8", "replace")
                        _, _, pw = raw.partition(":")
                        if pw == access_code:
                            return True
                    except Exception:
                        pass
                return False

            def _ask_auth(self):
                self.send_response(401)
                self.send_header("WWW-Authenticate", 'Basic realm="DraveLink"')
                self.send_header("Content-Length", "0")
                self.end_headers()

            def _json(self, obj, code=200):
                body = json.dumps(obj).encode("utf-8")
                self.send_response(code)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(body)

            def _qs(self):
                return urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)

            def _body(self):
                n = int(self.headers.get("Content-Length", 0) or 0)
                return self.rfile.read(n) if n else b""

            def do_GET(self):
                if not self._auth_ok():
                    self._ask_auth(); return
                path = urllib.parse.urlparse(self.path).path
                if path in ("/", "/index.html"):
                    body = web_html.encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers(); self.wfile.write(body); return
                if path == "/api/events":
                    q = self._qs()
                    sid = q.get("sid", [""])[0]; since = int(q.get("since", ["0"])[0])
                    hub.touch(sid)
                    evs, seq, peers = hub.events_since(sid, since)
                    self._json({"events": evs, "seq": seq, "peers": peers}); return
                if path.startswith("/api/file/"):
                    fid = path.rsplit("/", 1)[-1]
                    info = hub.get_file(fid)
                    if not info or not os.path.exists(info["path"]):
                        self._json({"error": "not found"}, 404); return
                    ctype = mimetypes.guess_type(info["name"])[0] or "application/octet-stream"
                    self.send_response(200)
                    self.send_header("Content-Type", ctype)
                    self.send_header("Content-Length", str(info["size"]))
                    self.send_header("Content-Disposition",
                                     'attachment; filename="%s"' % info["name"])
                    self.end_headers()
                    with open(info["path"], "rb") as f:
                        shutil.copyfileobj(f, self.wfile)
                    return
                self._json({"error": "not found"}, 404)

            def do_POST(self):
                if not self._auth_ok():
                    self._ask_auth(); return
                path = urllib.parse.urlparse(self.path).path
                if path == "/api/join":
                    data = json.loads(self._body().decode("utf-8") or "{}")
                    uid = uuid.uuid4().hex
                    hub.join(uid, (data.get("name") or "Gast").strip()[:40], "web")
                    self._json({"sid": uid}); return
                if path == "/api/send":
                    data = json.loads(self._body().decode("utf-8") or "{}")
                    sid = data.get("sid", "")
                    if sid in [p["uuid"] for p in hub.peers()]:
                        hub.post(sid, data.get("scope", "group"), data.get("to", ""),
                                 text=(data.get("text") or "")[:4000])
                    self._json({"ok": True}); return
                if path == "/api/upload":
                    q = self._qs()
                    sid = q.get("sid", [""])[0]; scope = q.get("scope", ["group"])[0]
                    to = q.get("to", [""])[0]; name = q.get("name", ["bestand"])[0]
                    fid, dest = hub.file_dest(name)
                    n = int(self.headers.get("Content-Length", 0) or 0)
                    remaining = n
                    with open(dest, "wb") as f:
                        while remaining > 0:
                            chunk = self.rfile.read(min(65536, remaining))
                            if not chunk:
                                break
                            f.write(chunk); remaining -= len(chunk)
                    size = hub.register_file(fid, name, dest)
                    hub.post(sid, scope, to, file={"id": fid, "name": os.path.basename(name), "size": size})
                    self._json({"ok": True, "id": fid}); return
                if path == "/api/leave":
                    q = self._qs(); hub.leave(q.get("sid", [""])[0]); self._json({"ok": True}); return
                self._json({"error": "not found"}, 404)
        return Handler

# ----------------------------------------------------------------------------- uiterlijk


def make_logo(size=34):
    pm = QPixmap(size, size); pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm); p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(QBrush(QColor(ACCENT))); p.setPen(Qt.PenStyle.NoPen)
    r = size * 0.16; p.drawRoundedRect(1, 1, size - 2, size - 2, r, r)
    p.setBrush(QBrush(QColor(PANEL2)))
    n = size * 0.16
    a = (size * 0.30, size * 0.34); b = (size * 0.70, size * 0.66)
    p.setPen(QPen(QColor(PANEL2), max(2, size * 0.06)))
    p.drawLine(int(a[0]), int(a[1]), int(b[0]), int(b[1]))
    p.setPen(Qt.PenStyle.NoPen)
    for (cx, cy) in (a, b):
        p.drawEllipse(int(cx - n), int(cy - n), int(n * 2), int(n * 2))
    p.end(); return pm


def app_icon():
    return QIcon(make_logo(64))


QSS = """
* { font-size: 15px; color: %(silver)s; }
QMainWindow, QWidget { background: %(bg)s; }
#header { background: %(panel)s; border-bottom: 1px solid #20202a; }
#title { font-size: 20px; font-weight: 700; color: %(silver)s; }
#ver { color: %(mute)s; }
#info { background: %(panel)s; color: %(mute)s; border-bottom: 1px solid #20202a; }
#info b { color: %(silver)s; }
QListWidget { background: %(panel2)s; border: 1px solid #20202a; border-radius: 10px; padding: 6px; }
QListWidget::item { padding: 9px 10px; border-radius: 8px; }
QListWidget::item:selected { background: %(accent)s; color: #07121d; }
QTextBrowser { background: %(panel2)s; border: 1px solid #20202a; border-radius: 10px; padding: 8px; }
QLineEdit, QSpinBox, QComboBox { background: %(panel2)s; border: 1px solid #2a2a36;
        border-radius: 8px; padding: 7px 9px; color: %(silver)s; }
QPushButton { background: #1b1b22; border: 1px solid #2a2a36; border-radius: 9px; padding: 8px 14px; color: %(silver)s; }
QPushButton:hover { border-color: %(accent)s; }
QPushButton#cta { background: %(accent)s; color: #07121d; border: none; font-weight: 700; }
QPushButton#cta:hover { background: #84b4e2; }
QLabel#hint { color: %(mute)s; }
QStatusBar { background: %(panel)s; color: %(mute)s; border-top: 1px solid #20202a; }
""" % {"bg": BG, "panel": PANEL, "panel2": PANEL2, "silver": SILVER, "accent": ACCENT, "mute": MUTE}


# ----------------------------------------------------------------------------- snelgids
def guide_html(lang="nl"):
    if lang == "en":
        return ("""
<h1>DraveLink — Quick guide</h1>
<p>DraveLink lets devices on the same network <b>chat</b> and <b>share files</b> — no internet,
no cloud. One PC runs DraveLink as the <b>server</b>; everyone (including you) joins via the
<b>browser</b> with a chosen name.</p>
<h2>How it works</h2>
<ul>
<li>Start DraveLink on one PC. At the top it shows a web address like <code>http://192.168.1.50:8080/</code>.
The app itself is only the server: it shows the address and who is connected.</li>
<li>Want to <b>chat yourself</b>? On the PC click <b>Open in browser</b>.</li>
<li>Open the same address on any phone, tablet or PC on the <b>same Wi-Fi</b> and pick a name.</li>
<li>You can also test it alone: open the address in two browser tabs with different names.</li>
</ul>
<h2>Chat &amp; files</h2>
<p>Click <b>Group</b> for everyone, or a name for a private (1-on-1) chat. Use 📎 to send a file —
it is shared directly from the hub PC and others download it with one click.</p>
<h2>Good to know</h2>
<ul>
<li>Everything stays on your local network.</li>
<li>The hub PC must stay on while others are connected.</li>
<li>If others can't reach it: allow DraveLink through the firewall and set your network to <b>Private</b>.</li>
</ul>
<p style="color:%s">Made with care by Dravenlock — %s.</p>
""" % (MUTE, CONTACT))
    return ("""
<h1>DraveLink — Snelgids</h1>
<p>Met DraveLink kunnen apparaten op hetzelfde netwerk <b>chatten</b> en <b>bestanden delen</b> —
geen internet, geen cloud. Eén pc draait DraveLink als <b>server</b>; iedereen (ook jij) doet mee
via de <b>browser</b> met een gekozen naam.</p>
<h2>Hoe het werkt</h2>
<ul>
<li>Start DraveLink op één pc. Bovenin zie je een webadres zoals <code>http://192.168.1.50:8080/</code>.
De app zelf is alleen de server: hij toont het adres en wie er verbonden is.</li>
<li>Wil je <b>zelf meechatten</b>? Klik op de pc op <b>Open in browser</b>.</li>
<li>Open hetzelfde adres op een telefoon, tablet of pc op <b>hetzelfde wifi</b> in de browser, en
kies een naam.</li>
<li>Je kunt het ook alleen testen: open het adres in twee browsertabbladen met verschillende namen.</li>
</ul>
<h2>Chatten &amp; bestanden</h2>
<p>Klik op <b>Groep</b> voor iedereen, of op een naam voor een privégesprek (1-op-1). Gebruik 📎 om
een bestand te sturen — het wordt rechtstreeks vanaf de hub-pc gedeeld en anderen downloaden het met
één klik.</p>
<h2>Goed om te weten</h2>
<ul>
<li>Alles blijft op je eigen netwerk.</li>
<li>De hub-pc moet aan blijven zolang anderen verbonden zijn.</li>
<li>Kunnen anderen er niet bij? Sta DraveLink toe in de firewall en zet je netwerk op <b>Privé</b>.</li>
</ul>
<p style="color:%s">Met zorg gemaakt door Dravenlock — %s.</p>
""" % (MUTE, CONTACT))


class QuickGuideDialog(QDialog):
    def __init__(self, parent, lang="nl"):
        super().__init__(parent)
        self.setWindowTitle(t("Snelgids", lang)); self.resize(700, 620)
        lay = QVBoxLayout(self); lay.setContentsMargins(16, 16, 16, 16); lay.setSpacing(12)
        view = QTextBrowser(); view.setOpenExternalLinks(True)
        view.setStyleSheet("QTextBrowser{background:%s;color:%s;border:1px solid #20202a;"
                           "border-radius:10px;font-size:16px;padding:8px;}" % (PANEL2, SILVER))
        view.setHtml(guide_html(lang)); lay.addWidget(view, 1)
        row = QHBoxLayout(); row.addStretch(1)
        b = QPushButton(t("Sluiten", lang)); b.clicked.connect(self.accept); row.addWidget(b)
        lay.addLayout(row)


class SettingsDialog(QDialog):
    def __init__(self, parent, cfg, lang="nl"):
        super().__init__(parent)
        self.cfg = cfg; self.lang = lang
        self.setWindowTitle(t("Instellingen", lang)); self.resize(560, 300)
        lay = QVBoxLayout(self); lay.setContentsMargins(16, 16, 16, 16); lay.setSpacing(10)
        lay.addWidget(QLabel(t("Webpoort:", lang)))
        self.port = QSpinBox(); self.port.setRange(1024, 65535)
        self.port.setValue(int(cfg.get("web_port") or WEB_PORT)); lay.addWidget(self.port)
        lay.addWidget(QLabel(t("Map voor gedeelde bestanden:", lang)))
        drow = QHBoxLayout()
        self.dl = QLineEdit(cfg.get("share_dir") or os.path.join(_app_dir(), "_dravelink_share"))
        drow.addWidget(self.dl, 1)
        pick = QPushButton(t("Map kiezen…", lang)); pick.clicked.connect(self._pick); drow.addWidget(pick)
        lay.addLayout(drow)
        lay.addWidget(QLabel(t("Taal:", lang)))
        self.langbox = QComboBox()
        self.langbox.addItem(t("Automatisch (systeem)", lang), "")
        self.langbox.addItem("Nederlands", "nl"); self.langbox.addItem("English", "en")
        self.langbox.setCurrentIndex({"": 0, "nl": 1, "en": 2}.get(cfg.get("lang", ""), 0))
        lay.addWidget(self.langbox)
        lay.addWidget(QLabel(t("Toegangscode (voor toegang van buitenaf):", lang)))
        self.code = QLineEdit(cfg.get("access_code", ""))
        self.code.setPlaceholderText(t("leeg = open (alleen veilig op je eigen netwerk)", lang))
        lay.addWidget(self.code)
        note = QLabel(t("Sommige instellingen gaan pas in na herstarten.", lang))
        note.setObjectName("hint"); note.setWordWrap(True); lay.addWidget(note)
        lay.addStretch(1)
        row = QHBoxLayout(); row.addStretch(1)
        cancel = QPushButton(t("Annuleren", lang)); cancel.clicked.connect(self.reject)
        ok = QPushButton(t("Opslaan", lang)); ok.setObjectName("cta"); ok.clicked.connect(self.accept)
        row.addWidget(cancel); row.addWidget(ok); lay.addLayout(row)

    def _pick(self):
        d = QFileDialog.getExistingDirectory(self, t("Map kiezen…", self.lang), self.dl.text())
        if d:
            self.dl.setText(d)

    def result_cfg(self):
        self.cfg["web_port"] = int(self.port.value())
        self.cfg["share_dir"] = self.dl.text().strip()
        self.cfg["lang"] = self.langbox.currentData()
        self.cfg["access_code"] = self.code.text().strip()
        return self.cfg


# ----------------------------------------------------------------------------- serverconsole
class DraveLink(QMainWindow):
    """De pc-app is ALLEEN de server: toont het webadres en wie er verbonden is.
    Iedereen chat via de browser (clients). Open de browser ook zelf om mee te doen."""
    hub_msg = pyqtSignal(dict)

    def __init__(self, cfg):
        super().__init__()
        self.cfg = cfg; self.lang = _LANG
        self.setWindowTitle("%s — server" % APP_NAME); self.setWindowIcon(app_icon())
        self.resize(960, 640)

        share = cfg.get("share_dir") or os.path.join(_app_dir(), "_dravelink_share")
        self.hub = Hub(share)
        self.web_port = int(cfg.get("web_port") or WEB_PORT)
        self.http = HttpHub(self.hub, self.web_port, cfg.get('access_code', ''))
        self._running = True
        self._urls = []
        self._known = set()
        self._names = {}
        self._log = []

        root = QWidget(); self.setCentralWidget(root)
        outer = QVBoxLayout(root); outer.setContentsMargins(0, 0, 0, 0); outer.setSpacing(0)
        outer.addWidget(self._header())

        # groot adresvlak
        addr = QWidget(); addr.setObjectName("info")
        al = QHBoxLayout(addr); al.setContentsMargins(14, 12, 14, 12); al.setSpacing(10)
        self.info = QLabel(" "); self.info.setTextFormat(Qt.TextFormat.RichText)
        self.info.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        al.addWidget(self.info, 1)
        openb = QPushButton(t("Open in browser")); openb.setObjectName("cta")
        openb.clicked.connect(self._open_browser); al.addWidget(openb)
        copyb = QPushButton(t("Kopieer link")); copyb.clicked.connect(self._copy_link); al.addWidget(copyb)
        outer.addWidget(addr)

        body = QWidget(); outer.addWidget(body, 1)
        bl = QHBoxLayout(body); bl.setContentsMargins(12, 12, 12, 12); bl.setSpacing(12)
        left = QVBoxLayout(); left.setSpacing(8)
        self.onlinelbl = QLabel(t("Online") + " (0)")
        left.addWidget(self.onlinelbl)
        self.peerlist = QListWidget(); left.addWidget(self.peerlist, 1)
        self.empty = QLabel(t("Niemand gevonden — wacht op apparaten…"))
        self.empty.setObjectName("hint"); self.empty.setWordWrap(True); left.addWidget(self.empty)
        lwrap = QWidget(); lwrap.setLayout(left); lwrap.setFixedWidth(260); bl.addWidget(lwrap)

        right = QVBoxLayout(); right.setSpacing(8)
        right.addWidget(QLabel(t("Activiteit")))
        self.view = QTextBrowser(); self.view.setOpenExternalLinks(False)
        self.view.anchorClicked.connect(self._on_anchor); right.addWidget(self.view, 1)
        rwrap = QWidget(); rwrap.setLayout(right); bl.addWidget(rwrap, 1)

        sb = QStatusBar(); self.setStatusBar(sb); sb.showMessage("%s v%s" % (APP_NAME, APP_VERSION))
        donate = QPushButton(t("♥ Donatie")); donate.setObjectName("cta")
        donate.setToolTip(t("Steun Dravenlock")); donate.clicked.connect(self._donate)
        sb.addPermanentWidget(donate)

        self.hub_msg.connect(self._log_msg)
        self.hub.add_listener(lambda m: self.hub_msg.emit(m))
        threading.Thread(target=self.hub.prune_loop, args=(lambda: self._running,), daemon=True).start()
        try:
            port = self.http.start(); self.web_port = port; self._show_info(port)
            self._add_log("<span style='color:%s'>%s %d</span>"
                          % (MUTE, t("Webserver gestart op poort"), port))
        except Exception as e:
            self.info.setText("Webserver kon niet starten: %s" % e)

        self._refresh_peers()
        self._timer = QTimer(self); self._timer.timeout.connect(self._refresh_peers); self._timer.start(2000)

    def _show_info(self, port):
        ips = local_ips() or ["127.0.0.1"]
        self._urls = ["http://%s:%d/" % (ip, port) for ip in ips]
        urls = "   ".join(self._urls)
        if self.http.access_code:
            badge = "&nbsp;&nbsp;<span style='color:%s'>%s</span>" % (
                ACCENT, t("🔒 Beveiligd met toegangscode"))
        else:
            badge = "&nbsp;&nbsp;<span style='color:#e0a23a'>%s</span>" % (
                t("⚠ Geen code — open voor iedereen die het adres kent"))
        self.info.setText("%s  <b>%s</b>%s"
                          % (t("Anderen doen mee via de browser:"), urls, badge))

    def _header(self):
        w = QWidget(); w.setObjectName("header"); w.setFixedHeight(58)
        lay = QHBoxLayout(w); lay.setContentsMargins(14, 8, 14, 8)
        logo = QLabel(); logo.setPixmap(make_logo(34)); lay.addWidget(logo)
        title = QLabel(APP_NAME); title.setObjectName("title"); lay.addWidget(title)
        ver = QLabel("v" + APP_VERSION); ver.setObjectName("ver"); lay.addWidget(ver)
        lay.addStretch(1)
        sett = QPushButton(t("Instellingen…")); sett.clicked.connect(self._settings); lay.addWidget(sett)
        guide = QPushButton(t("Snelgids")); guide.clicked.connect(self._guide); lay.addWidget(guide)
        about = QPushButton(t("Over")); about.clicked.connect(self._about); lay.addWidget(about)
        return w

    def _open_browser(self):
        QDesktopServices.openUrl(QUrl("http://127.0.0.1:%d/" % self.web_port))

    def _copy_link(self):
        if self._urls:
            QApplication.clipboard().setText(self._urls[0])
            self.statusBar().showMessage(t("Gekopieerd!") + " " + self._urls[0], 4000)

    def _refresh_peers(self):
        peers = self.hub.peers()
        cur = set(p["uuid"] for p in peers)
        for p in peers:
            self._names[p["uuid"]] = p["name"]
        for u in cur - self._known:
            self._add_log("<span style='color:%s'>🟢 %s %s</span>"
                          % (ACCENT, _html.escape(self._names.get(u, "?")), t("kwam binnen")))
        for u in self._known - cur:
            self._add_log("<span style='color:%s'>⚪ %s %s</span>"
                          % (MUTE, _html.escape(self._names.get(u, "?")), t("ging weg")))
        self._known = cur
        self.peerlist.clear()
        for p in sorted(peers, key=lambda x: x["name"].lower()):
            self.peerlist.addItem(QListWidgetItem("🟢  " + p["name"]))
        self.onlinelbl.setText(t("Online") + " (%d)" % len(peers))
        self.empty.setVisible(len(peers) == 0)

    def _log_msg(self, m):
        ts = time.strftime("%H:%M", time.localtime(m.get("ts", time.time())))
        name = _html.escape(m.get("name", "?"))
        if m.get("scope") != "group":
            return  # privé blijft privé; niet in de serverlog
        if m.get("file"):
            fi = m["file"]; info = self.hub.get_file(fi["id"])
            links = ""
            if info:
                links = ("&nbsp; <a href='open:%s' style='color:%s'>%s</a> &nbsp;"
                         "<a href='folder:%s' style='color:%s'>%s</a>"
                         % (info["path"], ACCENT, t("Openen"),
                            os.path.dirname(info["path"]), ACCENT, t("Map openen")))
            line = ("<b>%s</b> %s 📎 %s <span style='color:%s'>(%s)</span>%s"
                    % (name, t("deelde"), _html.escape(fi["name"]), MUTE,
                       fmt_size(fi.get("size", 0)), links))
        else:
            line = "<b>%s:</b> %s" % (name, _html.escape(m.get("text", "")))
        self._add_log("<span style='color:%s'>%s</span> %s" % (MUTE, ts, line))

    def _add_log(self, html_line):
        self._log.append(html_line)
        if len(self._log) > 400:
            self._log = self._log[-400:]
        self.view.setHtml("<div style='font-size:15px;line-height:1.5'>"
                          + "<br>".join(self._log) + "</div>")
        self.view.verticalScrollBar().setValue(self.view.verticalScrollBar().maximum())

    def _on_anchor(self, url):
        s = url.toString()
        if s.startswith("open:"):
            QDesktopServices.openUrl(QUrl.fromLocalFile(s[5:]))
        elif s.startswith("folder:"):
            QDesktopServices.openUrl(QUrl.fromLocalFile(s[7:]))

    def _settings(self):
        dlg = SettingsDialog(self, dict(self.cfg), self.lang)
        if dlg.exec():
            self.cfg = dlg.result_cfg(); save_config(self.cfg)
            self.statusBar().showMessage(t("Sommige instellingen gaan pas in na herstarten."), 5000)

    def _guide(self):
        QuickGuideDialog(self, self.lang).exec()

    def _about(self):
        QMessageBox.information(self, t("Over"), "%s v%s\nDravenlock\n%s" % (APP_NAME, APP_VERSION, CONTACT))

    def _donate(self):
        if not QDesktopServices.openUrl(QUrl(DONATE_URL)):
            QMessageBox.information(self, t("Donatie"), t("Steun Dravenlock — bedankt!") + "\n" + DONATE_URL)

    def closeEvent(self, e):
        self._running = False
        try:
            self.http.stop()
        except Exception:
            pass
        super().closeEvent(e)

def main():
    global _LANG
    cfg = load_config(); _LANG = detect_lang(cfg); save_config(cfg)
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_DontShowIconsInMenus, True)
    app = QApplication(sys.argv); app.setApplicationName(APP_NAME)
    app.setWindowIcon(app_icon()); app.setStyleSheet(QSS)
    win = DraveLink(cfg); win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
