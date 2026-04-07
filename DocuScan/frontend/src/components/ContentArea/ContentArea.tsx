import WorkPanel from "./components/WorkPanel/WorkPanel";
import styles from "./ContentArea.module.css";

export default function ContentArea() {
  return (
    <div className={styles.screen}>
      <div className={styles.card}>
        <header className={styles.cardHeader}>
          <h1 style={{ margin: 0 }}>Dokumenten DatenExraktor</h1>
          <p className={styles.subtitle}>
            Automatisierte Erfassung von Vertragsdaten
          </p>
        </header>
        <div className={styles.cardBody}>
          <WorkPanel />
        </div>
      </div>
    </div>
  );
}
