from django.contrib.admin.forms import AdminAuthenticationForm
from django.contrib.auth import login as auth_login
from django.contrib.auth.views import LoginView
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
import logging

# تنظیم لاگر برای دیباگ بهتر
logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class AdminLoginView(LoginView):
    """
    ویو سفارشی برای لاگین پنل ادمین که از بررسی CSRF معاف است
    """
    template_name = 'admin/login.html'
    form_class = AdminAuthenticationForm
    
    def get_success_url(self):
        return reverse('admin:index')
    
    def form_valid(self, form):
        """
        پس از احراز هویت موفق، کاربر را وارد سیستم می‌کند
        """
        # ثبت اطلاعات مهم در لاگ
        logger.info(f"احراز هویت موفق برای کاربر: {form.get_user()}")
        
        # ذخیره کاربر در سشن با تنظیمات بیشتر
        auth_login(self.request, form.get_user())
        
        # بررسی وجود سشن
        if self.request.user.is_authenticated:
            logger.info(f"کاربر {self.request.user.username} با موفقیت وارد شد و در سشن ذخیره شد")
        else:
            logger.error("کاربر احراز هویت شد اما در سشن ذخیره نشد")

        # تنظیم کوکی‌های اضافی برای اطمینان از سشن
        response = HttpResponseRedirect(self.get_success_url())
        return response
        
    def post(self, request, *args, **kwargs):
        """
        اضافه کردن معافیت CSRF برای درخواست‌های POST
        """
        # دیباگ اطلاعات POST
        logger.info(f"درخواست POST دریافت شد: {request.POST}")
        
        form = self.get_form()
        if form.is_valid():
            logger.info("فرم معتبر است")
            return self.form_valid(form)
        else:
            logger.error(f"خطاهای فرم: {form.errors}")
            return self.form_invalid(form)
            
    def get(self, request, *args, **kwargs):
        """
        نمایش فرم لاگین
        """
        logger.info(f"درخواست GET به {request.path} دریافت شد")
        return super().get(request, *args, **kwargs) 