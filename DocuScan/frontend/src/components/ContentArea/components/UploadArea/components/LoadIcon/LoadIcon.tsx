import styles from "./LoadIcon.module.css";
const LoadIcon = () => {
  return (
    <svg
      className={styles.icon}
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
      strokeWidth={1.5}
      stroke="currentColor"
      aria-hidden="true"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M14 16v-8m0 0l-3 3m3-3l3 3m6 5v1a2 2 0 01-2 2H6a2 2 0 01-2-2v-1"
      />
    </svg>
  );
};

export default LoadIcon;
