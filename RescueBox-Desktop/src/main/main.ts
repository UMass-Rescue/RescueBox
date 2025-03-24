/* eslint global-require: off, no-console: off, promise/always-return: off */

/**
 * This module executes inside of electron's main process. You can start
 * electron renderer process from here and communicate with the other processes
 * through IPC.
 *
 * When running `npm run build` or `npm run build:main`, this file is compiled to
 * `./src/main.js` using webpack. This gives us some performance wins.
 */
import path from 'path';
import { app, BrowserWindow, shell, ipcMain } from 'electron';
import { autoUpdater } from 'electron-updater';
import log from 'electron-log/main';
import isDummyMode from 'src/shared/dummy_data/set_dummy_mode';
import MenuBuilder from './menu';
import { resolveHtmlPath } from './util';
import * as registration from './handlers/registration';
import * as job from './handlers/job';
import * as models from './handlers/models';
import * as fileSystem from './handlers/file-system';
import * as loggingHandler from './handlers/logging';
import * as taskHandler from './handlers/task';
import DatabaseConn, { getDbPath } from './database/database-conn';

// It preloads electron-log IPC code in renderer processes
log.initialize();

class AppUpdater {
  constructor() {
    log.transports.file.level = 'info';
    autoUpdater.logger = log;
    autoUpdater.checkForUpdatesAndNotify();
  }
}

let mainWindow: BrowserWindow | null = null;

// IPCMain Setup

function setupIpcMain() {
  // Database: access to reset database
  ipcMain.handle('database:reset-database', () => {
    if (isDummyMode) {
      return DatabaseConn.resetDummyData(getDbPath(app));
    }
    return DatabaseConn.resetDatabase(getDbPath(app));
  });
  // Registration: handles registering models
  ipcMain.handle(
    'register:register-model-app-ip',
    registration.registerModelAppIp,
  );
  ipcMain.handle(
    'register:unregister-model-app-ip',
    registration.unregisterModelAppIp,
  );
  ipcMain.handle(
    'register:get-model-app-status',
    registration.getModelAppStatus,
  );
  ipcMain.handle('register:get-model-servers', registration.getModelServers);
  ipcMain.handle('register:get-model-server', registration.getModelServer);

  // Models: handles registering models
  ipcMain.handle('models:get-models', models.getModels);
  ipcMain.handle('models:get-model-by-uid', models.getModelByUid);
  ipcMain.handle('models:remove-model-by-uid', models.removeModelByUid);

  // Job: handles creating jobs
  ipcMain.handle('job:get-jobs', job.getJobs);
  ipcMain.handle('job:get-job-by-id', job.getJobById);
  ipcMain.handle('job:run-job', job.runJob);
  ipcMain.handle('job:cancel-job', job.cancelJob);
  ipcMain.handle('job:delete-job-by-id', job.deleteJobById);

  // File System: handles file system operations
  ipcMain.handle('fileSystem:read-file', fileSystem.readFile);
  ipcMain.handle('fileSystem:open-path', fileSystem.openPath);
  ipcMain.handle(
    'fileSystem:show-file-in-explorer',
    fileSystem.showFileInExplorer,
  );
  ipcMain.handle('fileSystem:select-directory', fileSystem.selectDirectory);
  ipcMain.handle('fileSystem:select-directories', fileSystem.selectDirectories);
  ipcMain.handle('fileSystem:select-file', fileSystem.selectFile);
  ipcMain.handle('fileSystem:select-files', fileSystem.selectFiles);
  ipcMain.handle('fileSystem:select-file-save', fileSystem.selectFileSave);
  ipcMain.handle('fileSystem:save-logs', fileSystem.saveLogs);
  ipcMain.handle('fileSystem:get-files-from-dir', fileSystem.getFilesFromDir);
  ipcMain.handle('fileSystem:delete-file', fileSystem.deleteFile);
  ipcMain.handle('fileSystem:get-file-icon', fileSystem.getFileIcon);
  ipcMain.handle('fileSystem:join-path', fileSystem.joinPath);

  // Logging: handles logging operations
  ipcMain.handle('logging:get-logs', loggingHandler.getLogs);
  ipcMain.handle('logging:clear-logs', loggingHandler.clearLogs);

  // Task: handles task service operations
  ipcMain.handle('task:get-api-routes', taskHandler.getApiRoutes);
  ipcMain.handle('task:get-app-metadata', taskHandler.getAppMetadata);
  ipcMain.handle('task:get-task-schema', taskHandler.getTaskSchema);
  ipcMain.handle(
    'task:get-task-by-model-uid-and-task-id',
    taskHandler.getTaskByModelUidAndTaskId,
  );
}

