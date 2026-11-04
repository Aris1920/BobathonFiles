import { useState, useRef, DragEvent } from 'react';
import { extractResume } from '../api/resume';

interface ResumeUploadProps {
  onExtracted: (text: string) => void;
}

export default function ResumeUpload({ onExtracted }: ResumeUploadProps) {
  const [loading, setLoading] = useState(false);
  const [fileName, setFileName] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  async function processFile(file: File) {
    if (!file.name.match(/\.(pdf|docx)$/i)) {
      setError('Only .pdf and .docx files are supported.');
      return;
    }
    setError(null);
    setLoading(true);
    setDone(false);
    try {
      const result = await extractResume(file);
      setFileName(file.name);
      setDone(true);
      onExtracted(result.text);
    } catch {
      setError('Failed to parse resume. Please try again.');
    } finally {
      setLoading(false);
    }
  }

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) processFile(file);
  }

  function handleDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) processFile(file);
  }

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors ${
        dragging ? 'border-blue-400 bg-blue-50' : 'border-gray-300 bg-white'
      }`}
    >
      {loading ? (
        <div className="flex flex-col items-center gap-2 text-gray-500">
          <svg className="animate-spin h-6 w-6 text-blue-500" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
          </svg>
          <span className="text-sm">Parsing resume…</span>
        </div>
      ) : done ? (
        <div className="flex flex-col items-center gap-1 text-green-700">
          <span className="text-2xl">✓</span>
          <span className="text-sm font-medium">Resume parsed</span>
          <span className="text-xs text-gray-500">{fileName}</span>
          <button
            onClick={() => { setDone(false); setFileName(null); if (inputRef.current) inputRef.current.value = ''; }}
            className="mt-1 text-xs text-blue-600 hover:underline"
          >
            Upload a different file
          </button>
        </div>
      ) : (
        <div className="flex flex-col items-center gap-2">
          <p className="text-sm text-gray-500">
            Drag &amp; drop your resume here, or{' '}
            <button
              type="button"
              onClick={() => inputRef.current?.click()}
              className="text-blue-600 hover:underline font-medium"
            >
              browse
            </button>
          </p>
          <p className="text-xs text-gray-400">PDF or DOCX only</p>
          {error && <p className="text-xs text-red-600">{error}</p>}
        </div>
      )}
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,.docx"
        onChange={handleFileChange}
        className="hidden"
      />
    </div>
  );
}
