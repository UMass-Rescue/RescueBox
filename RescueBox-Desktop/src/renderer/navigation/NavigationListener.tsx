import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import log from 'electron-log/renderer';

export default function NavigationListener() {
  const navigate = useNavigate();

  useEffect(() => {
    if (window.electronAPI === undefined) {
      log.error('Electron API handler is not defined.');
      return () => {};
    }

    window.electronAPI.onNavigate((page) => {
      navigate(page);
    });

    return () => {
      window.electronAPI?.offNavigate();
    };
  }, [navigate]);

  return null;
}
