import { Root } from 'react-markdown/lib';
import { Options } from 'rehype-external-links';

export default function RehypeExternalLinks(
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  options: Readonly<Options> | null | undefined,
) {
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  return (tree: Root) => undefined;
}
