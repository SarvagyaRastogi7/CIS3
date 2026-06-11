interface Props {
  onUpload: (file: File) => Promise<void>;
  loading: boolean;
  filename: string | null;
  recordCount: number;
}

export function DataUpload({ onUpload, loading, filename, recordCount }: Props) {
  return (
    <div className="upload-compact">
      <div className="upload-file-info">
        <div className="file-icon" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path d="M8 4 H16 L20 8 V20 H4 V4 H8 Z" strokeLinejoin="round" />
            <path d="M8 4 V8 H16" />
          </svg>
        </div>
        <div>
          <strong>{filename ?? "Dataset"}</strong>
          <span>{recordCount} months · validated</span>
        </div>
      </div>
      <label className="btn btn-outline btn-sm">
        <input
          type="file"
          accept=".xlsx,.xls"
          disabled={loading}
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) void onUpload(file);
          }}
        />
        Replace dataset
      </label>
    </div>
  );
}
