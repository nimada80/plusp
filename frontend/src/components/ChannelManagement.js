/*
 * ChannelManagement.js
 * React component for listing, creating, editing, and deleting channels.
 * Supports dual-list user assignment and CSRF-protected API calls.
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
  List,
  ListItem,
  ListItemText,
  Typography,
  Paper,
  Grid,
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
 * ChannelManagement
 * Manages channels: fetch list, open dialog for add/edit, transfer users
 * State variables:
 *  - channels: list of channels
 *  - formData: current channel data
 */
function ChannelManagement() {
  // State structure harmonized with UserManagement.js
  const [deletingId, setDeletingId] = useState(null);
  const [deleteError, setDeleteError] = useState('');
  const [channels, setChannels] = useState([]);
  const [loadingChannels, setLoadingChannels] = useState(false);
  const [loadingUsers, setLoadingUsers] = useState(false);
  const [error, setError] = useState('');

  const [selectedAvailable, setSelectedAvailable] = useState([]);
  const [selectedAllowed, setSelectedAllowed] = useState([]);

  const [availableSearchQuery, setAvailableSearchQuery] = useState('');
  const [allowedSearchQuery, setAllowedSearchQuery] = useState('');
  const [channelSearchQuery, setChannelSearchQuery] = useState('');

  const [users, setUsers] = useState([]);
  const [open, setOpen] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [selectedChannel, setSelectedChannel] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    allowed_users: [],
  });

  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [channelToDelete, setChannelToDelete] = useState(null);

  // Table filter
  const filteredChannels = useMemo(() => {
    // محافظت: اطمینان از آرایه بودن channels
    const safeChannels = Array.isArray(channels) ? channels : [];
    
    return safeChannels
      .filter(c => {
        if (!c || typeof c !== 'object') return false;
        if (!c.name) return false;
        return c.name.toLowerCase().includes((channelSearchQuery || '').toLowerCase());
      })
      .sort((a, b) => a.name.localeCompare(b.name, 'fa')); // مرتب‌سازی بر اساس حروف فارسی
  }, [channels, channelSearchQuery]);

  // Fetch all channels from backend
  const fetchChannels = async () => {
    setLoadingChannels(true);
    setError('');
    try {
      const data = await apiFetch('/api/channels/');

      // مدیریت جامع انواع مختلف پاسخ
      let channelsArray = [];

      if (Array.isArray(data)) {
        // 1. پاسخ یک آرایه است
        channelsArray = data;
      } else if (data && typeof data === 'object') {
        // 2. پاسخ یک شیء است
        if (data.channels && Array.isArray(data.channels)) {
          // 2.1. شیء دارای فیلد channels است
          channelsArray = data.channels;
        } else if (data.results && Array.isArray(data.results)) {
          // 2.2. شیء دارای فیلد results است (برای pagination)
          channelsArray = data.results;
        } else if (data.data && Array.isArray(data.data)) {
          // 2.3. شیء دارای فیلد data است
          channelsArray = data.data;
        } else if (Object.keys(data).length === 0) {
          // 2.4. شیء خالی است - آرایه خالی برگردانیم
          channelsArray = [];
        } else if (data.detail || data.message) {
          // 2.5. شیء حاوی پیام خطا است
          console.error('API Error:', data.detail || data.message);
          channelsArray = [];
        } else {
          // 2.6. ساختار ناشناخته - سعی کنیم مقادیر را استخراج کنیم
          console.warn('Unknown response structure:', data);
          // تبدیل خود شیء به آرایه اگر هیچ ساختار شناخته‌شده‌ای نداشت
          const possibleItems = Object.values(data).filter(val => 
            typeof val === 'object' && val !== null
          );
          if (possibleItems.length > 0) {
            channelsArray = possibleItems;
          } else {
            channelsArray = [];
          }
        }
      } else {
        // 3. داده null یا undefined یا نوع دیگری است
        console.warn('Unexpected response type:', typeof data);
        channelsArray = [];
      }

      setChannels(channelsArray);
    } catch (err) {
      console.error('Error fetching channels:', err);
      setError('خطا در دریافت لیست کانال‌ها. لطفا دوباره تلاش کنید.');
      setChannels([]);
    } finally {
      setLoadingChannels(false);
    }
  };

  // Fetch all users for assignment
  const fetchUsers = async () => {
    setLoadingUsers(true);
    setError('');
    try {
      const data = await apiFetch('/api/users/');
      if (!data) {
        setUsers([]);
        return;
      }
      if (!Array.isArray(data)) {
        setUsers([]);
        return;
      }
      setUsers(data);
    } catch (err) {
      console.error('Error fetching users:', err);
      setError('خطا در دریافت لیست کاربران.');
      setUsers([]);
    } finally {
      setLoadingUsers(false);
    }
  };

  useEffect(() => {
    fetchChannels();
    fetchUsers();
  }, []);

  // Open dialog for creating or editing a channel
  const handleClickOpen = (channel = null) => {
    setSelectedAvailable([]);
    setSelectedAllowed([]);
    setAvailableSearchQuery('');
    setAllowedSearchQuery('');
    setError('');
    if (channel) {
      setEditMode(true);
      setSelectedChannel(channel);
      setFormData({
        name: channel.name || '',
        allowed_users: Array.isArray(channel.allowed_users) ? channel.allowed_users : [],
      });
    } else {
      setEditMode(false);
      setSelectedChannel(null);
      setFormData({
        name: '',
        allowed_users: [],
      });
    }
    setOpen(true);
  };

  // Close the dialog and reset form
  const handleClose = () => {
    setOpen(false);
    setSelectedChannel(null);
    setEditMode(false);
    setError('');
  };

  // Update form state on input change
  const handleChange = (event) => {
    const { name, value } = event.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  // Move selected users between available and allowed lists
  const handleTransfer = (direction) => {
    if (direction === 'right' && selectedAvailable.length > 0) {
      setFormData((prev) => ({
        ...prev,
        allowed_users: [...new Set([...prev.allowed_users, ...selectedAvailable])],
      }));
      setSelectedAvailable([]);
    } else if (direction === 'left' && selectedAllowed.length > 0) {
      setFormData((prev) => ({
        ...prev,
        allowed_users: prev.allowed_users.filter((uid) => !selectedAllowed.includes(uid)),
      }));
      setSelectedAllowed([]);
    }
  };

  // Submit create or update request for channel
  const handleSubmit = async () => {
    setError('');
    const payload = {
      name: formData.name,
      allowed_users: formData.allowed_users,
    };
    try {
      if (editMode && selectedChannel) {
        await apiFetch(`/api/channels/${selectedChannel.uid}/`, {
          method: 'PUT',
          body: JSON.stringify(payload),
        });
      } else {
        await apiFetch('/api/channels/', {
          method: 'POST',
          body: JSON.stringify(payload),
        });
      }
      fetchChannels();
      handleClose();
    } catch (err) {
      setError(err.message || 'خطا در ذخیره کانال. لطفا ورودی‌ها را بررسی کنید.');
    }
  };

  // Delete channel by ID via API
  const handleDelete = async (channelId) => {
    setChannelToDelete(channelId);
    setDeleteConfirmOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!channelToDelete) return;
    
    setDeletingId(channelToDelete);
    setDeleteError('');
    setError('');
    try {
      await apiFetch(`/api/channels/${channelToDelete}/`, {
        method: 'DELETE',
      });
      fetchChannels();
    } catch (err) {
      setDeleteError(err.message || 'خطا در حذف کانال');
    } finally {
      setDeletingId(null);
      setDeleteConfirmOpen(false);
      setChannelToDelete(null);
    }
  };

  const handleDeleteCancel = () => {
    setDeleteConfirmOpen(false);
    setChannelToDelete(null);
  };

  // Dual list details
  const allowedUsersDetails = Array.isArray(users) 
    ? users.filter((u) => Array.isArray(formData.allowed_users) && formData.allowed_users.includes(u.uid))
          .filter((u) => u.username.toLowerCase().includes((allowedSearchQuery || '').toLowerCase()))
    : [];

  const availableUsersDetails = Array.isArray(users)
    ? users.filter((u) => !Array.isArray(formData.allowed_users) || !formData.allowed_users.includes(u.uid))
          .filter((u) => u.username.toLowerCase().includes((availableSearchQuery || '').toLowerCase()))
    : [];

  const renderChannels = () => {
    if (loadingChannels) {
      return (
        <TableRow>
          <TableCell colSpan={4} align="center">
            در حال بارگذاری...
          </TableCell>
        </TableRow>
      );
    }

    if (!Array.isArray(filteredChannels)) {
      return (
        <TableRow>
          <TableCell colSpan={4} align="center">
            خطا در بارگذاری کانال‌ها
          </TableCell>
        </TableRow>
      );
    }

    if (filteredChannels.length === 0) {
      return (
        <TableRow>
          <TableCell colSpan={4} align="center">
            هیچ کانالی یافت نشد
          </TableCell>
        </TableRow>
      );
    }

    return filteredChannels.map((channel) => (
      <TableRow key={channel.uid || crypto.randomUUID()}>
        <TableCell align="right">{channel.name}</TableCell>
        <TableCell align="center">{channel.allowed_users?.length || 0}</TableCell>
        <TableCell align="center">
          <IconButton color="primary" size="small" onClick={() => handleClickOpen(channel)}>
            <EditIcon />
          </IconButton>
          <IconButton color="error" size="small" onClick={() => handleDelete(channel.uid)} disabled={deletingId === channel.uid}>
            {deletingId === channel.uid ? '...' : <DeleteIcon />}
          </IconButton>
        </TableCell>
      </TableRow>
    ));
  };

  return (
    <Box sx={{ fontFamily: 'IRANSans, Vazirmatn, Roboto, Arial', fontSize: 15 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h5" sx={{ fontFamily: 'IRANSans, Vazirmatn, Roboto, Arial', fontSize: 24, fontWeight: 700 }} gutterBottom component="div">
          مدیریت کانال‌ها
        </Typography>
        <Button variant="contained" onClick={() => handleClickOpen()}>
          افزودن کانال جدید
        </Button>
      </Box>
      <TextField
        label="جستجوی کانال..."
        variant="outlined"
        size="small"
        fullWidth
        value={channelSearchQuery}
        onChange={(e) => setChannelSearchQuery(e.target.value)}
        sx={{ mb: 2 }}
      />
      {error && <Typography color="error" gutterBottom>{error}</Typography>}
      {deleteError && <Typography color="error" gutterBottom>{deleteError}</Typography>}
      <Paper sx={{ p: 2, mb: 2 }}>
        <TableContainer>
          <Table size="small" sx={{ '& .MuiTableCell-root': { fontFamily: 'IRANSans, Vazirmatn, Roboto, Arial', fontSize: 14, padding: '8px 16px' } }}>
            <TableHead>
              <TableRow>
                <TableCell align="right" sx={{ fontWeight: 'bold' }}>نام کانال</TableCell>
                <TableCell align="center" sx={{ fontWeight: 'bold' }}>تعداد کاربران</TableCell>
                <TableCell align="center" sx={{ fontWeight: 'bold' }}>اقدامات</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {renderChannels()}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>
      <Dialog open={open} onClose={handleClose} fullWidth maxWidth="sm" sx={{ '& .MuiDialog-paper': { width: 600, maxWidth: '600px' } }}>
        <DialogTitle sx={{ textAlign: 'right' }}>
          {editMode ? 'ویرایش کانال' : 'ایجاد کانال جدید'}
        </DialogTitle>
        <DialogContent sx={{ textAlign: 'right' }}>
          <TextField
            autoFocus
            margin="dense"
            name="name"
            label="نام کانال"
            type="text"
            fullWidth
            variant="outlined"
            value={formData.name}
            onChange={handleChange}
            sx={{ direction: 'rtl', mb: 2 }}
          />
          <Typography variant="h6" sx={{ mt: 2, mb: 1, textAlign: 'center' }}>
            مدیریت کاربران مجاز
          </Typography>
          <Grid container spacing={2} justifyContent="center" alignItems="flex-start">
            <Grid item xs={5}>
              <Typography variant="body2" sx={{ mb: 1, textAlign: 'center' }}>
                تمام کاربران
              </Typography>
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
                  {availableUsersDetails.map((user) => (
                    <ListItem
                      key={user.uid}
                      button
                      selected={selectedAvailable.includes(user.uid)}
                      onClick={() => setSelectedAvailable((prev) => prev.includes(user.uid) ? prev.filter((i) => i !== user.uid) : [...prev, user.uid])}
                      sx={selectedAvailable.includes(user.uid) ? { bgcolor: '#90caf9 !important' } : {}}
                    >
                      <ListItemText primary={user.username} sx={{ textAlign: 'center' }} />
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
              <Typography variant="body2" sx={{ mb: 1, textAlign: 'center' }}>
                کاربران مجاز
              </Typography>
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
                  {allowedUsersDetails.map((user) => (
                    <ListItem
                      key={user.uid}
                      button
                      selected={selectedAllowed.includes(user.uid)}
                      onClick={() => setSelectedAllowed((prev) => prev.includes(user.uid) ? prev.filter((i) => i !== user.uid) : [...prev, user.uid])}
                      sx={selectedAllowed.includes(user.uid) ? { bgcolor: '#90caf9 !important' } : {}}
                    >
                      <ListItemText primary={user.username} sx={{ textAlign: 'center' }} />
                    </ListItem>
                  ))}
                </List>
              </Paper>
            </Grid>
          </Grid>
        </DialogContent>
        {error && (
          <Typography color="error" sx={{ mt: 1, textAlign: 'center' }}>
            {error}
          </Typography>
        )}
        <DialogActions>
          <Button onClick={handleClose}>انصراف</Button>
          <Button onClick={handleSubmit} variant="contained" disabled={!formData.name.trim()}>
            {editMode ? 'ذخیره تغییرات' : 'ایجاد'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteConfirmOpen}
        onClose={handleDeleteCancel}
        aria-labelledby="delete-dialog-title"
      >
        <DialogTitle id="delete-dialog-title">تأیید حذف کانال</DialogTitle>
        <DialogContent>
          <Typography>
            آیا از حذف این کانال اطمینان دارید؟ این عمل غیرقابل بازگشت است.
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

export default ChannelManagement;
