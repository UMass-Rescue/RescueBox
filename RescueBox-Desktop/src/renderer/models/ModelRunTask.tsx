import GreenRunIcon from 'src/renderer/components/icons/GreenRunIcon';
import InputField from 'src/renderer/components/InputField';
import ParameterField from 'src/renderer/components/ParameterField';
import { Button } from '@shadcn/button';
import { Controller, useForm } from 'react-hook-form';
import { useNavigate, useOutletContext, useParams } from 'react-router-dom';
import {
  InputSchema,
  ParameterSchema,
  SchemaAPIRoute,
} from 'src/shared/generated_models';
import { RunJobArgs } from 'src/shared/models';
import { useTaskSchema } from '../lib/hooks';
import { buildRequestBody, isRunnableTaskSchema } from '../lib/utils';
import LoadingScreen from '../components/LoadingScreen';

export default function ModelRunTask() {
  const { modelUid, order } = useParams();
  const apiRoutes: SchemaAPIRoute[] = useOutletContext();
  const thisApiRoute = apiRoutes.find((route) => String(route.order) === order);

  const {
    data: taskSchema,
    error: taskSchemaError,
    isLoading: taskSchemaIsLoading,
  } = useTaskSchema(modelUid, order);

  const {
    handleSubmit,
    control,
    formState: { errors },
  } = useForm({
    mode: 'onChange',
  });

  const navigate = useNavigate();

  if (!modelUid || !order) {
    return <div>Invalid Model UID or Task ID.</div>;
  }

  if (!thisApiRoute || !taskSchema) {
    return (
      <div
        className="bg-orange-100 border-l-4 border-orange-500 text-orange-700 p-4"
        role="alert"
      >
        <p className="font-bold">No Tasks Available</p>
        <p>
          This model application has no tasks available to use. If you are a
          model application developer, see the section on{' '}
          <a
            className="underline text-blue-600"
            href="https://umass-rescue.github.io/Flask-ML/materials/guides/getting-started/#adding-a-ui-schema"
          >
            UI schema in the Flask-ML docs{' '}
          </a>
          for more information.
        </p>
      </div>
    );
  }
  if (taskSchemaIsLoading) {
    return <LoadingScreen />;
  }
  if (taskSchemaError) {
    return <div>Error loading task schema</div>;
  }

  const onSubmit = async (data: any) => {
    const runJobArgs: RunJobArgs = {
      taskSchemaAtTimeOfRun: taskSchema,
      modelUid,
      taskUid: order,
      requestBody: buildRequestBody(taskSchema, data),
    };
    await window.job.runJob(runJobArgs);
    navigate(`/jobs`);
  };

  const { runnable, reasons: notRunnableReasons } =
    isRunnableTaskSchema(taskSchema);

  return (
    <form
      onSubmit={handleSubmit(onSubmit)}
      className="flex flex-col justify-between min-h-full"
    >
      <div className="mb-10">
        <h1 className="text-2xl font-bold mb-4">{thisApiRoute.short_title}</h1>
        <div className="grid grid-cols-1 gap-6">
          {taskSchema.inputs.map((inputSchema: InputSchema) => (
            <div key={inputSchema.key}>
              <Controller
                name={inputSchema.key}
                control={control}
                rules={{ required: `Field is required.` }}
                render={({ field }) => (
                  <InputField
                    inputSchema={inputSchema}
                    value={field.value}
                    onChange={field.onChange}
                  />
                )}
              />
              {errors[inputSchema.key] && (
                <span className="text-red-500 text-xs mt-1">
                  {errors[inputSchema.key]?.message?.toString()}
                </span>
              )}
            </div>
          ))}
        </div>
        {taskSchema.parameters.length > 0 && (
          <div>
            <hr className="mt-8 mb-4" />
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {taskSchema.parameters.map((parameterSchema: ParameterSchema) => (
                <div key={parameterSchema.key}>
                  <Controller
                    name={parameterSchema.key}
                    control={control}
                    rules={{
                      required: `Field is required.`,
                      validate: {
                        validInt: (v) =>
                          (parameterSchema.value.parameterType === 'int'
                            ? !Number.isNaN(v) && Number.isInteger(v)
                            : true) || `Value must be an integer.`,
                        validFloat: (v) =>
                          (parameterSchema.value.parameterType === 'float'
                            ? !Number.isNaN(v)
                            : true) || `Value must be a float.`,
                      },
                    }}
                    defaultValue={parameterSchema.value.default || ''}
                    render={({ field }) => (
                      <ParameterField
                        parameterSchema={parameterSchema}
                        value={field.value}
                        onChange={field.onChange}
                      />
                    )}
                  />
                  {errors[parameterSchema.key] && (
                    <span className="text-red-500 text-xs mt-1">
                      {errors[parameterSchema.key]?.message?.toString()}
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
      {notRunnableReasons && (
        <div
          className="bg-orange-100 border-l-4 flex flex-col gap-2 border-orange-500 text-orange-700 p-4"
          role="alert"
        >
          <p className="font-bold">Task Unavailable</p>
          <div>
            <p className="font-semibold text-sm">Reasons:</p>
            {notRunnableReasons.map((reason) => (
              <li className="text-sm" key={reason}>
                {reason}
              </li>
            ))}
          </div>
        </div>
        // <div className="p-2 rounded-md bg-yellow-200">
        //   <h2 className="text-xl font-bold mb-4">Not Runnable</h2>
        //   <ul className="list-disc list-inside">
        //   </ul>
        // </div>
      )}
      <Button
        type="submit"
        className="w-full gap-2 hover:-translate-y-0.5 transition-all py-2 px-6 rounded-lg bg-green-600 hover:bg-green-500"
        disabled={!runnable}
      >
        Run Model
        <GreenRunIcon />
      </Button>
    </form>
  );
}
