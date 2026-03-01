import { ShieldCheck } from "lucide-react";

function HeroBanner() {
  return (
    <section className="hero-banner">
      <div className="hero-content">
        <div className="hero-icon">
          <ShieldCheck className="hero-icon-svg" />
        </div>
        <div>
          <p className="hero-eyebrow">SECURE CLIENT PORTAL</p>
          <h1 className="hero-title">Protect what matters</h1>
        </div>
      </div>
    </section>
  );
}

export default HeroBanner;