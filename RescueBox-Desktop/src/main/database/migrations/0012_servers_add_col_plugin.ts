import { QueryInterface, DataTypes } from 'sequelize';

const TABLE_NAME = 'servers';
const MIGRATION_NAME = '0012_servers_add_col_plugin';

const migration0012ServersAddColPlugin = {
  name: MIGRATION_NAME,
  async up({ context: queryInterface }: { context: QueryInterface }) {
    await queryInterface.addColumn(TABLE_NAME, 'pluginName', DataTypes.STRING);
  },
  async down({ context: queryInterface }: { context: QueryInterface }) {
    await queryInterface.removeColumn(TABLE_NAME, 'pluginName');
  },
};

export default migration0012ServersAddColPlugin;
