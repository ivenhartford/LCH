import React, { useState } from 'react';
import {
  Container,
  Paper,
  Typography,
  Box,
  Tab,
  Tabs,
  TextField,
  Button,
  Alert,
  Divider,
  Grid,
} from '@mui/material';
import { Person as PersonIcon, Lock as LockIcon } from '@mui/icons-material';

function TabPanel({ children, value, index, ...other }) {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`settings-tabpanel-${index}`}
      aria-labelledby={`settings-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const Settings = ({ user }) => {
  const [tabValue, setTabValue] = useState(0);

  // Profile state
  const [profileData, setProfileData] = useState({
    username: user?.username || '',
    email: user?.email || '',
    first_name: user?.first_name || '',
    last_name: user?.last_name || '',
  });
  const [profileMessage, setProfileMessage] = useState(null);

  // Password state
  const [passwordData, setPasswordData] = useState({
    current_password: '',
    new_password: '',
    confirm_password: '',
  });
  const [passwordMessage, setPasswordMessage] = useState(null);
  const [passwordError, setPasswordError] = useState(null);

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
    // Clear messages when switching tabs
    setProfileMessage(null);
    setPasswordMessage(null);
    setPasswordError(null);
  };

  const handleProfileChange = (e) => {
    setProfileData({
      ...profileData,
      [e.target.name]: e.target.value,
    });
  };

  const handleProfileSubmit = async (e) => {
    e.preventDefault();
    setProfileMessage(null);

    try {
      const response = await fetch('/api/user/profile', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(profileData),
      });

      if (response.ok) {
        setProfileMessage({ type: 'success', text: 'Profile updated successfully!' });
      } else {
        const error = await response.json();
        setProfileMessage({ type: 'error', text: error.message || 'Failed to update profile' });
      }
    } catch (error) {
      setProfileMessage({ type: 'error', text: 'An error occurred while updating profile' });
    }
  };

  const handlePasswordChange = (e) => {
    setPasswordData({
      ...passwordData,
      [e.target.name]: e.target.value,
    });
    // Clear error when user types
    setPasswordError(null);
  };

  const handlePasswordSubmit = async (e) => {
    e.preventDefault();
    setPasswordMessage(null);
    setPasswordError(null);

    // Validation
    if (passwordData.new_password !== passwordData.confirm_password) {
      setPasswordError('New passwords do not match');
      return;
    }

    if (passwordData.new_password.length < 8) {
      setPasswordError('Password must be at least 8 characters long');
      return;
    }

    try {
      const response = await fetch('/api/user/change-password', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          current_password: passwordData.current_password,
          new_password: passwordData.new_password,
        }),
      });

      if (response.ok) {
        setPasswordMessage({ type: 'success', text: 'Password changed successfully!' });
        // Clear form
        setPasswordData({
          current_password: '',
          new_password: '',
          confirm_password: '',
        });
      } else {
        const error = await response.json();
        setPasswordError(error.message || 'Failed to change password');
      }
    } catch (error) {
      setPasswordError('An error occurred while changing password');
    }
  };

  return (
    <Container maxWidth="md" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        Settings
      </Typography>

      <Paper sx={{ mt: 3 }}>
        <Tabs
          value={tabValue}
          onChange={handleTabChange}
          aria-label="settings tabs"
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          <Tab
            icon={<PersonIcon />}
            label="Profile"
            id="settings-tab-0"
            aria-controls="settings-tabpanel-0"
          />
          <Tab
            icon={<LockIcon />}
            label="Password"
            id="settings-tab-1"
            aria-controls="settings-tabpanel-1"
          />
        </Tabs>

        {/* Profile Tab */}
        <TabPanel value={tabValue} index={0}>
          <Typography variant="h6" gutterBottom>
            Profile Information
          </Typography>
          <Divider sx={{ mb: 3 }} />

          {profileMessage && (
            <Alert severity={profileMessage.type} sx={{ mb: 2 }}>
              {profileMessage.text}
            </Alert>
          )}

          <form onSubmit={handleProfileSubmit}>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Username"
                  name="username"
                  value={profileData.username}
                  onChange={handleProfileChange}
                  disabled
                  helperText="Username cannot be changed"
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Email"
                  name="email"
                  type="email"
                  value={profileData.email}
                  onChange={handleProfileChange}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="First Name"
                  name="first_name"
                  value={profileData.first_name}
                  onChange={handleProfileChange}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Last Name"
                  name="last_name"
                  value={profileData.last_name}
                  onChange={handleProfileChange}
                />
              </Grid>
              <Grid item xs={12}>
                <Box sx={{ mt: 2 }}>
                  <Button type="submit" variant="contained" color="primary">
                    Save Changes
                  </Button>
                </Box>
              </Grid>
            </Grid>
          </form>
        </TabPanel>

        {/* Password Tab */}
        <TabPanel value={tabValue} index={1}>
          <Typography variant="h6" gutterBottom>
            Change Password
          </Typography>
          <Divider sx={{ mb: 3 }} />

          {passwordMessage && (
            <Alert severity={passwordMessage.type} sx={{ mb: 2 }}>
              {passwordMessage.text}
            </Alert>
          )}

          {passwordError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {passwordError}
            </Alert>
          )}

          <form onSubmit={handlePasswordSubmit}>
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Current Password"
                  name="current_password"
                  type="password"
                  value={passwordData.current_password}
                  onChange={handlePasswordChange}
                  required
                  autoComplete="current-password"
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="New Password"
                  name="new_password"
                  type="password"
                  value={passwordData.new_password}
                  onChange={handlePasswordChange}
                  required
                  helperText="Must be at least 8 characters long"
                  autoComplete="new-password"
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Confirm New Password"
                  name="confirm_password"
                  type="password"
                  value={passwordData.confirm_password}
                  onChange={handlePasswordChange}
                  required
                  autoComplete="new-password"
                />
              </Grid>
              <Grid item xs={12}>
                <Box sx={{ mt: 2 }}>
                  <Button type="submit" variant="contained" color="primary">
                    Change Password
                  </Button>
                </Box>
              </Grid>
            </Grid>
          </form>
        </TabPanel>
      </Paper>

      <Box sx={{ mt: 3 }}>
        <Typography variant="body2" color="text.secondary">
          <strong>Role:</strong> {user?.role || 'User'}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          <strong>Last Login:</strong>{' '}
          {user?.last_login ? new Date(user.last_login).toLocaleString() : 'N/A'}
        </Typography>
      </Box>
    </Container>
  );
};

export default Settings;
