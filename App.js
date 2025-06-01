import React, { useState } from 'react';
import { 
  Container, 
  Box, 
  Typography, 
  Paper, 
  Alert,
  CircularProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Button
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import RefreshIcon from '@mui/icons-material/Refresh';
import DocumentUpload from './components/DocumentUpload';

const API_BASE_URL = 'http://localhost:3001';

function App() {
  const [uploadStatus, setUploadStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState(null);
  const [response, setResponse] = useState(null);
  const [error, setError] = useState(null);

  const resetState = () => {
    setUploadStatus(null);
    setAnalysis(null);
    setResponse(null);
    setError(null);
  };

  const checkBackendHealth = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/health`);
      if (!response.ok) {
        throw new Error('Backend service is not responding properly');
      }
      return true;
    } catch (error) {
      console.error('Health check failed:', error);
      throw new Error('Backend service is not available. Please make sure the backend server is running.');
    }
  };

  const handleUpload = async (data) => {
    setLoading(true);
    resetState();

    try {
      setUploadStatus({
        type: 'success',
        message: 'Document uploaded and processed successfully!'
      });
      setAnalysis(data.analysis);
      setResponse(data.response);
    } catch (error) {
      console.error('Upload error:', error);
      const errorMessage = error.message || 'Error uploading document. Please try again.';
      setError(errorMessage);
      setUploadStatus({
        type: 'error',
        message: errorMessage
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="md">
      <Box sx={{ my: 4 }}>
        <Typography variant="h3" component="h1" gutterBottom align="center">
          Document Upload System
        </Typography>
        <Typography variant="h6" gutterBottom align="center" color="text.secondary">
          Upload your documents for processing with Perplexity
        </Typography>
        
        <Paper elevation={3} sx={{ p: 4, mt: 4 }}>
          <DocumentUpload onUpload={handleUpload} />
          
          {loading && (
            <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
              <CircularProgress />
            </Box>
          )}

          {uploadStatus && (
            <Alert 
              severity={uploadStatus.type} 
              sx={{ mt: 2 }}
              action={
                uploadStatus.type === 'error' && (
                  <Button 
                    color="inherit" 
                    size="small" 
                    startIcon={<RefreshIcon />}
                    onClick={resetState}
                  >
                    Try Again
                  </Button>
                )
              }
            >
              {uploadStatus.message}
            </Alert>
          )}

          {error && (
            <Alert severity="error" sx={{ mt: 2 }}>
              <Typography variant="body2">
                Error Details: {error}
              </Typography>
            </Alert>
          )}

          {analysis && (
            <Accordion sx={{ mt: 2 }}>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography>Document Analysis</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Typography style={{ whiteSpace: 'pre-wrap' }}>
                  {analysis}
                </Typography>
              </AccordionDetails>
            </Accordion>
          )}

          {response && (
            <Accordion sx={{ mt: 2 }}>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography>Processed Response</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Typography style={{ whiteSpace: 'pre-wrap' }}>
                  {response}
                </Typography>
              </AccordionDetails>
            </Accordion>
          )}
        </Paper>
      </Box>
    </Container>
  );
}

export default App; 