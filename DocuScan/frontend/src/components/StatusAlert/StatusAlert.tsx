import styles from "./StatusAlert.module.css";

export const StatusAlert = ({ statusmessage }: { statusmessage: string }) => {
  return (
    <div role="alert" className={styles.status}>
      {statusmessage}
    </div>
  );
};