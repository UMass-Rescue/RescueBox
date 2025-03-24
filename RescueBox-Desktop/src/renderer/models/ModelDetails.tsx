import { Link, useParams } from 'react-router-dom';
import LoadingScreen from 'src/renderer/components/LoadingScreen';
import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { ModelAppStatus } from 'src/shared/models';
import rehypeExternalLinks from 'rehype-external-links';
import { Button } from '../components/ui/button';
import GreenRunIcon from '../components/icons/GreenRunIcon';
import { useModelInfo, useServerStatus } from '../lib/hooks';

function ModelDetails() {
  const { modelUid } = useParams();

  const {
    data: modelInfo,
    error: modelInfoError,
    isLoading: modelInfoIsLoading,
  } = useModelInfo(modelUid);

  const {
    serverStatus,
    error: serverStatusError,
    isLoading: serverStatusIsLoading,
  } = useServerStatus(modelUid);

  if (!modelUid) {
    return <div>Error: Model UID not found</div>;
  }

  if (!modelInfo) {
    return <LoadingScreen />;
  }
  if (modelInfoIsLoading) {
    return <LoadingScreen />;
  }
  if (modelInfoError) {
    return <div>Error loading model info</div>;
  }

  if (serverStatusIsLoading) {
    return <LoadingScreen />;
  }
  if (serverStatusError) {
    return <div>Error loading server status</div>;
  }
  if (!serverStatus) {
    return <div>No server status available</div>;
  }

  return (
    <div className="w-4/5 max-w-full mx-auto">
      <div className="flex flex-row justify-between m-3">
        <div className="w-2/3 m-2 mr-4 prose max-w-none markdown">
          <Markdown
            rehypePlugins={[[rehypeExternalLinks, { target: '_blank' }]]}
            className="text-black"
            remarkPlugins={[remarkGfm]}
          >
            {modelInfo.info}
          </Markdown>
        </div>
        <div className="sticky top-32 drop-shadow-md m-4 py-4 px-6 rounded-md w-1/3 bg-sky-200 h-full">
          <h1 className="font-bold text-lg md:text-xl lg:text-2xl m-2">
            Model Version
          </h1>
          <p className="m-2">{modelInfo.version}</p>
          <h1 className="font-bold text-lg md:text-xl lg:text-2xl m-2">
            Developed By
          </h1>
          <p className="m-2">{modelInfo.author}</p>
          <h1 className="font-bold text-lg md:text-xl lg:text-2xl m-2">
            Last Updated
          </h1>
          <p className="m-2">{new Date(modelInfo.updatedAt).toUTCString()}</p>
          <div className="mt-10">
            <Link
              to={`/models/${modelUid}/run`}
              className={
                serverStatus !== ModelAppStatus.Online
                  ? 'pointer-events-none opacity-50'
                  : ''
              }
            >
              <Button className="w-full flex flex-row gap-2 hover:-translate-y-0.5 transition-all py-2 px-6 rounded-lg bg-green-600 hover:bg-green-500">
                Run
                <GreenRunIcon />
              </Button>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
export default ModelDetails;
