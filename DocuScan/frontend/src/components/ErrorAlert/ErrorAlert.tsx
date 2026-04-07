import styles from "./ErrorAlert.module.css";

export const ErrorAlert = ({ message }: { message: string }) => {
  return (
    <div role="alert" className={styles.error}>
      {message}
    </div>
  );
};
