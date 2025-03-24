import { Button } from '../ui/button';
import { Input } from '../ui/input';

export default function DirectoryField({
  onChange,
  value,
  disabled,
}: {
  onChange: (filePath: string) => void;
  value: string;
  disabled: boolean;
}) {
  const handleSelectDirectory = async () => {
    await window.fileSystem.selectDirectory().then((newPath) => {
      onChange(newPath);
      return newPath;
    });
  };

  const handleOpenDirectory = async () => {
    await window.fileSystem.openPath({ path: value });
  };

  return (
    <div className="flex items-center mt-2">
      <Input
        type="text"
        className="flex-1 mr-2 border border-gray-300 disabled:opacity-100 disabled:cursor-text"
        value={value || 'No Directory Selected'}
        readOnly
      />
      <Button
        type="button"
        onClick={disabled ? handleOpenDirectory : handleSelectDirectory}
      >
        Browse
      </Button>
    </div>
  );
}
