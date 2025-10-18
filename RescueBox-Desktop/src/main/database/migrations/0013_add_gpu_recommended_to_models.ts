import { DataTypes, QueryInterface } from 'sequelize';

const TABLE_NAME = 'mlmodels';
const MIGRATION_NAME = '0013_add_gpu_recommended_to_models';

const migration0013AddGpuRecommendedToModels = {
  name: MIGRATION_NAME,
  async up({ context: queryInterface }: { context: QueryInterface }) {
    await queryInterface.addColumn(TABLE_NAME, 'gpu', {
      type: DataTypes.BOOLEAN,
      allowNull: false,
      defaultValue: false,
    });
  },
  async down({ context: queryInterface }: { context: QueryInterface }) {
    await queryInterface.removeColumn(TABLE_NAME, 'gpu');
  },
};

export default migration0013AddGpuRecommendedToModels;
