import {
  useId,
  useRef,
  useState,
  type DragEvent,
  type KeyboardEvent,
} from "react";
import type { UploadAreaProps } from "./UploadArea.interface";
import styles from "./UploadArea.module.css";
import { getFileSizeInMB } from "../../../../utils/getFileSizeInMB";
import LoadIcon from "./components/LoadIcon/LoadIcon";

export default function UploadArea({
  accept = "application/pdf",
  selectedFile,
  onFileSelected,
}: UploadAreaProps) {
  const inputId = useId();
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [dragActive, setDragActive] = useState(false);

  const openPicker = () => inputRef.current?.click();

  const onKeyDown = (e: KeyboardEvent<HTMLLabelElement>) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      openPicker();
    }
  };

  const onDragOver = (e: DragEvent<HTMLLabelElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(true);
  };

  const onDragLeave = (e: DragEvent<HTMLLabelElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
  };

  const onDrop = (e: DragEvent<HTMLLabelElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    const file = e.dataTransfer.files?.[0];
    onFileSelected(file ?? null);
  };

  const labelClassName = `${styles.dropArea} ${
    dragActive ? styles.dropAreaActive : ""
  }`;

  return (
    <>
      <label
        htmlFor={inputId}
        className={labelClassName}
        onDragOver={onDragOver}
        onDragEnter={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        onKeyDown={onKeyDown}
        tabIndex={0}
        aria-live="polite"
      >
        <div className={styles.title}>
          <LoadIcon />
          {dragActive ? "Datei hier ablegen" : "PDF hierher ziehen"}
        </div>
        <div id="dropHelp" className={styles.subtitle}>
          oder klicke, um sie auszuwählen
        </div>

        {selectedFile && (
          <div id="selectedFileDesc" className={styles.selectedFile}>
            Ausgewählt:{" "}
            <span className={styles.fileName}>{selectedFile.name}</span>{" "}
            <span>{getFileSizeInMB(selectedFile.size)}</span>
          </div>
        )}
      </label>

      <input
        id={inputId}
        ref={inputRef}
        type="file"
        accept={accept}
        style={{ display: "none" }}
        onChange={(e) => onFileSelected(e.target.files?.[0] ?? null)}
      />
    </>
  );
}
