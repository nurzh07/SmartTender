export function SkeletonCard() {
  return (
    <div className="card" style={{ opacity: 0.6 }}>
      <div style={{
        height: "24px",
        background: "var(--surface3)",
        borderRadius: "4px",
        marginBottom: "0.75rem",
        width: "60%"
      }} />
      <div style={{
        height: "16px",
        background: "var(--surface3)",
        borderRadius: "4px",
        marginBottom: "0.5rem",
        width: "40%"
      }} />
      <div style={{
        height: "32px",
        background: "var(--surface3)",
        borderRadius: "4px",
        marginTop: "1rem",
        width: "30%"
      }} />
    </div>
  );
}

export function SkeletonStatCard() {
  return (
    <div className="card" style={{ opacity: 0.6 }}>
      <div style={{
        height: "20px",
        background: "var(--surface3)",
        borderRadius: "4px",
        marginBottom: "0.5rem",
        width: "50%"
      }} />
      <div style={{
        height: "36px",
        background: "var(--surface3)",
        borderRadius: "4px",
        width: "40%"
      }} />
    </div>
  );
}

export function SkeletonRow() {
  return (
    <div style={{
      padding: "1rem",
      borderBottom: "1px solid var(--border)",
      display: "flex",
      justifyContent: "space-between",
      alignItems: "center",
      opacity: 0.6
    }}>
      <div style={{ flex: 1 }}>
        <div style={{
          height: "18px",
          background: "var(--surface3)",
          borderRadius: "4px",
          marginBottom: "0.5rem",
          width: "70%"
        }} />
        <div style={{
          height: "14px",
          background: "var(--surface3)",
          borderRadius: "4px",
          width: "50%"
        }} />
      </div>
      <div style={{
        height: "28px",
        background: "var(--surface3)",
        borderRadius: "4px",
        width: "80px"
      }} />
    </div>
  );
}

export function SkeletonGrid({ count = 3 }: { count?: number }) {
  return (
    <div className="grid-3">
      {Array.from({ length: count }).map((_, i) => (
        <SkeletonStatCard key={i} />
      ))}
    </div>
  );
}
