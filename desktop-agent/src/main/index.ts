import { app, BrowserWindow, ipcMain } from 'electron';
import * as path from 'path';
import { FileWatcher } from './fileWatcher';
import { ApiClient } from './apiClient';
import Store from 'electron-store';

const store = new Store();
let mainWindow: BrowserWindow | null = null;
let fileWatcher: FileWatcher | null = null;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 900,
    height: 700,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
    },
  });

  // Load the index.html
  mainWindow.loadFile(path.join(__dirname, '../renderer/index.html'));

  // Open DevTools in development
  if (process.env.NODE_ENV === 'development') {
    mainWindow.webContents.openDevTools();
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

app.whenReady().then(() => {
  createWindow();

  // Initialize file watcher with stored configuration
  const watchFolders = store.get('watchFolders', []) as string[];
  const apiUrl = store.get('apiUrl', 'http://localhost:8000') as string;
  const authToken = store.get('authToken', '') as string;

  if (watchFolders.length > 0 && authToken) {
    fileWatcher = new FileWatcher(watchFolders, apiUrl, authToken);
    fileWatcher.start();
  }

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    fileWatcher?.stop();
    app.quit();
  }
});

// IPC Handlers
ipcMain.handle('get-config', () => {
  return {
    apiUrl: store.get('apiUrl', 'http://localhost:8000'),
    authToken: store.get('authToken', ''),
    watchFolders: store.get('watchFolders', []),
  };
});

ipcMain.handle('save-config', (_event, config) => {
  store.set('apiUrl', config.apiUrl);
  store.set('authToken', config.authToken);
  store.set('watchFolders', config.watchFolders);

  // Restart file watcher
  if (fileWatcher) {
    fileWatcher.stop();
  }
  fileWatcher = new FileWatcher(config.watchFolders, config.apiUrl, config.authToken);
  fileWatcher.start();

  return { success: true };
});

ipcMain.handle('add-watch-folder', (_event, folderPath: string) => {
  const folders = store.get('watchFolders', []) as string[];
  if (!folders.includes(folderPath)) {
    folders.push(folderPath);
    store.set('watchFolders', folders);
  }
  return { success: true, folders };
});

ipcMain.handle('remove-watch-folder', (_event, folderPath: string) => {
  const folders = store.get('watchFolders', []) as string[];
  const filtered = folders.filter(f => f !== folderPath);
  store.set('watchFolders', filtered);
  return { success: true, folders: filtered };
});

ipcMain.handle('get-logs', () => {
  return store.get('logs', []);
});

ipcMain.handle('clear-logs', () => {
  store.set('logs', []);
  return { success: true };
});

