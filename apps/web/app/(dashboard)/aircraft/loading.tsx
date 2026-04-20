import styles from "./page.module.css";

export default function Loading() {
  return (
    <article className={`card ${styles.panel}`} aria-busy="true">
      <header className={styles.header}>
        <div className={styles.heading}>
          <div className={`${styles.skeleton} ${styles.skeletonKicker}`} />
          <div className={`${styles.skeleton} ${styles.skeletonTitle}`} />
          <div className={`${styles.skeleton} ${styles.skeletonLine}`} />
          <div className={`${styles.skeleton} ${styles.skeletonLineShort}`} />
        </div>
        <div className={`${styles.skeleton} ${styles.skeletonButton}`} />
      </header>

      <section className={styles.fleetGrid}>
        {Array.from({ length: 4 }, (_, index) => (
          <div key={index} className={styles.skeletonCard}>
            <div className={`${styles.skeleton} ${styles.skeletonBadge}`} />
            <div className={`${styles.skeleton} ${styles.skeletonCardTitle}`} />
            <div className={`${styles.skeleton} ${styles.skeletonLine}`} />
            <div className={styles.skeletonMetaGrid}>
              <div className={`${styles.skeleton} ${styles.skeletonLine}`} />
              <div className={`${styles.skeleton} ${styles.skeletonLine}`} />
            </div>
            <div className={styles.skeletonChipRow}>
              <div className={`${styles.skeleton} ${styles.skeletonChip}`} />
              <div className={`${styles.skeleton} ${styles.skeletonChip}`} />
              <div className={`${styles.skeleton} ${styles.skeletonChip}`} />
            </div>
          </div>
        ))}
      </section>
    </article>
  );
}
