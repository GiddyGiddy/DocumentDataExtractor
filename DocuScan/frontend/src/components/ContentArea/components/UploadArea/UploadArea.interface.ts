export interface UploadAreaProps {
  accept?: string;
  selectedFile?: File | null;
  onFileSelected: (file: File | null) => void;
}
