import { QueryInterface, DataTypes } from 'sequelize';

const TABLE_NAME = 'mlmodels';
const MIGRATION_NAME = '0011_models_revise_schema_removed';

const migration0011ModelsAddIsRemoved = {
  name: MIGRATION_NAME,
  async up({ context: queryInterface }: { context: QueryInterface }) {
    await queryInterface.addColumn(TABLE_NAME, 'isRemoved', {
      type: DataTypes.BOOLEAN,
      allowNull: false,
      defaultValue: false,
    });
  },

  async down({ context: queryInterface }: { context: QueryInterface }) {
    await queryInterface.removeColumn(TABLE_NAME, 'isRemoved');
  },
};

export default migration0011ModelsAddIsRemoved;
