# Dockerfile for React frontend
FROM node:20-alpine as build

# تنظیم دایرکتوری کاری
WORKDIR /app

# کپی فایل‌های package.json و package-lock.json
COPY package.json package-lock.json ./

# نصب وابستگی‌ها
RUN npm install

# کپی بقیه فایل‌های پروژه
COPY . .

# تنظیم متغیر محیطی برای ساخت
ARG REACT_APP_API_BASE_URL=http://localhost
ENV REACT_APP_API_BASE_URL=${REACT_APP_API_BASE_URL}

# ساخت نسخه production
RUN npm run build

# مرحله دوم - سرور nginx برای سرو فایل‌های استاتیک
FROM nginx:1.25-alpine

# کپی فایل‌های استاتیک ساخته شده
COPY --from=build /app/build /usr/share/nginx/html

# ایجاد فایل env.js برای تنظیم متغیرهای محیطی در زمان اجرا
RUN echo "window.env = { REACT_APP_API_BASE_URL: 'http://localhost' };" > /usr/share/nginx/html/env.js

# کپی اسکریپت راه‌اندازی
COPY docker-entrypoint.sh /
RUN chmod +x /docker-entrypoint.sh

# کپی کانفیگ nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# نمایش پورت 80
EXPOSE 80

# اجرای nginx با اسکریپت راه‌اندازی
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"] 