if (process.env.NODE_ENV === 'production') {
  const sourceMapSupport = require('source-map-support');
  sourceMapSupport.install();
}

const isDebug =
  process.env.NODE_ENV === 'development' || process.env.DEBUG_PROD === 'true';

if (isDebug) {
  require('electron-debug')();
}

const installExtensions = async () => {
  const installer = require('electron-devtools-installer');
  const forceDownload = !!process.env.UPGRADE_EXTENSIONS;
  const extensions = ['REACT_DEVELOPER_TOOLS'];

  return installer
    .default(
      extensions.map((name) => installer[name]),
      forceDownload,
    )
    .catch(console.log);
};

/**
 * Window Management ...
 */

const createWindow = async () => {
  if (isDebug) {
    await installExtensions();
  }

  const RESOURCES_PATH = app.isPackaged
    ? path.join(process.resourcesPath, 'assets')
    : path.join(__dirname, '../../assets');

  const getAssetPath = (...paths: string[]): string => {
    return path.join(RESOURCES_PATH, ...paths);
  };

  mainWindow = new BrowserWindow({
    titleBarStyle: 'hidden',
    titleBarOverlay: {
      color: '#374151',
      symbolColor: '#ffffff',
      height: 30,
    },
    trafficLightPosition: {
      x: 10,
      y: 8,
    },
    show: false,
    width: 1024,
    height: 728,
    icon: getAssetPath('icon.png'),
    webPreferences: {
      preload: app.isPackaged
        ? path.join(__dirname, 'preload.js')
        : path.join(__dirname, '../../.erb/dll/preload.js'),
      webSecurity: process.env.NODE_ENV !== 'development',
    },
  });

  mainWindow.loadURL(resolveHtmlPath('index.html'));

  mainWindow.on('ready-to-show', () => {
    if (!mainWindow) {
      throw new Error('"mainWindow" is not defined');
    }
    if (process.env.START_MINIMIZED) {
      mainWindow.minimize();
    } else {
      mainWindow.show();
    }
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  const menuBuilder = new MenuBuilder(mainWindow);
  menuBuilder.buildMenu();

  // Open urls in the user's browser
  mainWindow.webContents.setWindowOpenHandler((edata) => {
    shell.openExternal(edata.url);
    return { action: 'deny' };
  });

  // Remove this if your app does not use auto updates
  // eslint-disable-next-line
  new AppUpdater();
};

/**
 * Add event listeners...
 */

app.on('window-all-closed', () => {
  // Respect the OSX convention of having the application in memory even
  // after all windows have been closed
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

if (process.env.NODE_ENV === 'development') {
  app.setAppUserModelId(process.execPath);
}

app
  .whenReady()
  .then(async () => {
    setupIpcMain();
    const dbPath = getDbPath(app);
    log.info('Database location is', dbPath);
    if (isDummyMode) {
      log.info('Initializing dummy data');
      await DatabaseConn.initDatabaseTest(dbPath);
    } else {
      log.info('Initializing database');
      await DatabaseConn.initDatabase(dbPath);
      // await DatabaseConn.resetDatabase(dbPath); // For testing purposes only
    }
    createWindow();
    app.on('activate', () => {
      // On macOS it's common to re-create a window in the app when the
      // dock icon is clicked and there are no other windows open.
      console.log('Activating app');
      if (mainWindow === null) createWindow();
    });
  })
  .catch(console.log);
