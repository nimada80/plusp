/*
 * ChannelManagement.js
 * React component for listing, creating, editing, and deleting channels.
 * Supports dual-list user assignment and CSRF-protected API calls.
 */

import React, { useState, useEffect } from 'react';
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
  IconButton,
  Typography,
  Paper,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import EditIcon from '@mui/icons-material/Edit';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

// Helper to read CSRF token cookie
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
      cookie = cookie.trim();
      if (cookie.startsWith(name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

/**
 * apiFetch
 * Wraps fetch to include CSRF token and error handling.
 * @param {string} url - API endpoint path starting with '/api'
 * @param {object} options - fetch options (method, headers, body)
 * @returns {object|null} JSON response or null for 204
 * @throws {Error} on network or server error
 */
const apiFetch = async (url, options = {}) => {
  const defaultOptions = {
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
  };
  const mergedOptions = {
    ...defaultOptions,
    ...options,
    headers: {
      ...defaultOptions.headers,
      ...options.headers,
    },
  };
  // Attach CSRF token
  const csrftoken = getCookie('csrftoken');
  if (csrftoken) mergedOptions.headers['X-CSRFToken'] = csrftoken;

  const response = await fetch(`${API_BASE_URL}${url}`, mergedOptions);

  if (!response.ok) {
    const errorBody = await response.text();
    console.error('API Fetch Error:', response.status, errorBody);
    throw new Error(`خطا در ارتباط با سرور: ${response.status} ${response.statusText}`);
  }

  if (response.status === 204 || response.headers.get('content-length') === '0') {
    return null;
  }

  try {
    return await response.json();
  } catch (e) {
    console.error('Failed to parse JSON response:', e);
    throw new Error('پاسخ دریافتی از سرور معتبر نبود.');
  }
};

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
    authorized_users: [],
  });

  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [channelToDelete, setChannelToDelete] = useState(null);

  // Fetch all channels from backend
  const fetchChannels = async () => {
    setLoadingChannels(true);
    setError('');
    try {
      const data = await apiFetch('/api/channels/');
      setChannels(data || []);
    } catch (err) {
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
      setUsers(data || []);
    } catch (err) {
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
        authorized_users: Array.isArray(channel.authorized_users) ? channel.authorized_users : [],
      });
    } else {
      setEditMode(false);
      setSelectedChannel(null);
      setFormData({
        name: '',
        authorized_users: [],
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
        authorized_users: [...new Set([...prev.authorized_users, ...selectedAvailable])],
      }));
      setSelectedAvailable([]);
    } else if (direction === 'left' && selectedAllowed.length > 0) {
      setFormData((prev) => ({
        ...prev,
        authorized_users: prev.authorized_users.filter((uid) => !selectedAllowed.includes(uid)),
      }));
      setSelectedAllowed([]);
    }
  };

  // Submit create or update request for channel
  const handleSubmit = async () => {
    setError('');
    const payload = {
      name: formData.name,
      authorized_users: formData.authorized_users,
    };
    try {
      if (editMode && selectedChannel) {
        await apiFetch(`/api/channels/${selectedChannel.id}/`, {
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
  const allowedUsersDetails = users.filter((u) => formData.authorized_users.includes(u.id)).filter((u) =>
    u.username.toLowerCase().includes(allowedSearchQuery.toLowerCase())
  );
  const availableUsersDetails = users.filter((u) => !formData.authorized_users.includes(u.id)).filter((u) =>
    u.username.toLowerCase().includes(availableSearchQuery.toLowerCase())
  );

  // Table filter
  const filteredChannels = channels.filter((c) => c.name.toLowerCase().includes(channelSearchQuery.toLowerCase()));

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
          <Table size="small">
            <TableHead>
              <TableRow sx={{ fontSize: 15 }}>
                <TableCell align="right" sx={{ fontSize: 15 }}>نام کانال</TableCell>
                <TableCell align="center" sx={{ fontSize: 15 }}>اقدامات</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredChannels.map((channel) => (
                <TableRow sx={{ fontSize: 15 }} key={channel.id} hover>
                  <TableCell align="right" sx={{ fontSize: 15 }}>{channel.name}</TableCell>
                  <TableCell align="center" sx={{ fontSize: 15 }}>
                    <IconButton color="primary" size="small" onClick={() => handleClickOpen(channel)}>
                      <EditIcon />
                    </IconButton>
                    <IconButton color="error" size="small" onClick={() => handleDelete(channel.id)}>
                      <DeleteIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))}
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
                      key={user.id}
                      button
                      selected={selectedAvailable.includes(user.id)}
                      onClick={() => setSelectedAvailable((prev) => prev.includes(user.id) ? prev.filter((i) => i !== user.id) : [...prev, user.id])}
                      sx={selectedAvailable.includes(user.id) ? { bgcolor: '#90caf9 !important' } : {}}
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
                      key={user.id}
                      button
                      selected={selectedAllowed.includes(user.id)}
                      onClick={() => setSelectedAllowed((prev) => prev.includes(user.id) ? prev.filter((i) => i !== user.id) : [...prev, user.id])}
                      sx={selectedAllowed.includes(user.id) ? { bgcolor: '#90caf9 !important' } : {}}
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
