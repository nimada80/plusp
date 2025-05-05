#!/bin/bash
# اسکریپت پشتیبان‌گیری از پایگاه داده پلاس پی‌تی‌تی

# تنظیمات
BACKUP_DIR="./backups"
DATE=$(date +%Y-%m-%d_%H-%M-%S)
BACKUP_FILE="$BACKUP_DIR/plusptt_db_$DATE.sql"
BACKUP_FILE_COMPRESSED="$BACKUP_FILE.gz"
RETENTION_DAYS=30

# ایجاد دایرکتوری پشتیبان‌گیری اگر وجود ندارد
mkdir -p $BACKUP_DIR

# پشتیبان‌گیری از پایگاه داده
echo "پشتیبان‌گیری از پایگاه داده در $BACKUP_FILE..."
docker exec supabase-db pg_dump -U postgres postgres > $BACKUP_FILE

# بررسی موفقیت عملیات
if [ $? -eq 0 ]; then
    echo "پشتیبان‌گیری با موفقیت انجام شد."
    
    # فشرده‌سازی فایل پشتیبان
    echo "در حال فشرده‌سازی فایل پشتیبان..."
    gzip $BACKUP_FILE
    
    # بررسی موفقیت عملیات فشرده‌سازی
    if [ $? -eq 0 ]; then
        echo "فشرده‌سازی با موفقیت انجام شد: $BACKUP_FILE_COMPRESSED"
        
        # حذف فایل‌های پشتیبان قدیمی‌تر از مدت تعیین شده
        echo "در حال حذف فایل‌های پشتیبان قدیمی‌تر از $RETENTION_DAYS روز..."
        find $BACKUP_DIR -name "plusptt_db_*.sql.gz" -type f -mtime +$RETENTION_DAYS -delete
        
        # نمایش اطلاعات فایل پشتیبان
        echo "اطلاعات فایل پشتیبان:"
        ls -lh $BACKUP_FILE_COMPRESSED
        
        # نمایش تعداد کل فایل‌های پشتیبان
        BACKUP_COUNT=$(ls -1 $BACKUP_DIR/plusptt_db_*.sql.gz 2>/dev/null | wc -l)
        echo "تعداد کل فایل‌های پشتیبان موجود: $BACKUP_COUNT"
    else
        echo "خطا در فشرده‌سازی فایل پشتیبان."
    fi
else
    echo "خطا در پشتیبان‌گیری از پایگاه داده."
    # حذف فایل پشتیبان ناقص در صورت وجود
    if [ -f $BACKUP_FILE ]; then
        rm $BACKUP_FILE
    fi
fi 