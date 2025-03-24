import { cn } from 'src/renderer/lib/utils';

export default function ExportIcon({
  className = '',
}: {
  // eslint-disable-next-line react/require-default-props
  className?: string;
}) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={cn('size-6', className)}
    >
      <path
        d="M4 12C4 16.4183 7.58172 20 12 20C16.4183 20 20 16.4183 20 12"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
      <path
        d="M12 14L12 4M12 4L15 7M12 4L9 7"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
