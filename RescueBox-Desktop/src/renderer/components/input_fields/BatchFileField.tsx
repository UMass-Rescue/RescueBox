import { Button } from '../ui/button';
import { Input } from '../ui/input';

export default function BatchFileField({
  onChange,
  value,
  disabled = false,
}: {
  onChange: (paths: string[]) => void;
  value: string;
  disabled: boolean;
}) {
  const handleSelectFiles = async () => {
    await window.fileSystem.selectFiles().then((paths) => {
      onChange(paths);
      return paths;
    });
  };

  const handleOpenFile = async () => {
    await window.fileSystem.openPath({ path: value });
  };
  return (
    <div className="flex items-center mt-2">
      <Input
        type="text"
        className="flex-1 mr-2 border border-gray-300 disabled:opacity-100 disabled:cursor-text"
        value={value || 'No Files Selected'}
        readOnly
      />
      <Button
        type="button"
        onClick={!disabled ? handleSelectFiles : handleOpenFile}
      >
        Browse
      </Button>
    </div>
  );
}
