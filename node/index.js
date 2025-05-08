/**
 * index.js
 * سرویس احراز هویت کاربران با Supabase و دریافت توکن LiveKit
 */

const path = require('path');
const fs = require('fs');
const fastify = require('fastify')({ logger: true });
const { createClient } = require('@supabase/supabase-js');
const { AccessToken } = require('livekit-server-sdk');
const dotenv = require('dotenv');

// تلاش برای بارگذاری متغیرهای محیطی از فایل .env اگر موجود باشد
// ابتدا در مسیر داخل کانتینر و سپس در مسیر اصلی پروژه
const envPaths = [
  path.join(__dirname, '.env'),              // مسیر فایل در پوشه فعلی
  path.join('/docker', '.env'),              // مسیر محل قرارگیری فایل در docker
  path.join('..', 'docker', '.env'),         // مسیر نسبی به پوشه docker
  path.join(__dirname, '..', 'docker', '.env'), // مسیر مطلق به پوشه docker
  '/app/.env'                                // مسیر احتمالی در کانتینر
];

let envLoaded = false;

// بررسی همه مسیرهای ممکن برای فایل .env
for (const envPath of envPaths) {
  if (fs.existsSync(envPath)) {
    dotenv.config({ path: envPath });
    fastify.log.info(`متغیرهای محیطی از ${envPath} بارگذاری شدند`);
    envLoaded = true;
    break;
  }
}

if (!envLoaded) {
  fastify.log.warn(`فایل .env در هیچ یک از مسیرهای مورد انتظار پیدا نشد. از متغیرهای محیطی پیش‌فرض استفاده می‌شود.`);
  // اگر هیچ فایلی پیدا نشد، از متغیرهای محیطی سیستم استفاده می‌شود
  dotenv.config();
}

// تنظیم CORS
fastify.register(require('@fastify/cors'), {
  origin: true, // یا ['http://localhost', 'file://*'] برای امنیت بیشتر
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'X-Requested-With', 'Accept'],
  credentials: true // اجازه ارسال کوکی‌ها و هدرهای احراز هویت
});

// اتصال به Supabase
const supabaseUrl = process.env.SUPABASE_URL;
const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

if (!supabaseUrl || !supabaseServiceKey) {
  fastify.log.error('متغیرهای محیطی SUPABASE_URL یا SUPABASE_SERVICE_ROLE_KEY تنظیم نشده‌اند!');
  process.exit(1);
}

// تنظیمات LiveKit
const livekitApiKey = process.env.LIVEKIT_API_KEY;
const livekitApiSecret = process.env.LIVEKIT_API_SECRET;
const livekitHost = process.env.LIVEKIT_HOST || 'localhost:7880';

if (!livekitApiKey || !livekitApiSecret) {
  fastify.log.error('متغیرهای محیطی LIVEKIT_API_KEY یا LIVEKIT_API_SECRET تنظیم نشده‌اند!');
  process.exit(1);
}

// ایجاد کلاینت Supabase با دسترسی Service Role
const supabase = createClient(supabaseUrl, supabaseServiceKey);

/**
 * تولید توکن LiveKit برای کاربر و کانال مشخص
 * @param {string} username - نام کاربر
 * @param {string} channelUid - شناسه کانال
 * @param {string} channelName - نام کانال
 * @returns {object} - توکن و اطلاعات اتصال
 */
function generateLivekitToken(username, channelUid, channelName) {
  try {
    // ایجاد یک توکن دسترسی جدید با نام کاربر
    const token = new AccessToken(livekitApiKey, livekitApiSecret, {
      identity: username,
      // اضافه کردن متادیتا برای کاربر (به صورت JSON)
      metadata: JSON.stringify({
        name: username,
        channelName
      })
    });

    // اضافه کردن دسترسی به کانال مشخص (با استفاده از شناسه کانال)
    token.addGrant({ roomId: channelUid, roomJoin: true, canPublish: true, canSubscribe: true });

    // برگرداندن توکن، شناسه کانال و نام کانال
    return {
      token: token.toJwt(),
      channelUid,
      channelName,
      livekitHost
    };
  } catch (error) {
    fastify.log.error(`خطا در تولید توکن LiveKit: ${error.message}`);
    return null;
  }
}

