import { useEffect, useMemo, useRef } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { Shield, Lock, Key, FileText } from "lucide-react";

const ICONS = [Shield, Lock, Key, FileText];

const randomBetween = (min, max) => Math.random() * (max - min) + min;

function createIconImage(Icon) {
  const svg = renderToStaticMarkup(
    <Icon size={64} strokeWidth={1.5} color="rgba(226, 232, 240, 0.85)" />
  );
  const img = new Image();
  img.src = `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`;
  return img;
}

export default function SecurityBackground() {
  const canvasRef = useRef(null);
  const iconImages = useMemo(() => ICONS.map(createIconImage), []);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    let rafId;
    const ctx = canvas.getContext("2d", { alpha: true });
    const particles = [];
    const count = 18;

    const resize = () => {
      const { clientWidth, clientHeight } = canvas;
      const dpr = window.devicePixelRatio || 1;
      canvas.width = clientWidth * dpr;
      canvas.height = clientHeight * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };

    const initParticles = () => {
      particles.length = 0;
      const { clientWidth: w, clientHeight: h } = canvas;
      for (let i = 0; i < count; i += 1) {
        particles.push({
          x: randomBetween(0, w),
          y: randomBetween(0, h),
          size: randomBetween(28, 52),
          speed: randomBetween(0.15, 0.45),
          rotation: randomBetween(0, Math.PI * 2),
          rotationSpeed: randomBetween(-0.004, 0.004),
          iconIndex: Math.floor(randomBetween(0, iconImages.length)),
          phase: randomBetween(0, Math.PI * 2),
        });
      }
    };

    const drawGrid = (w, h) => {
      ctx.save();
      ctx.strokeStyle = "rgba(209, 213, 219, 0.06)";
      ctx.lineWidth = 1;
      const gap = 44;
      for (let x = 0; x < w; x += gap) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, h);
        ctx.stroke();
      }
      for (let y = 0; y < h; y += gap) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(w, y);
        ctx.stroke();
      }
      ctx.restore();
    };

    const drawGlows = (w, h, t) => {
      const pulse = 0.5 + 0.5 * Math.sin(t * 0.0006);
      const glows = [
        { x: w * 0.25, y: h * 0.3, r: 220 },
        { x: w * 0.75, y: h * 0.6, r: 260 },
        { x: w * 0.5, y: h * 0.85, r: 200 },
      ];
      glows.forEach((g) => {
        const grad = ctx.createRadialGradient(g.x, g.y, 0, g.x, g.y, g.r);
        grad.addColorStop(0, `rgba(241, 245, 249, ${0.28 * pulse})`);
        grad.addColorStop(1, "rgba(241, 245, 249, 0)");
        ctx.fillStyle = grad;
        ctx.beginPath();
        ctx.arc(g.x, g.y, g.r, 0, Math.PI * 2);
        ctx.fill();
      });
    };

    const drawConnections = () => {
      const maxDist = 200;
      for (let i = 0; i < particles.length; i += 1) {
        for (let j = i + 1; j < particles.length; j += 1) {
          const a = particles[i];
          const b = particles[j];
          const dx = a.x - b.x;
          const dy = a.y - b.y;
          const dist = Math.hypot(dx, dy);
          if (dist < maxDist) {
            const alpha = (1 - dist / maxDist) * 0.2;
            ctx.strokeStyle = `rgba(209, 213, 219, ${alpha})`;
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(a.x, a.y);
            ctx.lineTo(b.x, b.y);
            ctx.stroke();
          }
        }
      }
    };

    const draw = (t) => {
      const { clientWidth: w, clientHeight: h } = canvas;
      ctx.clearRect(0, 0, w, h);

      const bg = ctx.createLinearGradient(0, 0, w, h);
      bg.addColorStop(0, "#1a1d23");
      bg.addColorStop(0.5, "#2b3038");
      bg.addColorStop(1, "#3a414c");

      ctx.fillStyle = bg;
      ctx.fillRect(0, 0, w, h);

      drawGlows(w, h, t);
      drawGrid(w, h);
      drawConnections(w, h);

      particles.forEach((p) => {
        p.y -= p.speed;
        p.rotation += p.rotationSpeed;

        if (p.y + p.size < -40) {
          p.y = h + randomBetween(20, 120);
          p.x = randomBetween(0, w);
        }

        const img = iconImages[p.iconIndex];
        if (!img.complete) return;

        ctx.save();
        ctx.translate(p.x, p.y);
        ctx.rotate(p.rotation);
        ctx.globalAlpha = 0.6;
        ctx.drawImage(img, -p.size / 2, -p.size / 2, p.size, p.size);
        ctx.restore();
      });

      rafId = requestAnimationFrame(draw);
    };

    resize();
    initParticles();
    rafId = requestAnimationFrame(draw);

    window.addEventListener("resize", resize);
    return () => {
      cancelAnimationFrame(rafId);
      window.removeEventListener("resize", resize);
    };
  }, [iconImages]);

  return (
    <div className="absolute inset-0">
      <canvas ref={canvasRef} className="h-full w-full" />
    </div>
  );
}