from django.utils.deprecation import MiddlewareMixin
from django.views.decorators.csrf import csrf_exempt
import logging
import re

logger = logging.getLogger(__name__)

class CustomCsrfMiddleware(MiddlewareMixin):
    """
    میدل‌ور سفارشی برای مدیریت CSRF در مسیرهای خاص
    """
    def process_view(self, request, callback, callback_args, callback_kwargs):
        # مسیرهایی که باید از بررسی CSRF معاف شوند
        exempt_paths = [
            '/backend/admin/login/',
            '/api/auth/login/',
            '/admin/login/',
            '/api/users/',
        ]
        
        # اگر مسیر درخواست در لیست معاف‌ها باشد، CSRF بررسی نشود
        if any(request.path.startswith(path) for path in exempt_paths):
            logger.debug(f"مسیر {request.path} از بررسی CSRF معاف شد")
            setattr(request, '_dont_enforce_csrf_checks', True)
            return None
            
        # لاگ کردن اطلاعات CSRF برای دیباگ
        if request.method == 'POST':
            logger.debug(f"CSRF token in cookie: {request.COOKIES.get('csrftoken', 'None')}")
            logger.debug(f"CSRF token in header: {request.META.get('HTTP_X_CSRFTOKEN', 'None')}")
            
        # در غیر این صورت، بگذارید میدل‌ور بعدی آن را پردازش کند
        return None
    
    def process_response(self, request, response):
        # از تنظیم هدرهای CORS خودداری می‌کنیم چون در nginx تنظیم شده‌اند
        # فقط لاگ می‌کنیم برای دیباگ
        if re.match(r'^/(api|backend)/', request.path):
            # لاگ کردن هدرهای موجود
            logger.debug(f"Response headers for {request.path}: {dict(response.headers)}")
                
            # بررسی Origin برای دیباگ
            origin = request.META.get('HTTP_ORIGIN')
            if origin:
                logger.debug(f"Origin header: {origin}")
        
        return response

class SessionDebugMiddleware(MiddlewareMixin):
    """
    میدل‌ور برای دیباگ اطلاعات سشن و احراز هویت
    همچنین تنظیم مسیر درخواست با توجه به هدر X-Script-Name
    """
    def process_request(self, request):
        # لاگ کردن اطلاعات درخواست مرتبط با مسیر admin
        if request.path.startswith('/admin') or request.path.startswith('/backend/admin'):
            logger.debug(f"درخواست به مسیر ادمین: {request.path}")
            logger.debug(f"وضعیت احراز هویت: {request.user.is_authenticated}")
            logger.debug(f"کوکی‌های درخواست: {request.COOKIES}")
            logger.debug(f"هدرهای درخواست: {dict(request.headers)}")
            
            # لاگ هدر X-Script-Name اگر موجود باشد
            if 'HTTP_X_SCRIPT_NAME' in request.META:
                logger.debug(f"X-Script-Name هدر: {request.META['HTTP_X_SCRIPT_NAME']}")
            
            if hasattr(request, 'session'):
                logger.debug(f"کلیدهای سشن: {list(request.session.keys())}")
        
        # لاگ کردن اطلاعات درخواست برای مسیرهای API نیز
        if request.path.startswith('/api/'):
            logger.debug(f"درخواست API: {request.path}, متد: {request.method}")
            logger.debug(f"وضعیت احراز هویت: {request.user.is_authenticated}")
            logger.debug(f"کوکی‌های درخواست: {request.COOKIES}")
            if 'HTTP_X_CSRFTOKEN' in request.META:
                logger.debug(f"CSRF Token در هدر: {request.META['HTTP_X_CSRFTOKEN']}")
            
        return None
    
    def process_response(self, request, response):
        # لاگ کردن اطلاعات پاسخ مرتبط با مسیر admin
        if request.path.startswith('/admin') or request.path.startswith('/backend/admin'):
            logger.debug(f"پاسخ به مسیر ادمین: {request.path}")
            logger.debug(f"هدرهای پاسخ: {dict(response.headers)}")
            logger.debug(f"کوکی‌های پاسخ: {response.cookies}")
            logger.debug(f"کد وضعیت: {response.status_code}")
            
            # لاگ کردن مسیر ریدایرکت اگر موجود باشد
            if 'Location' in response:
                logger.debug(f"مسیر ریدایرکت: {response['Location']}")
        
        # لاگ کردن اطلاعات پاسخ API
        if request.path.startswith('/api/'):
            logger.debug(f"پاسخ API: {request.path}, کد وضعیت: {response.status_code}")
            logger.debug(f"هدرهای پاسخ: {dict(response.headers)}")
            if 'Set-Cookie' in response:
                logger.debug(f"کوکی‌های تنظیم شده: {response['Set-Cookie']}")
        
        return response 