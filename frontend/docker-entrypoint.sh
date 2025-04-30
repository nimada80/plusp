#!/bin/sh

# ایجاد فایل env.js با متغیرهای محیطی
echo "window.env = { REACT_APP_API_BASE_URL: '${REACT_APP_API_BASE_URL:-http://localhost}' };" > /usr/share/nginx/html/env.js

# اجرای دستور اصلی
exec "$@" 