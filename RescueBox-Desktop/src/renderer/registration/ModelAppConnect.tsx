/* eslint-disable react/require-default-props */
/* eslint-disable @typescript-eslint/no-shadow */
/* eslint-disable react/jsx-props-no-spreading */
import { useForm, SubmitHandler } from 'react-hook-form';
import { useNavigate, useParams } from 'react-router-dom';
import { mutate } from 'swr';
import { useState } from 'react';
import { ModelAppStatus } from 'src/shared/models';
import { Button } from '../components/ui/button';
import { Label } from '../components/ui/label';
import { Input } from '../components/ui/input';
import { registerModelAppIp, useMLModel, useModelInfo, useServer, useServers, useServerStatus, useServerStatuses } from '../lib/hooks';
import LoadingIcon from '../components/icons/LoadingIcon';

import Modal from './Modal';
import StatusComponent from '../jobs/sub-components/StatusComponent';
import ModelDetails from '../models/ModelDetails';
import RegisterModelButton from '../components/custom_ui/RegisterModelButton';
import Models from '../models/Models';




type InvalidServer = {
  isInvalid: boolean;
  cause: 'failed' | 'flask-ml-version' | 'app-metadata-not-set' | null;
};

function ModelAppConnect() {
  // Params from URL
  const { modelUid } = useParams();
  if (!modelUid) throw new Error('modelUid is required');

  const navigate = useNavigate();

   const {
      data,
      error: serverStatusError,
      isLoading: serverIsLoading,
      isValidating: serverStatusIsValidating,
      mutate: mutateServers,
    } = registerModelAppIp();

  if (serverStatusError) {
    return <p>Error: {serverStatusError.message}</p>;
  }
  // if (serverIsLoading) return <LoadingIcon />;


  const onClose = () => {
    navigate('/registration', { replace: true });
  };

  let status = 'Running';
  if (data) {
    status = 'Completed';
  }

  return (
    <Modal title="Register Models" onClose={onClose}>
       <div className="flex justify-between items-center mb-4">
              <h1 className="text-2xl font-bold">Model Server Startup</h1>
              <StatusComponent status={status} />
      </div>
    </Modal>
  );
}
export default ModelAppConnect;
