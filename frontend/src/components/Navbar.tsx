import { NavLink, useLocation } from "react-router";
import styles from "./Navbar.module.css";

const DEBUG_PATHS = ["/playground", "/debug"];

function navClass({ isActive }: { isActive: boolean }) {
  return `${styles.link} ${isActive ? styles.active : ""}`;
}

export default function Navbar() {
  const { pathname } = useLocation();
  const isDebug = DEBUG_PATHS.some((p) => pathname.startsWith(p));
  if (!isDebug) return null;

  return (
    <nav className={styles.nav}>
      <NavLink to="/" className={styles.brand}>
        WayTum
      </NavLink>
      <NavLink to="/playground" className={navClass}>
        Playground
      </NavLink>
      <NavLink to="/debug/chat" className={navClass}>
        Chat
      </NavLink>
    </nav>
  );
}
