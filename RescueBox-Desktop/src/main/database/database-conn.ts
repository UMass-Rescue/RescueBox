/* eslint-disable no-use-before-define */
import { Sequelize } from 'sequelize';
import Main from 'electron/main';
import path from 'path';
import log from 'electron-log/main';
import SQLiteDB from './sqlite-db';
import getMigrationsUmzug from './migrations/umzug';

export function getDbPath(app: Main.App): string {
  return path.join(app.getPath('userData'), 'rbox-data.db');
}

export default class DatabaseConn {
  private db: SQLiteDB;

  static #instance: DatabaseConn | null = null;

  constructor(dbPath: string) {
    const sequelize = new Sequelize({
      dialect: 'sqlite',
      storage: dbPath,
      logging: false,
    });

    const umzug = getMigrationsUmzug(sequelize);
    this.db = new SQLiteDB(sequelize, umzug);
  }

  static async initDatabase(dbPath: string): Promise<void> {
    if (!DatabaseConn.#instance) {
      DatabaseConn.#instance = new DatabaseConn(dbPath);
      await DatabaseConn.#instance.db.connect();
    }
  }

  static async resetDatabase(dbPath: string): Promise<void> {
    if (!DatabaseConn.#instance) {
      DatabaseConn.#instance = new DatabaseConn(dbPath);
    }
    await DatabaseConn.#instance.db.connect();
    log.info('Resetting database');
    return DatabaseConn.#instance.db.resetTables();
  }

  static async resetDummyData(dbPath: string): Promise<void> {
    if (!DatabaseConn.#instance) {
      DatabaseConn.#instance = new DatabaseConn(dbPath);
    }
    log.info('Resetting dummy data');
    await DatabaseConn.#instance.db.connect();
    return DatabaseConn.#instance.db.resetDummyData();
  }

  static async initDatabaseTest(dbPath: string): Promise<void> {
    if (!DatabaseConn.#instance) {
      DatabaseConn.#instance = new DatabaseConn(dbPath);
      await DatabaseConn.#instance.db.connect();
      await DatabaseConn.#instance.db.clearDummyData();
      await DatabaseConn.#instance.db.initDummyData();
    }
  }
}
