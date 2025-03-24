export default function ImagePreview({ filePath }: { filePath: string }) {
  return (
    <div className="border border-gray-300 rounded-lg p-4 bg-white">
      <div className="overflow-auto flex flex-col items-center">
        <img
          src={filePath}
          alt="Preview"
          className="object-contain max-h-96 w-auto"
        />
      </div>
    </div>
  );
}
