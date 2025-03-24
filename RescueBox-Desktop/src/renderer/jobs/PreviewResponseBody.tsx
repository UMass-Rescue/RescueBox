/* eslint-disable @typescript-eslint/no-unused-vars */
import { ResponseBody } from 'src/shared/generated_models';
import { match } from 'ts-pattern';
import MarkdownView from '../components/response_body/text_views/MarkdownView';
import DirectoryView from '../components/response_body/directory_views/DirectoryView';
import BatchDirectoryView from '../components/response_body/directory_views/BatchDirectoryView';
import BatchFileView from '../components/response_body/file_views/BatchFileView';
import BatchTextView from '../components/response_body/text_views/BatchTextView';
import TextView from '../components/response_body/text_views/TextView';
import FileView from '../components/response_body/file_views/FileView';

export default function PreviewResponseBody({
  response,
}: {
  response: ResponseBody;
}) {
  return match(response)
    .with({ output_type: 'file' }, (fileResponse) => {
      return <FileView response={fileResponse} />;
    })
    .with({ output_type: 'directory' }, (directoryResponse) => {
      return <DirectoryView response={directoryResponse} />;
    })
    .with({ output_type: 'markdown' }, (markdownResponse) => {
      return <MarkdownView response={markdownResponse} />;
    })
    .with({ output_type: 'text' }, (textResponse) => {
      return <TextView response={textResponse} />;
    })
    .with({ output_type: 'batchfile' }, (batchFileResponse) => {
      return <BatchFileView response={batchFileResponse} />;
    })
    .with({ output_type: 'batchtext' }, (batchTextResponse) => {
      return <BatchTextView response={batchTextResponse} />;
    })
    .with({ output_type: 'batchdirectory' }, (batchDirectoryResponse) => {
      return <BatchDirectoryView response={batchDirectoryResponse} />;
    })
    .otherwise(() => {
      return <div>Unknown Response</div>;
    });
}
