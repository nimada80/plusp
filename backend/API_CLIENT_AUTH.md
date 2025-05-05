# راهنمای API احراز هویت کاربر و توکن LiveKit

این API به کلاینت‌ها اجازه می‌دهد تا با ارسال نام کاربری و رمز عبور، احراز هویت شوند و توکن‌های دسترسی LiveKit برای کانال‌های مجاز خود را دریافت کنند.

## آدرس API
```
POST /api/auth/client/
```

## پارامترهای ورودی

| پارامتر | نوع | توضیحات |
|---------|------|------------|
| username | string | نام کاربری (ایمیل) |
| password | string | رمز عبور |
| server_url | string | (اختیاری) آدرس سرور LiveKit - پیش‌فرض به مقدار LIVEKIT_HOST در تنظیمات سرور |

## نمونه درخواست

```json
{
  "username": "user@example.com",
  "password": "user_password",
  "server_url": "https://livekit.yourdomain.com"
}
```

## پاسخ موفق

در صورت موفقیت‌آمیز بودن احراز هویت، API اطلاعات زیر را برمی‌گرداند:

```json
{
  "success": true,
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "username": "user@example.com",
  "channels": [
    {
      "channel_id": 1234567,
      "name": "کانال عمومی"
    },
    {
      "channel_id": 7654321,
      "name": "کانال خصوصی"
    }
  ],
  "tokens": {
    "1234567": {
      "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "room": "channel-1234567",
      "name": "کانال عمومی"
    },
    "7654321": {
      "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "room": "channel-7654321",
      "name": "کانال خصوصی"
    }
  },
  "server_url": "https://livekit.yourdomain.com"
}
```

## پاسخ‌های خطا

### خطای 400 - درخواست نامعتبر
زمانی که پارامترهای ورودی ناقص باشند:

```json
{
  "error": "نام کاربری و رمز عبور الزامی است."
}
```

### خطای 401 - عدم احراز هویت
زمانی که نام کاربری یا رمز عبور اشتباه باشد:

```json
{
  "error": "نام کاربری یا رمز عبور اشتباه است."
}
```

### خطای 403 - عدم دسترسی
زمانی که کاربر غیرفعال باشد:

```json
{
  "error": "حساب کاربری شما غیرفعال شده است."
}
```

یا زمانی که کاربر به هیچ کانالی دسترسی نداشته باشد:

```json
{
  "error": "شما به هیچ کانالی دسترسی ندارید."
}
```

### خطای 404 - یافت نشد
زمانی که اطلاعات کاربر در دیتابیس یافت نشود:

```json
{
  "error": "اطلاعات کاربر یافت نشد."
}
```

### خطای 500 - خطای سرور
زمانی که خطایی در سرور رخ دهد:

```json
{
  "error": "خطای سرور در احراز هویت",
  "details": "جزئیات خطا"
}
```

## نکات مهم

1. برای استفاده از این API، باید متغیرهای محیطی زیر در سرور تنظیم شوند:
   - `LIVEKIT_SERVER_URL`: آدرس سرور LiveKit
   - `LIVEKIT_SERVER_API_KEY`: کلید API سرور LiveKit
   - `LIVEKIT_SERVER_API_SECRET`: رمز API سرور LiveKit

2. توکن‌های تولید شده برای هر کانال منحصر به فرد هستند و باید در هنگام اتصال به اتاق LiveKit استفاده شوند.

3. نام اتاق LiveKit برای هر کانال به صورت `channel-{channel_id}` تعریف می‌شود.

4. این API از CORS پشتیبانی می‌کند و هدرهای مناسب را برای درخواست‌های Cross-Origin برمی‌گرداند.

## نمونه کد کلاینت (JavaScript)

```javascript
async function authenticateUser(username, password, serverUrl) {
  try {
    const response = await fetch('http://your-backend-url/api/auth/client/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        username,
        password,
        server_url: serverUrl,
      }),
    });

    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.error || 'خطا در احراز هویت');
    }
    
    return data;
  } catch (error) {
    console.error('Error:', error);
    throw error;
  }
}

// نمونه استفاده
authenticateUser('user@example.com', 'password123', 'https://livekit.yourdomain.com')
  .then(result => {
    console.log('Authentication successful:', result);
    
    // دسترسی به توکن‌ها
    const tokens = result.tokens;
    
    // اتصال به اولین کانال
    const firstChannelId = Object.keys(tokens)[0];
    const channelInfo = tokens[firstChannelId];
    
    // استفاده از اطلاعات برای اتصال به LiveKit
    connectToLiveKit(
      result.server_url, 
      channelInfo.token, 
      channelInfo.room
    );
  })
  .catch(error => {
    console.error('Authentication failed:', error.message);
  });

// اتصال به LiveKit (نیاز به کتابخانه livekit-client)
function connectToLiveKit(serverUrl, token, roomName) {
  // کد اتصال به LiveKit
  console.log(`Connecting to room ${roomName} on ${serverUrl} with token: ${token}`);
}
``` 