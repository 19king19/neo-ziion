import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import NexusApp from './App.jsx';

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <NexusApp />
  </StrictMode>,
);
