import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import './DocumentUpload.css';

const API_BASE_URL = 'http://localhost:3001';

const DocumentUpload = ({ onUpload }) => {
  const [uploadStatus, setUploadStatus] = useState(null);
  const [error, setError] = useState(null);

  const onDrop = useCallback(async (acceptedFiles) => {
    setError(null);
    setUploadStatus('uploading');

    const formData = new FormData();
    const file = acceptedFiles[0];
    
    // Validate file type
    const allowedTypes = ['application/pdf', 'application/json', 'text/plain'];
    if (!allowedTypes.includes(file.type)) {
      setError('Invalid file type. Please upload PDF, JSON, or TXT files only.');
      setUploadStatus(null);
      return;
    }

    formData.append('file', file);

    try {
      const response = await fetch(`${API_BASE_URL}/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Upload failed');
      }

      const data = await response.json();
      setUploadStatus('success');
      if (onUpload) {
        onUpload(data);
      }
    } catch (err) {
      setError(err.message || 'Failed to upload file. Please try again.');
      setUploadStatus('error');
    }
  }, [onUpload]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/json': ['.json'],
      'text/plain': ['.txt']
    },
    multiple: false
  });

  return (
    <div className="document-upload">
      <div 
        {...getRootProps()} 
        className={`dropzone ${isDragActive ? 'active' : ''} ${uploadStatus}`}
      >
        <input {...getInputProps()} />
        {isDragActive ? (
          <p>Drop the file here...</p>
        ) : (
          <div className="upload-content">
            <i className="fas fa-cloud-upload-alt"></i>
            <p>Drag and drop a file here, or click to select</p>
            <p className="file-types">Supported formats: PDF, JSON, TXT</p>
          </div>
        )}
      </div>
      
      {error && <div className="error-message">{error}</div>}
      
      {uploadStatus === 'success' && (
        <div className="success-message">
          File uploaded successfully!
        </div>
      )}
    </div>
  );
};

export default DocumentUpload; 