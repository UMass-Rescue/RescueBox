/* eslint import/prefer-default-export: off */
import { URL } from 'url';
import path from 'path';
import { Model } from 'sequelize';
import { InferAttributes } from 'sequelize/types/model';
import { app, Notification, BrowserWindow } from 'electron';

export function resolveHtmlPath(htmlFileName: string) {
  if (process.env.NODE_ENV === 'development') {
    const port = process.env.PORT || 1212;
    const url = new URL(`http://localhost:${port}`);
    url.pathname = htmlFileName;
    return url.href;
  }
  return `file://${path.resolve(__dirname, '../renderer/', htmlFileName)}`;
}

export function getRaw<T extends Model>(
  model: T | null,
): InferAttributes<T> | null {
  if (!model) {
    return null;
  }
  return model.get({ plain: true, clone: true });
}

export function showNotification(
  title: string,
  body: string,
  navigateTo: string,
) {
  const icon = app.isPackaged
    ? path.join(process.resourcesPath, 'assets')
    : path.join(__dirname, '../../assets');
  new Notification({
    title,
    body,
    icon,
  })
    .on('click', () => {
      const window = BrowserWindow.getAllWindows()[0];
      window.moveTop();
      window.focus();
      window.webContents.send('navigate-to', navigateTo);
    })
    .show();
}
