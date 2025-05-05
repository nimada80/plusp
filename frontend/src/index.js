import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import reportWebVitals from './reportWebVitals';
import { BrowserRouter } from 'react-router-dom';

// کاهش تعداد پیام‌ها و نمایش فقط اخطارها
const originalConsoleLog = console.log;
const originalConsoleWarn = console.warn;
const originalConsoleInfo = console.info;
const originalConsoleDebug = console.debug;
const originalConsoleError = console.error;

// حفظ متدهای اصلی کنسول برای استفاده در صورت نیاز
window._originalConsole = {
  log: originalConsoleLog,
  warn: originalConsoleWarn,
  info: originalConsoleInfo,
  debug: originalConsoleDebug,
  error: originalConsoleError
};

// غیرفعال کردن تمام پیام‌های معمولی
console.log = function() { 
  // کاملاً غیرفعال
};

// غیرفعال کردن هشدارها 
console.warn = function() {
  // کاملاً غیرفعال
};

// غیرفعال کردن پیام‌های اطلاعاتی
console.info = function() {
  // کاملاً غیرفعال
};

// غیرفعال کردن پیام‌های اشکال‌زدایی
console.debug = function() {
  // کاملاً غیرفعال
};

// فقط پیام‌های خطا نمایش داده شوند
console.error = function(...args) {
  originalConsoleError.apply(console, args);
};

// بازنویسی متد clear برای ریست کردن console در بعضی مرورگرها
const originalClear = console.clear;
console.clear = function() {
  originalClear.apply(console);
  console.error('کنسول پاک شد - فقط اخطارها نمایش داده می‌شوند');
};

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
);

// غیرفعال کردن reportWebVitals برای جلوگیری از لاگ‌های اضافی
// reportWebVitals();
