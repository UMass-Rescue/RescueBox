import { MarkdownResponse } from '../generated_models';

const markdownResponseBody: MarkdownResponse = {
  output_type: 'markdown',
  value:
    '\n## Results\n\n- Found: True\n- Target File: /Users/atharvakale/workspace/umass/596e-cs/individual-project/small-block-forensics/examples/target_directory/sample.txt\n- Block Number in Target File: 0\n- Known Dataset File: /Users/atharvakale/workspace/umass/596e-cs/individual-project/small-block-forensics/examples/known_content_directory/sample.txt\n- Block Number in Known Dataset File: 0\n',
  title: 'Small Block Forensics',
  subtitle: undefined,
} satisfies MarkdownResponse;

export default markdownResponseBody;
