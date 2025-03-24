import ReactPlayer from 'react-player';

export default function VideoPreview({ filePath }: { filePath: string }) {
  return <ReactPlayer url={filePath} controls width="100%" height="100%" />;
}
