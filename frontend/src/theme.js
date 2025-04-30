import { createTheme } from '@mui/material/styles';

const theme = createTheme({
  direction: 'rtl',
  palette: {
    primary: { main: '#3f51b5' },
    secondary: { main: '#f50057' },
    background: { default: '#f4f6f8', paper: '#ffffff' }
  },
  shape: { borderRadius: 8 },
  typography: {
    fontFamily: 'Vazirmatn',
    button: { textTransform: 'none', fontWeight: 500 },
    h6: { fontWeight: 600 },
  },
  components: {
    MuiAppBar: {
      defaultProps: { elevation: 2, color: 'primary' }
    },
    MuiButton: {
      defaultProps: { disableElevation: true, variant: 'contained', color: 'primary' }
    },
    MuiPaper: {
      defaultProps: { elevation: 1 },
      styleOverrides: { rounded: { borderRadius: 8 } }
    },
    MuiTextField: {
      defaultProps: {
        inputProps: {
          style: { textAlign: 'right' }
        }
      }
    },
    MuiDialog: {
      defaultProps: {
        PaperProps: {
          style: { direction: 'rtl' }
        }
      }
    }
  }
});

export default theme;
