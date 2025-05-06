/*
 * UserManagement.js
 * React component for managing users and their channel assignments.
 * Supports CRUD operations and dual-list transfer UI with CSRF-protected API calls.
 */

import React, { useState, useEffect, useMemo } from 'react';
import {
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  TextField,
  Typography,
  Paper,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Grid,
  List,
  ListItem,
  ListItemText,
  Divider,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import EditIcon from '@mui/icons-material/Edit';
import { apiFetch } from '../utils/api';

/**
 * UserManagement
 * Provides UI and logic for listing, creating, editing, and deleting users.
 * Manages channel assignment using available/allowed dual lists.
 */
function UserManagement() {
  const [deletingId, setDeletingId] = useState(null);
  const [deleteError, setDeleteError] = useState('');
  const [users, setUsers] = useState([]);
  const [loadingUsers, setLoadingUsers] = useState(false);
  const [loadingChannels, setLoadingChannels] = useState(false);
  const [error, setError] = useState('');

  const [selectedAvailable, setSelectedAvailable] = useState([]);
  const [selectedAllowed, setSelectedAllowed] = useState([]);

  const [availableSearchQuery, setAvailableSearchQuery] = useState('');
  const [allowedSearchQuery, setAllowedSearchQuery] = useState('');

  const [userSearchQuery, setUserSearchQuery] = useState('');

  const filteredUsers = useMemo(() => {
    return (users || [])
      .filter((u) => u.username.toLowerCase().includes(userSearchQuery.toLowerCase()))
      .sort((a, b) => a.username.localeCompare(b.username, 'fa')); // مرتب‌سازی بر اساس حروف فارسی
  }, [users, userSearchQuery]);

  // Toggle selection of channels not assigned to user
  const handleSelectAvailable = (id) => {
    setSelectedAvailable((prev) => 
      prev.includes(id) ? prev.filter((cid) => cid !== id) : [...prev, id]
    );
  };

  // Toggle selection of channels already assigned to user
  const handleSelectAllowed = (id) => {
    setSelectedAllowed((prev) => 
      prev.includes(id) ? prev.filter((cid) => cid !== id) : [...prev, id]
    );
  };

  // Move selected channels between available and allowed lists
  const handleTransfer = (direction) => {
    if (direction === 'right') {
      setFormData((prev) => ({
        ...prev,
        allowed_channels: [...new Set([...prev.allowed_channels, ...selectedAvailable])],
      }));
      setSelectedAvailable([]);
    } else {
      setFormData((prev) => ({
        ...prev,
        allowed_channels: prev.allowed_channels.filter((cid) => !selectedAllowed.includes(cid)),
      }));
      setSelectedAllowed([]);
    }
  };

  const [channelsList, setChannelsList] = useState([]);
  const [open, setOpen] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const initialFormData = {
    username: '',
    password: '',
    role: 'regular',
    active: true,
    allowed_channels: [],
  };
  const [formData, setFormData] = useState(initialFormData);

  const roles = [
    { value: 'regular', label: 'کاربر ساده' },
    { value: 'senior', label: 'کاربر ارشد' },
    { value: 'manager', label: 'مدیر' },
    { value: 'admin', label: 'ادمین' },
  ];

  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [userToDelete, setUserToDelete] = useState(null);

  useEffect(() => {
    fetchUsers();
    fetchChannels();
  }, []);

  // Fetch all users from backend
  const fetchUsers = async () => {
    setLoadingUsers(true);
    setError('');
    try {
      const data = await apiFetch('/api/users/');
      setUsers(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('خطا در دریافت کاربران:', err);
      setError('خطا در دریافت لیست کاربران. لطفا دوباره تلاش کنید.');
      setUsers([]);
    } finally {
      setLoadingUsers(false);
    }
  };

  // Fetch all channels for assignment
  const fetchChannels = async () => {
    setLoadingChannels(true);
    setError('');
    try {
      const data = await apiFetch('/api/channels/');
      // اگر داده‌ها آرایه خالی باشند، خطا نیست
      if (Array.isArray(data)) {
        const formattedChannels = data.map((channel) => ({
          id: channel.uid,
          name: channel.name || `Channel ${channel.uid}`,
          channel_id: channel.channel_id || '',
        }));
        setChannelsList(formattedChannels);
      } else {
        setChannelsList([]);
      }
    } catch (err) {
      console.error('خطا در دریافت کانال‌ها:', err);
      // فقط در صورت خطای واقعی در ارتباط با سرور پیام خطا نمایش داده شود
      if (err.name === 'TypeError' || err.message?.includes('Failed to fetch')) {
        setError('خطا در ارتباط با سرور');
      }
      setChannelsList([]);
    } finally {
      setLoadingChannels(false);
    }
  };

  // Open dialog for creating or editing a user
  const handleClickOpen = (user = null) => {
    setSelectedAvailable([]);
    setSelectedAllowed([]);
    setAvailableSearchQuery('');
    setAllowedSearchQuery('');
    setError('');
    if (user) {
      setEditMode(true);
      setSelectedUser(user);
      setFormData({
        username: user.username || '',
        password: '',
        role: user.role || 'regular',
        active: typeof user.active === 'boolean' ? user.active : true,
        allowed_channels: Array.isArray(user.allowed_channels) ? user.allowed_channels : [],
      });
    } else {
      setEditMode(false);
      setSelectedUser(null);
      setFormData(initialFormData);
    }
    setOpen(true);
  };

  // Close the user dialog and reset form
  const handleClose = () => {
    setOpen(false);
    setSelectedUser(null);
    setEditMode(false);
    setError('');
  };

  // Update form state on input change
  const handleChange = (event) => {
    const { name, value, type, checked } = event.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  // Submit create or update request for user
  const handleSubmit = async () => {
    setError('');
    const payload = {
      username: formData.username,
      role: formData.role,
      active: formData.active,
      allowed_channels: formData.allowed_channels,
    };

    if (formData.password) {
      payload.password = formData.password;
    }

    // Debug log - برای مشاهده اطلاعات ارسالی (بدون نمایش کامل پسورد)
    console.log('Sending user data:', {
      ...payload,
      password: payload.password ? `${payload.password.substring(0, 3)}...` : undefined
    });

    try {
      if (editMode && selectedUser) {
        await apiFetch(`/api/users/${selectedUser.uid}/`, {
          method: 'PUT',
          body: JSON.stringify(payload),
        });
      } else {
        await apiFetch('/api/users/', {
          method: 'POST',
          body: JSON.stringify(payload),
        });
      }
      fetchUsers();
      handleClose();
    } catch (err) {
      console.error('خطا در ذخیره کاربر:', err);
      setError(err.message || 'خطا در ذخیره کاربر. لطفا ورودی‌ها را بررسی کنید.');
    }
  };

  // Delete user by ID via API
  const handleDelete = async (userId) => {
    // نمایش اطلاعات کاربر برای دیباگ
    console.log(`درخواست حذف کاربر:`, userId);
    
    // بررسی انواع شناسه‌ها
    if (!userId) {
      console.error('شناسه کاربر برای حذف خالی است');
      return;
    }
    
    // بررسی نوع داده شناسه
    console.log('نوع شناسه کاربر:', typeof userId);
    
    setUserToDelete(userId);
    setDeleteConfirmOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!userToDelete) {
      console.error('شناسه کاربر برای حذف تعیین نشده است');
      return;
    }
    
    setDeletingId(userToDelete);
    setDeleteError('');
    setError('');
    try {
      console.log(`شروع حذف کاربر با شناسه: ${userToDelete}`);
      console.log(`آدرس API: /api/users/${userToDelete}/`);
      
      // نمایش توکن CSRF برای دیباگ
      const csrfCookie = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='));
      const csrfToken = csrfCookie ? csrfCookie.split('=')[1] : 'توکن یافت نشد';
      console.log(`CSRF Token: ${csrfToken}`);

      // تست این درخواست با fetch مستقیم به جای apiFetch
      try {
        const baseUrl = process.env.REACT_APP_API_BASE_URL || 'http://localhost';
        const apiUrl = `${baseUrl}/api/users/${userToDelete}/`;
        console.log(`درخواست با fetch مستقیم به آدرس: ${apiUrl}`);
        
        const deleteResponse = await fetch(apiUrl, {
          method: 'DELETE',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
          },
          credentials: 'include',
        });
        
        console.log(`نتیجه درخواست مستقیم: ${deleteResponse.status} ${deleteResponse.statusText}`);
        
        if (deleteResponse.ok) {
          console.log('حذف با موفقیت انجام شد');
          fetchUsers();
        } else {
          const errorText = await deleteResponse.text();
          console.error(`خطای درخواست: ${errorText}`);
          setDeleteError(`خطا در حذف کاربر: ${deleteResponse.status} ${deleteResponse.statusText}`);
        }
      } catch (fetchErr) {
        console.error(`خطا در fetch مستقیم: ${fetchErr.message}`);
        
        // در صورت خطا در fetch مستقیم، از apiFetch استفاده کنیم
        console.log('تلاش با استفاده از apiFetch...');
        const response = await apiFetch(`/api/users/${userToDelete}/`, {
          method: 'DELETE',
        });
        
        console.log('پاسخ apiFetch:', response);
        fetchUsers();
      }
    } catch (err) {
      console.error('خطا در حذف کاربر:', err);
      setDeleteError(err.message || 'خطا در حذف کاربر');
    } finally {
      setDeletingId(null);
      setDeleteConfirmOpen(false);
      setUserToDelete(null);
    }
  };

  const handleDeleteCancel = () => {
    setDeleteConfirmOpen(false);
    setUserToDelete(null);
  };

  const allowedChannelsDetails = channelsList.filter((c) => formData.allowed_channels.includes(c.id)).filter((c) =>
    c.name.toLowerCase().includes(allowedSearchQuery.toLowerCase())
  );

  const availableChannelsDetails = channelsList.filter((c) => !formData.allowed_channels.includes(c.id)).filter((c) =>
    c.name.toLowerCase().includes(availableSearchQuery.toLowerCase())
  );

  return (
    <Box sx={{ fontFamily: 'IRANSans, Vazirmatn, Roboto, Arial', fontSize: 15 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h5" sx={{ fontFamily: 'IRANSans, Vazirmatn, Roboto, Arial', fontSize: 24, fontWeight: 700 }} gutterBottom component="div">
          مدیریت کاربران
        </Typography>
        <Button variant="contained" onClick={() => handleClickOpen()}>
          افزودن کاربر جدید
        </Button>
      </Box>
      <TextField
        label="جستجوی کاربر..."
        variant="outlined"
        size="small"
        fullWidth
        value={userSearchQuery}
        onChange={(e) => setUserSearchQuery(e.target.value)}
        sx={{ mb: 2 }}
      />
      {error && <Typography color="error" gutterBottom>{error}</Typography>}
      {deleteError && <Typography color="error" gutterBottom>{deleteError}</Typography>}
      <Paper sx={{ p: 2, mb: 2 }}>
        <TableContainer>
          <Table size="small" sx={{ 
            '& .MuiTableCell-root': { 
              fontFamily: 'IRANSans, Vazirmatn, Roboto, Arial', 
              fontSize: 14, 
              padding: '8px 16px',
              width: '25%'  // تنظیم عرض مساوی برای ستون‌ها
            } 
          }}>
            <TableHead>
              <TableRow>
                <TableCell align="right" sx={{ fontWeight: 'bold' }}>نام کاربری</TableCell>
                <TableCell align="right" sx={{ fontWeight: 'bold' }}>نقش</TableCell>
                <TableCell align="right" sx={{ fontWeight: 'bold' }}>وضعیت</TableCell>
                <TableCell align="center" sx={{ fontWeight: 'bold' }}>اقدامات</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {loadingUsers ? (
                <TableRow>
                  <TableCell colSpan={4} align="center">در حال بارگذاری کاربران...</TableCell>
                </TableRow>
              ) : filteredUsers.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={4} align="center">کاربری یافت نشد.</TableCell>
                </TableRow>
              ) : (
                filteredUsers.map((user) => (
                  <TableRow key={user.uid} hover>
                    <TableCell align="right">{user.username}</TableCell>
                    <TableCell align="right">{roles.find((r) => r.value === user.role)?.label || user.role}</TableCell>
                    <TableCell align="right">{user.active ? 'فعال' : 'غیرفعال'}</TableCell>
                    <TableCell align="center">
                      <IconButton color="primary" size="small" onClick={() => handleClickOpen(user)}>
                        <EditIcon />
                      </IconButton>
                      <IconButton color="error" size="small" onClick={() => handleDelete(user.uid)} disabled={deletingId === user.uid}>
                        {deletingId === user.uid ? '...' : <DeleteIcon />}
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>
      <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth sx={{ '& .MuiDialog-paper': { width: 600, maxWidth: '600px' } }}>
        <DialogTitle sx={{ textAlign: 'right' }}>{editMode ? 'ویرایش کاربر' : 'افزودن کاربر جدید'}</DialogTitle>
        <DialogContent sx={{ textAlign: 'right' }}>
          {error && <Typography color="error" gutterBottom>{error}</Typography>}
          <TextField
            autoFocus
            margin="dense"
            name="username"
            label="نام کاربری"
            type="text"
            fullWidth
            variant="outlined"
            sx={{ direction: 'rtl', mb: 2 }}
            value={formData.username}
            onChange={handleChange}
            required
          />
          <TextField
            margin="dense"
            name="password"
            label={editMode ? 'رمز عبور (خالی بگذارید اگر تغییری نمی‌دهید)' : 'رمز عبور'}
            type="password"
            fullWidth
            variant="outlined"
            sx={{ mb: 2 }}
            value={formData.password}
            onChange={handleChange}
            required={!editMode}
          />
          <FormControl fullWidth variant="outlined" margin="dense" sx={{ mb: 2 }}>
            <InputLabel id="role-select-label">نقش</InputLabel>
            <Select
              labelId="role-select-label"
              name="role"
              value={formData.role}
              label="نقش"
              onChange={handleChange}
            >
              {roles.map((option) => (
                <MenuItem key={option.value} value={option.value}>
                  {option.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <FormControlLabel
            control={<Switch checked={formData.active} onChange={handleChange} name="active" />}
            label="فعال"
          />

          <Divider sx={{ my: 2 }} />
          <Typography
            variant="h6"
            sx={{ mt: 2, mb: 1, textAlign: 'center' }}
          >
            مدیریت کانال‌های مجاز
          </Typography>
          <Grid container spacing={2} justifyContent="center" alignItems="flex-start">
            <Grid item xs={5}>
              <Typography variant="body2" sx={{ mb: 1, textAlign: 'center' }}>کانال‌های موجود</Typography>
              <TextField
                label="جستجو..."
                variant="outlined"
                size="small"
                fullWidth
                value={availableSearchQuery}
                onChange={(e) => setAvailableSearchQuery(e.target.value)}
                sx={{ mb: 1 }}
              />
              <Paper sx={{ width: '100%', height: 250, overflow: 'auto', direction: 'rtl' }}>
                <List dense component="div" role="list">
                  {channelsList
                    .filter((c) => !formData.allowed_channels.includes(c.id) && c.name.toLowerCase().includes(availableSearchQuery.toLowerCase()))
                    .map((channel) => (
                      <ListItem
                        key={channel.id}
                        button
                        selected={selectedAvailable.includes(channel.id)}
                        onClick={() => handleSelectAvailable(channel.id)}
                        sx={selectedAvailable.includes(channel.id) ? { bgcolor: '#90caf9 !important' } : {}}
                      >
                        <ListItemText primary={channel.name} sx={{ textAlign: 'center' }} />
                      </ListItem>
                    ))}
                </List>
              </Paper>
            </Grid>
            <Grid item xs={1} sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
              <Button
                variant="outlined"
                size="small"
                onClick={() => handleTransfer('right')}
                disabled={selectedAvailable.length === 0}
                sx={{ mb: 1 }}
              >
                &gt;
              </Button>
              <Button
                variant="outlined"
                size="small"
                onClick={() => handleTransfer('left')}
                disabled={selectedAllowed.length === 0}
              >
                &lt;
              </Button>
            </Grid>
            <Grid item xs={5}>
              <Typography variant="body2" sx={{ mb: 1, textAlign: 'center' }}>کانال‌های مجاز</Typography>
              <TextField
                label="جستجو..."
                variant="outlined"
                size="small"
                fullWidth
                value={allowedSearchQuery}
                onChange={(e) => setAllowedSearchQuery(e.target.value)}
                sx={{ mb: 1 }}
              />
              <Paper sx={{ width: '100%', height: 250, overflow: 'auto', direction: 'rtl' }}>
                <List dense component="div" role="list">
                  {channelsList
                    .filter((c) => formData.allowed_channels.includes(c.id) && c.name.toLowerCase().includes(allowedSearchQuery.toLowerCase()))
                    .map((channel) => (
                      <ListItem
                        key={channel.id}
                        button
                        selected={selectedAllowed.includes(channel.id)}
                        onClick={() => handleSelectAllowed(channel.id)}
                        sx={selectedAllowed.includes(channel.id) ? { bgcolor: '#90caf9 !important' } : {}}
                      >
                        <ListItemText primary={channel.name} sx={{ textAlign: 'center' }} />
                      </ListItem>
                    ))}
                </List>
              </Paper>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose}>لغو</Button>
          <Button onClick={handleSubmit}>{editMode ? 'ذخیره تغییرات' : 'افزودن'}</Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteConfirmOpen}
        onClose={handleDeleteCancel}
        aria-labelledby="delete-dialog-title"
      >
        <DialogTitle id="delete-dialog-title">تأیید حذف کاربر</DialogTitle>
        <DialogContent>
          <Typography>
            آیا از حذف این کاربر اطمینان دارید؟ این عمل غیرقابل بازگشت است.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleDeleteCancel} color="primary">
            انصراف
          </Button>
          <Button onClick={handleDeleteConfirm} color="error" autoFocus>
            حذف
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default UserManagement;
