import { Button } from '../ui/button';
import { Input } from '../ui/input';

export default function FileField({
  onChange,
  value,
  disabled,
}: {
  onChange: (filePath: string) => void;
  value: string;
  disabled: boolean;
}) {
  const handleSelectFile = async () => {
    await window.fileSystem.selectFile().then((path) => {
      onChange(path);
      return path;
    });
  };

  const handleShowFileInExplorer = async () => {
    await window.fileSystem.showFileInExplorer({ path: value });
  };

  return (
    <div className="flex items-center mt-2">
      <Input
        type="text"
        className="flex-1 mr-2 border border-gray-300 disabled:opacity-100 disabled:cursor-text"
        value={value || 'No File Selected'}
        readOnly
      />
      <Button
        type="button"
        onClick={disabled ? handleShowFileInExplorer : handleSelectFile}
      >
        Browse
      </Button>
    </div>
  );
}
