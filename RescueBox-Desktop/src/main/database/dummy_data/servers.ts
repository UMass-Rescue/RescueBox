import { imgObjModelId, isrModelId, sbfModelId } from './mlmodels';

const servers = [
  {
    modelUid: isrModelId,
    serverAddress: '127.0.0.1',
    serverPort: 5000,
    isUserConnected: true,
  },
  {
    modelUid: sbfModelId,
    serverAddress: '127.0.0.1',
    serverPort: 5001,
    isUserConnected: true,
  },
  {
    modelUid: imgObjModelId,
    serverAddress: '127.0.0.1',
    serverPort: 5002,
    isUserConnected: true,
  },
];

export default servers;
