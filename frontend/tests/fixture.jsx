import React from 'react';
import {createRoot} from 'react-dom/client';
import App from '../src/App.jsx';
import '../src/styles.css';

window.testRequests = [];
window.modelRequests = 0;
window.testErrors = [];
window.addEventListener('error', event => window.testErrors.push(event.message));
window.addEventListener('unhandledrejection', event => window.testErrors.push(String(event.reason)));
const originalFetch = window.fetch.bind(window);
window.referenceFetch = originalFetch;
window.fetch = async (url, options) => {
  window.testRequests.push({url: String(url), method: options?.method ?? 'GET', body: options?.body ?? null});
  if (String(url).includes('/models/milestone3/')) {
    window.modelRequests++;
    if (window.modelRequests === 1) return new Response('', {status: 503});
  }
  return originalFetch(url, options);
};
createRoot(document.getElementById('root')).render(<App/>);
