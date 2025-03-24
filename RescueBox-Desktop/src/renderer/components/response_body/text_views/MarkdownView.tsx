import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeExternalLinks from 'rehype-external-links';
import { MarkdownResponse } from 'src/shared/generated_models';

export default function MarkdownView({
  response,
}: {
  response: MarkdownResponse;
}) {
  return (
    <div className="prose max-w-full markdown">
      <Markdown
        rehypePlugins={[[rehypeExternalLinks, { target: '_blank' }]]}
        className="text-black"
        remarkPlugins={[remarkGfm]}
      >
        {`# ${response.title}\n${response.subtitle || ''}\n${response.value}`}
      </Markdown>
    </div>
  );
}
