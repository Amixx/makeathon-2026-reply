import { NavLink } from "react-router";
import styles from "./Navbar.module.css";

function navClass({ isActive }: { isActive: boolean }) {
  return `${styles.link} ${isActive ? styles.active : ""}`;
}

export default function Navbar() {
  return (
    <nav className={styles.nav}>
      <NavLink to="/" className={styles.brand}>
        Campus Co-Pilot
      </NavLink>
      <NavLink to="/" className={navClass} end>
        Home
      </NavLink>
      <NavLink to="/chat" className={navClass}>
        Chat
      </NavLink>
    </nav>
  );
}
