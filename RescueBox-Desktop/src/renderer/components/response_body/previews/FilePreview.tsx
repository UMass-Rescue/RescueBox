import { match } from 'ts-pattern';
import { FileResponse } from 'src/shared/generated_models';
import AudioPreview from './AudioPreview';
import CSVPreview from './CSVPreview';
import ImagePreview from './ImagePreview';
import JSONPreview from './JSONPreview';
import MarkdownPreview from './MarkdownPreview';
import TextPreview from './TextPreview';
import VideoPreview from './VideoPreview';

export default function FilePreview({
  response,
  modal,
}: {
  response: FileResponse;
  modal: boolean;
}) {
  const filePrefixedPath = `file://${response.path}`;

  return match(response)
    .with({ file_type: 'text' }, () => (
      <TextPreview filePath={response.path} modal={modal} />
    ))
    .with({ file_type: 'json' }, () => (
      <JSONPreview filePath={response.path} modal={modal} />
    ))
    .with({ file_type: 'csv' }, () => (
      <CSVPreview filePath={response.path} modal={modal} />
    ))
    .with({ file_type: 'img' }, () => (
      <ImagePreview filePath={filePrefixedPath} />
    ))
    .with({ file_type: 'audio' }, () => (
      <AudioPreview filePath={filePrefixedPath} />
    ))
    .with({ file_type: 'video' }, () => (
      <VideoPreview filePath={filePrefixedPath} />
    ))
    .with({ file_type: 'markdown' }, () => (
      <MarkdownPreview filePath={response.path} modal={modal} />
    ))
    .exhaustive();
}
