/**
 * Cv'ne Bakalım! masaüstü uygulaması (T-059): web arayüzünün derlenmiş hâlini (web/dist) bir pencerede açar.
 *
 * Sayfalar file:// yerine özel bir adresten (app://careerai) sunulur. Böylece React Router'ın tarayıcı geçmişi
 * çalışır, localStorage kalıcı bir kökene bağlı kalır ve CSP gibi başlıklar eklenebilir.
 * Güvenlik (Electron güvenlik kontrol listesi): contextIsolation açık, nodeIntegration kapalı, sandbox açık;
 * sayfaya Node erişimi verilmez (preload yok). Uygulama dışındaki adresler sistem tarayıcısında açılır.
 * Paketli uygulamada Node'u açan yollar (ELECTRON_RUN_AS_NODE, NODE_OPTIONS, --inspect) Fuses ile kapalıdır.
 *
 *   npm start                 → web/dist'i açar (önce: npm run web)
 *   npm start -- --smoke      → açılır, sayfayı kontrol eder, sonucu yazıp kapanır (CI/elle doğrulama)
 *   CAREERAI_DEV_URL=http://127.0.0.1:5173 npm start   → Vite geliştirme sunucusunu açar (sadece paketsizken)
 */
const { app, BrowserWindow, net, protocol, session, shell } = require("electron");
const crypto = require("node:crypto");
const fs = require("node:fs");
const path = require("node:path");
const { pathToFileURL } = require("node:url");

const SCHEME = "app";
const HOST = "careerai";
const APP_ORIGIN = `${SCHEME}://${HOST}`;
// Paketli uygulama ortam değişkeniyle başka bir siteyi "uygulama" diye açmasın.
const DEV_URL = app.isPackaged ? undefined : process.env.CAREERAI_DEV_URL;
const SMOKE = process.argv.includes("--smoke");
// Paketlenmiş uygulamada web/dist, kaynak klasörüne "web" adıyla kopyalanır (package.json → build.extraResources).
// Kullanıcı verisi klasörü (oturum, localStorage, tek pencere kilidi) eski adla sabit: Electron bunu productName'den
// türetir ve ad "Cv'ne Bakalım!" olunca (karar #34) kurulu uygulamalar oturumunu kaybederdi. Teknik ad değişmez.
app.setPath("userData", path.join(app.getPath("appData"), "CareerAI"));

const DIST = app.isPackaged ? path.join(process.resourcesPath, "web") : path.join(__dirname, "..", "dist");
const INDEX = path.join(DIST, "index.html");

protocol.registerSchemesAsPrivileged([
  { scheme: SCHEME, privileges: { standard: true, secure: true, supportFetchAPI: true } },
]);

/** index.html'deki satır içi betiklerin (tema) özetleri: CSP 'unsafe-inline' olmadan bunlara izin verir. */
function inlineScriptHashes(html) {
  return [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(
    // HTML ayrıştırıcısı CRLF'yi LF'ye çevirir; özet de öyle hesaplanmalı (Windows'ta dosya CRLF olabilir).
    (m) => `'sha256-${crypto.createHash("sha256").update(m[1].replace(/\r\n?/g, "\n")).digest("base64")}'`,
  );
}

function contentSecurityPolicy(html) {
  // API adresi derlemeye gömülü (VITE_API_URL); üretimde HTTPS. Geliştirmede yerel backend.
  const connect = app.isPackaged ? "'self' https:" : "'self' https: http://127.0.0.1:*";
  return [
    "default-src 'self'",
    `script-src 'self' ${inlineScriptHashes(html).join(" ")}`,
    "style-src 'self' 'unsafe-inline'", // React'in style özelliği (tasarım sayfası)
    "img-src 'self' data:",
    "font-src 'self'",
    `connect-src ${connect}`,
    "form-action 'self'",
    "object-src 'none'",
    "base-uri 'none'",
    "frame-ancestors 'none'",
  ].join("; ");
}

let csp; // index.html değişmez: bir kez hesaplanır

/**
 * Dosyayı web/dist içinden sunar; bilinmeyen yol tek sayfalık uygulamanın index.html'idir (React Router).
 * CSP her yanıta eklenir: Windows'ta "INDEX.HTML", "index.html." gibi yollar da aynı dosyayı açar ve CSP'siz kalmamalı.
 */
async function serve(request) {
  const url = new URL(request.url);
  if (url.host !== HOST) return new Response(null, { status: 404 });
  csp ??= contentSecurityPolicy(fs.readFileSync(INDEX, "utf8"));
  let file;
  try {
    file = path.normalize(path.join(DIST, decodeURIComponent(url.pathname)));
    // "../" ile web/dist dışına çıkılamaz; klasör veya olmayan dosya index.html'e düşer.
    if (!file.startsWith(DIST + path.sep) || !fs.statSync(file, { throwIfNoEntry: false })?.isFile()) file = INDEX;
  } catch {
    return new Response(null, { status: 400 }); // bozuk yüzde kodlaması, %00 vb.
  }
  const response = await net.fetch(pathToFileURL(file).toString());
  const headers = new Headers(response.headers);
  headers.set("content-security-policy", csp);
  if (file === INDEX) headers.set("content-type", "text/html; charset=utf-8");
  return new Response(response.body, { status: response.status, headers });
}

function isAppUrl(raw) {
  try {
    const url = new URL(raw);
    return DEV_URL ? url.origin === new URL(DEV_URL).origin : url.origin === APP_ORIGIN;
  } catch {
    return false;
  }
}

/** Uygulama dışındaki bağlantılar (kaynak siteler, ilan kaynakları) sistem tarayıcısında açılır; sadece http(s). */
function openOutside(raw) {
  try {
    const url = new URL(raw);
    if (url.protocol === "https:" || url.protocol === "http:") shell.openExternal(url.toString()).catch(() => {});
  } catch {
    // geçersiz adres yok sayılır
  }
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1200,
    height: 820,
    minWidth: 360,
    minHeight: 480,
    show: false,
    title: "Cv'ne Bakalım!",
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
      webSecurity: true,
      spellcheck: false,
    },
  });
  win.once("ready-to-show", () => {
    if (!SMOKE) win.show();
  });
  win.loadURL(DEV_URL ?? `${APP_ORIGIN}/`);
  return win;
}

