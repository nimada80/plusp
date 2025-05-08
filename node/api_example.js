/**
 * نمونه کد کلاینت برای فراخوانی API احراز هویت
 * این کد نحوه استفاده از API احراز هویت پلاس پی‌تی‌تی را نشان می‌دهد.
 */

// با استفاده از fetch API
async function authenticateUser(email, password) {
  try {
    const response = await fetch('http://localhost:3030/authenticate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'خطا در احراز هویت');
    }

    const data = await response.json();
    console.log('احراز هویت موفق:', data);
    
    // ذخیره اطلاعات کاربر و توکن‌ها
    localStorage.setItem('username', data.username);
    localStorage.setItem('userId', data.userId);
    localStorage.setItem('channels', JSON.stringify(data.channels));
    
    return data;
  } catch (error) {
    console.error('خطا در احراز هویت:', error.message);
    throw error;
  }
}

// با استفاده از axios
// ابتدا نیاز است axios نصب شود: npm install axios
function authenticateUserWithAxios(email, password) {
  const axios = require('axios');
  
  return axios.post('http://localhost:3030/authenticate', {
    email,
    password
  })
  .then(response => {
    const data = response.data;
    console.log('احراز هویت موفق:', data);
    
    // ذخیره اطلاعات کاربر و توکن‌ها
    localStorage.setItem('username', data.username);
    localStorage.setItem('userId', data.userId);
    localStorage.setItem('channels', JSON.stringify(data.channels));
    
    return data;
  })
  .catch(error => {
    console.error('خطا در احراز هویت:', 
      error.response?.data?.error || error.message);
    throw error;
  });
}

// مثال برای اتصال به LiveKit با استفاده از توکن دریافتی
// نیاز به نصب کتابخانه LiveKit است: npm install livekit-client
async function connectToLiveKit(channelData) {
  const { Room } = require('livekit-client');
  
  // ایجاد اتاق LiveKit
  const room = new Room();
  
  try {
    // اتصال به سرور LiveKit با استفاده از توکن
    await room.connect(`ws://${channelData.livekitHost}`, channelData.token);
    console.log(`اتصال به کانال ${channelData.channelName} برقرار شد`);
    
    // رویدادهای room را ثبت کنید
    room.on('participantConnected', participant => {
      console.log(`کاربر جدید متصل شد: ${participant.identity}`);
    });
    
    room.on('participantDisconnected', participant => {
      console.log(`کاربر قطع ارتباط کرد: ${participant.identity}`);
    });
    
    return room;
  } catch (error) {
    console.error(`خطا در اتصال به کانال ${channelData.channelName}:`, error.message);
    throw error;
  }
}

// مثال نحوه استفاده
async function example() {
  try {
    // 1. احراز هویت
    const authData = await authenticateUser('user@example.com', 'password123');
    
    // 2. بررسی کانال‌های موجود
    if (authData.channels.length === 0) {
      console.log('کاربر به هیچ کانالی دسترسی ندارد');
      return;
    }
    
    // 3. اتصال به اولین کانال
    const firstChannel = authData.channels[0];
    console.log(`در حال اتصال به کانال ${firstChannel.channelName}...`);
    
    const room = await connectToLiveKit(firstChannel);
    
    // 4. نمایش فهرست همه کانال‌ها
    console.log('فهرست کانال‌های مجاز:');
    authData.channels.forEach((channel, index) => {
      console.log(`${index + 1}. ${channel.channelName} (${channel.channelUid})`);
    });
    
    // به کاربر اجازه دهید کانال را انتخاب کند یا سایر عملیات را انجام دهد
    
  } catch (error) {
    console.error('خطا در اجرای نمونه:', error.message);
  }
}

// example();  // برای اجرای نمونه این خط را از حالت کامنت خارج کنید 