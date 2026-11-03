// A local product-test runtime, never a remote API or production login service.
// Version is pinned. Module workers are required by this Pyodide release.
import {pbkdf2_hex} from './crypto-runtime.mjs';
const RUNTIME_URL = 'https://cdn.jsdelivr.net/pyodide/v314.0.7/full/';
const DATA_PATH = '/school-browser-test-v04';
let runtime, bridge, activeMode = 'demo';
let queue = Promise.resolve();
const progress = text => self.postMessage({kind:'progress',text});
const sync = populate => new Promise((resolve,reject) => runtime.FS.syncfs(populate,error => error ? reject(error) : resolve()));

async function boot(hostname, mode) {
  progress('بارگذاری موتور اجرای نسخهٔ ۰٫۴؛ بار اول ممکن است کمی طول بکشد…');
  const {loadPyodide} = await import(RUNTIME_URL + 'pyodide.mjs');
  runtime = await loadPyodide({indexURL:RUNTIME_URL, stdout:()=>{}, stderr:()=>{}});
  runtime.registerJsModule('school_crypto',{pbkdf2_hex});
  runtime.FS.mkdirTree(DATA_PATH);
  runtime.FS.mount(runtime.FS.filesystems.IDBFS, {}, DATA_PATH);
  progress('بازخوانی داده‌های آزمایشی همین مرورگر…');
  await sync(true);
  const response = await fetch(new URL('./backend.zip',import.meta.url));
  if(!response.ok) throw new Error('دریافت کد نسخهٔ ۰٫۴ ممکن نشد.');
  runtime.FS.writeFile('/school-backend.zip',new Uint8Array(await response.arrayBuffer()));
  runtime.runPython("import zipfile, sys\nzipfile.ZipFile('/school-backend.zip').extractall('/school-source')\nsys.path.insert(0,'/school-source')\nimport browser_bridge");
  bridge = runtime.pyimport('browser_bridge');
  progress('آماده‌سازی ۴۲۰ پروندهٔ ساختگی و نقش‌های نمونه…');
  const result = JSON.parse(bridge.initialize(hostname,mode));
  activeMode = mode;
  await sync(false);
  return result;
}

async function execute(message) {
  const {id,kind} = message;
  try {
    let result;
    if(kind==='boot') result = await boot(message.hostname,message.mode);
    else {
      if(!bridge) throw new Error('موتور هنوز آماده نیست.');
      if(kind==='request') {
        result = JSON.parse(bridge.handle_request(JSON.stringify(message.request)));
        // Respond only after IndexedDB has acknowledged durable local storage.
        if(message.request.method==='POST') await sync(false);
      } else if(kind==='mode') {
        progress(message.mode==='demo' ? 'باز کردن مدرسهٔ نمونه…' : 'باز کردن نصب خالی برای آزمون ادمین اولیه…');
        result = JSON.parse(bridge.initialize(message.hostname,message.mode));
        activeMode = message.mode;
        await sync(false);
      } else if(kind==='role') {
        if(activeMode!=='demo') throw new Error('انتخاب نقش فقط برای حساب‌های ساختگی مدرسهٔ نمونه است.');
        result = JSON.parse(bridge.select_demo_role(message.role));
        await sync(false);
      } else if(kind==='reset' || kind==='restore') {
        progress(kind==='reset' ? 'ساخت نمونهٔ تازه؛ نسخهٔ قبلی برای بازگردانی نگه داشته می‌شود…' : 'بازگردانی نمونهٔ قبلی…');
        result = JSON.parse(bridge.reset_sandbox(kind==='restore'));
        await sync(false);
      } else throw new Error('فرمان آزمون شناخته نشد.');
    }
    self.postMessage({id,kind:'result',result});
  } catch(error) {
    // Do not print requests, passwords, cookies or database records.
    self.postMessage({id,kind:'error',error:kind==='boot'
      ? 'شروع محیط تست ممکن نشد. دسترسی به CDN و اجازهٔ ذخیره‌سازی مرورگر را بررسی کنید.'
      : 'عملیات محیط تست کامل نشد. داده‌ها را پاک نکنید و دوباره تلاش کنید.'});
  }
}
self.onmessage = event => { queue = queue.then(()=>execute(event.data)); };
