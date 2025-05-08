FROM node:18-alpine

WORKDIR /app

# کپی فایل‌های پروژه
COPY package*.json ./
RUN npm install

# کپی کد برنامه
COPY . .

# تنظیم متغیرهای محیطی پیش‌فرض (در تولید از .env استفاده می‌شود)
ENV NODE_ENV=production
ENV AUTH_SERVICE_PORT=3030
ENV AUTH_SERVICE_HOST=0.0.0.0

# پورت سرویس
EXPOSE 3030

# شروع برنامه
CMD ["npm", "start"] 