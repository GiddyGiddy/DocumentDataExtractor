import logo from "../../assets/CGI_logo_color_rgb.svg";
import styles from "./Header.module.css";

export const Header = () => {
  return (
    <div className={styles.header}>
      <img src={logo} alt="Logo" className={styles.headerLogo} />
      <h1 className={styles.headerTitle}>Innovation Push Projekt für WMK: Sovereign Cloud Hybrid/OnPrem Lösung</h1>
    </div>
  );
};
