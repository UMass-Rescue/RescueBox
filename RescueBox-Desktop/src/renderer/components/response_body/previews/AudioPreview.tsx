import AudioPlayer from 'react-h5-audio-player';
import 'react-h5-audio-player/lib/styles.css';

export default function AudioPreview({ filePath }: { filePath: string }) {
  return (
    <div>
      <AudioPlayer src={filePath} />
    </div>
  );
}