/**
 * مسیر اصلی برای احراز هویت کاربر و دریافت توکن‌های LiveKit
 */
fastify.post('/api/node/token', async (request, reply) => {
  let { email, username, password } = request.body;

  // اگر username ارسال شده ولی email ارسال نشده، از username به عنوان email استفاده کنیم
  if (!email && username) {
    email = username + '@example.com'; // تبدیل username به یک ایمیل معتبر
  }
  
  // بررسی ورودی‌ها
  if (!email || !password) {
    reply.code(400).send({ error: 'ایمیل و رمز عبور الزامی هستند' });
    return;
  }

  try {
    // 1. احراز هویت کاربر با ایمیل/رمز عبور از طریق Supabase
    const { data: authData, error: authError } = await supabase.auth.signInWithPassword({
      email,
      password
    });

    if (authError) {
      fastify.log.error(`خطا در احراز هویت: ${authError.message}`);
      reply.code(401).send({ error: 'احراز هویت ناموفق بود', details: authError.message });
      return;
    }

    // دریافت uid کاربر از پاسخ احراز هویت
    const userId = authData.user.id;
    const username = email.split('@')[0]; // استفاده از بخش قبل از @ در ایمیل به عنوان نام کاربری

    // 2. دریافت کانال‌های مجاز کاربر از جدول users
    const { data: userData, error: userError } = await supabase
      .from('users')
      .select('allowed_channels')
      .eq('uid', userId)
      .single();

    if (userError) {
      fastify.log.error(`خطا در دریافت اطلاعات کاربر: ${userError.message}`);
      reply.code(404).send({ error: 'اطلاعات کاربر یافت نشد', details: userError.message });
      return;
    }

    // اگر لیست کانال‌های مجاز خالی باشد
    if (!userData.allowed_channels || userData.allowed_channels.length === 0) {
      reply.code(200).send({
        message: 'کاربر به هیچ کانالی دسترسی ندارد',
        username: username,
        channels: []
      });
      return;
    }

    // 3. دریافت نام کانال‌ها براساس uid آنها
    const { data: channelsData, error: channelsError } = await supabase
      .from('channels')
      .select('uid, name')
      .in('uid', userData.allowed_channels);

    if (channelsError) {
      fastify.log.error(`خطا در دریافت اطلاعات کانال‌ها: ${channelsError.message}`);
      reply.code(500).send({ error: 'خطا در دریافت اطلاعات کانال‌ها', details: channelsError.message });
      return;
    }

    // 4. تولید توکن LiveKit برای هر کانال
    const channelTokens = channelsData.map(channel => 
      generateLivekitToken(username, channel.uid, channel.name)
    ).filter(token => token !== null); // حذف توکن‌های ناموفق

    // 5. ارسال پاسخ به کلاینت
    reply.code(200).send({
      message: 'احراز هویت موفق',
      username: username,
      userId: userId,
      channels: channelTokens
    });

  } catch (error) {
    fastify.log.error(`خطای سیستمی: ${error.message}`);
    reply.code(500).send({ error: 'خطای سرور', details: error.message });
  }
});

// مسیر سلامتی برای بررسی وضعیت سرویس
fastify.get('/health', async (request, reply) => {
  reply.code(200).send({ status: 'up', version: '1.0.0' });
});

// تنظیم پورت از متغیرهای محیطی یا مقدار پیش‌فرض
const PORT = process.env.AUTH_SERVICE_PORT || 3030;
const HOST = process.env.AUTH_SERVICE_HOST || '0.0.0.0';

// شروع سرور
const start = async () => {
  try {
    await fastify.listen({ port: PORT, host: HOST });
    fastify.log.info(`سرویس احراز هویت در آدرس ${HOST}:${PORT} در حال اجراست`);
  } catch (err) {
    fastify.log.error(err);
    process.exit(1);
  }
};

start(); 