const smokeErrors = [];

async function waitFor(win, expression, timeoutMs = 5000) {
  const until = Date.now() + timeoutMs;
  while (Date.now() < until) {
    if (await win.webContents.executeJavaScript(expression)) return true;
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  return false;
}

/** Duman testi: ana sayfa çizildi mi, derin yol açılıyor mu, sayfada Node var mı, dist dışına çıkılabiliyor mu? */
async function smokeCheck(win) {
  try {
    const home = await waitFor(win, `(document.getElementById("root")?.childElementCount ?? 0) > 0`);
    // Derin bir yola doğrudan gitmek de index.html'e düşmeli (React Router).
    await win.loadURL(`${APP_ORIGIN}/giris`);
    const deep = await waitFor(win, `!!document.querySelector("input[type=email]")`);
    const result = await win.webContents.executeJavaScript(
      `(async () => {
        const escape = await fetch("/..%5c..%5cpackage.json");
        const upper = await fetch("/INDEX.HTML");
        return {
          origin: location.origin,
          node: typeof require !== "undefined" || typeof process !== "undefined",
          escapeIsIndex: (await escape.text()).includes('id="root"'),
          cspOnEveryFile: !!upper.headers.get("content-security-policy"),
        };
      })()`,
    );
    const ok = home && deep && !result.node && result.escapeIsIndex && result.cspOnEveryFile && !smokeErrors.length;
    console.log(`SMOKE ${ok ? "OK" : "FAIL"} ${JSON.stringify({ home, deep, ...result, errors: smokeErrors })}`);
    app.exit(ok ? 0 : 1);
  } catch (err) {
    console.log(`SMOKE FAIL ${err?.message ?? err}`);
    app.exit(1);
  }
}

function startUpdater() {
  // GitHub Releases'tan güncelleme (package.json → build.publish). İndirilen sürüm uygulama kapanınca kurulur.
  // Paketli Windows uygulamasında konsol yok: güncelleme kaydı kullanıcı klasöründeki log dosyasına yazılır.
  const { autoUpdater } = require("electron-updater");
  const logFile = path.join(app.getPath("logs"), "updater.log");
  const write = (level) => (msg) => {
    try {
      fs.mkdirSync(path.dirname(logFile), { recursive: true });
      fs.appendFileSync(logFile, `${new Date().toISOString()} ${level} ${msg}\n`);
    } catch {
      // log yazılamazsa güncelleme yine çalışır
    }
  };
  autoUpdater.logger = { info: write("INFO"), warn: write("WARN"), error: write("ERROR"), debug: () => {} };
  autoUpdater.checkForUpdatesAndNotify().catch((err) => write("ERROR")(err?.message ?? String(err)));
}

if (!app.requestSingleInstanceLock()) {
  // Başka bir pencere zaten açık; duman testi bunu "geçti" saymasın.
  if (SMOKE) console.log("SMOKE FAIL baska bir pencere acik");
  app.exit(SMOKE ? 1 : 0);
} else {
  app.on("second-instance", () => {
    const [win] = BrowserWindow.getAllWindows();
    if (win) {
      if (win.isMinimized()) win.restore();
      win.focus();
    }
  });

  // Her web içeriği için: yeni pencere ve dış gezinme engellenir, webview eklenemez.
  app.on("web-contents-created", (_event, contents) => {
    contents.setWindowOpenHandler(({ url }) => {
      openOutside(url);
      return { action: "deny" };
    });
    const stayInside = (event, url) => {
      if (!isAppUrl(url)) {
        event.preventDefault();
        openOutside(url);
      }
    };
    contents.on("will-navigate", stayInside);
    contents.on("will-redirect", stayInside);
    contents.on("will-attach-webview", (event) => event.preventDefault());
  });

  app.whenReady().then(() => {
    protocol.handle(SCHEME, serve);
    // Kamera, mikrofon, konum, bildirim gibi izinlere ihtiyaç yok: hepsi reddedilir.
    session.defaultSession.setPermissionRequestHandler((_wc, _permission, callback) => callback(false));
    session.defaultSession.setPermissionCheckHandler(() => false);

    const win = createWindow();
    if (SMOKE) {
      // CSP ihlali gibi hatalar konsola düşer; duman testi bunlarda başarısız sayılır.
      win.webContents.on("console-message", (event) => {
        if (event.level === "error") smokeErrors.push(event.message);
      });
      win.webContents.once("did-finish-load", () => smokeCheck(win));
      win.webContents.once("did-fail-load", (_e, code, desc) => {
        console.log(`SMOKE FAIL load ${code} ${desc}`);
        app.exit(1);
      });
    } else if (app.isPackaged) {
      startUpdater();
    }

    app.on("activate", () => {
      if (BrowserWindow.getAllWindows().length === 0) createWindow();
    });
  });

  app.on("window-all-closed", () => {
    if (process.platform !== "darwin") app.quit();
  });
}
