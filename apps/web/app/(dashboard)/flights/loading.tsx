import styles from "./page.module.css";

export default function Loading() {
  return (
    <article className={`card ${styles.panel}`} aria-busy="true">
      <header className={styles.skeletonHeader}>
        <div className={styles.skeletonHeading}>
          <div className={`${styles.skeleton} ${styles.skeletonKicker}`} />
          <div className={`${styles.skeleton} ${styles.skeletonTitle}`} />
          <div className={`${styles.skeleton} ${styles.skeletonLine}`} />
          <div className={`${styles.skeleton} ${styles.skeletonLineShort}`} />
        </div>
        <div className={`${styles.skeleton} ${styles.skeletonAction}`} />
      </header>

      <section className={styles.skeletonTable}>
        {Array.from({ length: 6 }, (_, index) => (
          <div key={index} className={styles.skeletonRow}>
            <div className={`${styles.skeleton} ${styles.skeletonCell}`} />
            <div className={`${styles.skeleton} ${styles.skeletonCell}`} />
            <div className={`${styles.skeleton} ${styles.skeletonCell}`} />
            <div className={`${styles.skeleton} ${styles.skeletonCellShort}`} />
            <div className={`${styles.skeleton} ${styles.skeletonCellShort}`} />
            <div className={`${styles.skeleton} ${styles.skeletonCellShort}`} />
          </div>
        ))}
      </section>
    </article>
  );
}
