import { dialog, shell, app } from 'electron';
import fs from 'fs';
import log from 'electron-log/main';
import path from 'path';

export type PathArgs = {
  path: string;
  enclosingDirectory?: string;
};

export type JoinPathArgs = {
  paths: string[];
};

function getPathString(arg: PathArgs) {
  let pathString = arg.path;
  if (arg.enclosingDirectory) {
    pathString = path.join(arg.enclosingDirectory, arg.path);
  }
  return pathString;
}

export type NewFileArgs = {
  defaultName: string;
  defaultExtension: string;
  allowedExtensions: '*' | string[];
};

export async function readFile(_event: any, arg: PathArgs) {
  const pathString = getPathString(arg);
  if (!fs.existsSync(pathString)) {
    log.error('File does not exist');
    dialog.showErrorBox(
      "We can't find this file.",
      "Make sure it hasn't been moved or deleted.",
    );
    return '';
  }
  return fs.readFileSync(pathString).toString();
}

export async function openPath(_event: any, arg: PathArgs) {
  const pathString = getPathString(arg);
  log.info('Opening file/directory', pathString);
  if (!fs.existsSync(pathString)) {
    log.error('Directory does not exist');
    dialog.showErrorBox(
      "We can't find this folder.",
      "Make sure it hasn't been moved or deleted.",
    );
  } else {
    shell.openPath(pathString).catch((err) => {
      log.error('Error opening directory', err);
      dialog.showErrorBox('Error opening directory', err.message);
    });
  }
}

export async function showFileInExplorer(_event: any, arg: PathArgs) {
  const pathString = getPathString(arg);
  const filePath = path.resolve(pathString);
  if (!fs.existsSync(filePath)) {
    log.error('File does not exist');
    dialog.showErrorBox(
      "We can't find this file.",
      "Make sure it hasn't been moved or deleted.",
    );
  } else {
    log.info('Showing file in explorer', filePath);
    shell.showItemInFolder(filePath);
  }
}

export async function deleteFile(_event: any, arg: PathArgs) {
  const pathString = getPathString(arg);
  const filePath = path.resolve(pathString);
  if (!fs.existsSync(filePath)) {
    log.error('File does not exist');
    dialog.showErrorBox(
      "We can't find this file.",
      "Make sure it hasn't been moved or deleted.",
    );
  } else {
    log.info('Deleting file', filePath);
    await shell.trashItem(filePath).catch((err) => {
      log.error('Error deleting file', err);
      dialog.showErrorBox('Error deleting file', err.message);
    });
  }
}

export async function joinPath(_event: any, arg: JoinPathArgs) {
  return path.join(...arg.paths);
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
export async function selectDirectory(_event: any, _arg: any) {
  const result = await dialog.showOpenDialog({
    properties: ['openDirectory'],
  });

  return result.filePaths[0];
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
export async function selectDirectories(_event: any, _arg: any) {
  const result = await dialog.showOpenDialog({
    properties: ['openDirectory', 'multiSelections'],
  });

  return result.filePaths;
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
export async function selectFile(_event: any, _arg: any) {
  const result = await dialog.showOpenDialog({
    properties: ['openFile'],
  });

  return result.filePaths[0];
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
export async function selectFiles(_event: any, _arg: any) {
  const result = await dialog.showOpenDialog({
    properties: ['openFile', 'multiSelections'],
  });

  return result.filePaths;
}

export async function selectFileSave(_event: any, arg: NewFileArgs) {
  const filters = [];
  if (arg.allowedExtensions !== '*') {
    filters.push(
      ...arg.allowedExtensions.map((ext) => ({
        name: ext,
        extensions: [ext],
      })),
    );
  } else {
    filters.push({ name: 'All Files', extensions: ['*'] });
  }

  if (
    arg.allowedExtensions !== '*' &&
    !arg.allowedExtensions.includes(arg.defaultExtension)
  ) {
    filters.push({
      name: arg.defaultExtension,
      extensions: [arg.defaultExtension],
    });
  }
  return dialog
    .showSaveDialog({
      title: 'Select New File Path',
      defaultPath: arg.defaultName,
      buttonLabel: 'Confirm',
      filters,
      properties: [],
    })
    .then((file) => {
      log.info(
        file.canceled ? 'Dialog was canceled' : 'Dialog was not canceled',
      );
      if (!file.canceled) {
        log.info('File path selected to save: ', file.filePath);
      }
      return file.filePath;
    })
    .catch((err) => {
      log.error('Error in obtaining file path: ', err);
    });
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
export async function saveLogs(_event: any, _arg: any) {
  return dialog
    .showSaveDialog({
      title: 'Select the File Path to save',
      defaultPath: `rescuebox-logs-${new Date().toISOString()}.log`,
      buttonLabel: 'Save',
      // Restricting the user to only Text Files.
      filters: [
        {
          name: 'Text Files',
          extensions: ['log'],
        },
      ],
      properties: [],
    })
    .then((file) => {
      // Stating whether dialog operation was cancelled or not.
      log.info(
        file.canceled ? 'Dialog was canceled' : 'Dialog was not canceled',
      );
      if (!file.canceled) {
        log.info('File path selected to save logs: ', file.filePath);

        fs.copyFileSync(log.transports.file.getFile().path, file.filePath);
        log.info('File saved successfully');
      }
      return file.filePath;
    })
    .catch((err) => {
      log.error('Error in saving logs: ', err);
    });
}

export type FileInfo = {
  fullPath: string;
  fileName: string;
  parent: string;
};

export async function getFilesFromDir(_event: any, arg: PathArgs) {
  const files = fs.readdirSync(arg.path);
  return files.map((file) => ({
    fullPath: path.join(arg.path, file),
    fileName: file,
    parent: arg.path,
  }));
}

export async function getFileIcon(_event: any, arg: PathArgs) {
  const iconImg = await app.getFileIcon(arg.path);
  return iconImg.toDataURL();
}
