import { useMemo } from "react";
import styles from "./ResultArea.module.css";

export const ResultArea = ({ data }: { data: any }) => {
  const jsonText = useMemo(() => JSON.stringify(data, null, 2), [data]);
  const hasData = data != null;

  const handleCopy = async () => {
    await navigator.clipboard.writeText(jsonText); // requires https or localhost
  };

  return (
    <div className={styles.resultRoot}>
      {hasData ? (
        <>
          <div className={styles.headingRow}>
            <div className={styles.heading}>Extrahierte Daten</div>
            <button className={styles.copyBtn} onClick={handleCopy}>
              <span className="material-icons">content_copy</span>
            </button>
          </div>

          <div className={styles.outputSection}>
            <pre className={styles.pre}>{jsonText}</pre>
          </div>
        </>
      ) : (
        <p className={styles.empty}>
          Noch keine Daten. Laden Sie ein PDF hoch.
        </p>
      )}
    </div>
  );
};
