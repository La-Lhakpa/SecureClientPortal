import React, { useEffect, useRef, useState, FC, CSSProperties } from "react";
import * as THREE from "three";

export const shaders = {
  ASTRAL_FLARE: `
        varying vec2 vUv;
        uniform vec2 u_resolution;
        uniform float u_time;

        void main() {
            vec2 uv = (vUv - 0.5) * 2.0;
            float aspect = u_resolution.x / u_resolution.y;
            uv.x *= aspect;
            
            float t = u_time * 0.2;
            vec3 color = vec3(0.0);
            
            float angle = atan(uv.y, uv.x);
            float len = length(uv);
            
            float spiral = angle + 1.0 / max(0.1, len) - t * 2.0;
            float spiral_pattern = pow(sin(spiral * 5.0) * 0.5 + 0.5, 2.0);
            
            float ring_speed = t * 2.0;
            float ring_pattern = sin(len * 20.0 - ring_speed);
            ring_pattern = smoothstep(0.8, 1.0, ring_pattern);
            
            float combined_pattern = max(spiral_pattern * 0.6, ring_pattern * 0.8);
            
            float noise = fract(sin(dot(uv, vec2(12.9898, 78.233))) * 43758.5453);
            combined_pattern *= (0.8 + noise * 0.2);
            
            vec3 color1 = vec3(0.1, 0.2, 0.8);
            vec3 color2 = vec3(1.0, 0.2, 0.5);
            vec3 color3 = vec3(0.9, 0.9, 0.1);
            
            color = mix(color, color1, combined_pattern);
            color = mix(color, color2, pow(len, 2.0) * 0.5);
            color = mix(color, color3, smoothstep(0.95, 1.0, spiral_pattern) * 0.5);
            
            color *= smoothstep(1.5, 0.4, len);
            
            gl_FragColor = vec4(color, 1.0);
        }
    `,
  RADIANT_ORB: `
        varying vec2 vUv;
        uniform vec2 u_resolution;
        uniform float u_time;

        void main() {
            vec2 uv = (gl_FragCoord.xy * 2.0 - u_resolution.xy) / min(u_resolution.x, u_resolution.y);
            float t = u_time * 0.2;
            
            vec3 color = vec3(0.0);
            float val = 0.0;

            for(int i = 0; i < 5; i++) {
                float angle = t * (float(i) * 0.5 + 0.5);
                float radius = 0.5 + 0.1 * sin(t * float(i+1));
                vec2 offset = vec2(cos(angle), sin(angle)) * radius;
                val += 0.005 / distance(uv, offset);
            }

            color = vec3(pow(val, 2.0), pow(val, 3.0), pow(val, 4.0));
            gl_FragColor = vec4(color, 1.0);
        }
    `,
  COSMIC_WEB: `
        varying vec2 vUv;
        uniform vec2 u_resolution;
        uniform float u_time;

        void main() {
            vec2 uv = (vUv - 0.5) * 2.0;
            float aspect = u_resolution.x / u_resolution.y;
            uv.x *= aspect;

            float t = u_time * 0.1;
            vec3 color = vec3(0.0);
            
            for(int j = 0; j < 3; j++){
                for(int i = 0; i < 5; i++){
                    float i_float = float(i);
                    float j_float = float(j);
                    float intensity = i_float * i_float * 0.002;
                    float phase = t - 0.01 * j_float + i_float * 0.01;
                    float line_dist = fract(phase) * 5.0 - length(uv) + mod(uv.x + uv.y, 0.2);
                    color[j] += intensity / abs(line_dist);
                }
            }
            
            gl_FragColor = vec4(color, 1.0);
        }
    `,
};

const vertexShader = `
    varying vec2 vUv;
    void main() {
        vUv = uv;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
    }
`;

class ThreeShaderManager {
  private container: HTMLElement;
  private fragmentShader: string;
  private renderer: THREE.WebGLRenderer;
  private scene: THREE.Scene;
  private camera: THREE.OrthographicCamera;
  private material: THREE.ShaderMaterial;
  private mesh: THREE.Mesh;
  private uniforms: { [uniform: string]: THREE.IUniform };
  private animationId: number | null = null;

  constructor(container: HTMLElement, fragmentShader: string) {
    this.container = container;
    this.fragmentShader = fragmentShader;

    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    this.scene = new THREE.Scene();
    this.camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);

    this.uniforms = {
      u_time: { value: 0.0 },
      u_resolution: { value: new THREE.Vector2() },
    };

    const geometry = new THREE.PlaneGeometry(2, 2);
    this.material = new THREE.ShaderMaterial({
      uniforms: this.uniforms,
      vertexShader,
      fragmentShader: this.fragmentShader,
    });
    this.mesh = new THREE.Mesh(geometry, this.material);
  }

  public init(): void {
    this.scene.add(this.mesh);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.container.appendChild(this.renderer.domElement);
    this.handleResize();
    window.addEventListener("resize", this.handleResize);
    this.startAnimation();
  }

  private handleResize = (): void => {
    if (!this.container) return;
    const width = this.container.clientWidth;
    const height = this.container.clientHeight;
    this.renderer.setSize(width, height);
    (this.uniforms.u_resolution.value as THREE.Vector2).x = width;
    (this.uniforms.u_resolution.value as THREE.Vector2).y = height;
  };

  private startAnimation = (): void => {
    this.animate(0);
  };

  private animate = (timestamp: number): void => {
    this.uniforms.u_time.value = timestamp / 1000;
    this.renderer.render(this.scene, this.camera);
    this.animationId = requestAnimationFrame(this.animate);
  };

  public cleanup = (): void => {
    window.removeEventListener("resize", this.handleResize);
    if (this.animationId) cancelAnimationFrame(this.animationId);
    if (this.container && this.renderer.domElement) {
      try {
        this.container.removeChild(this.renderer.domElement);
      } catch (e) {
      }
    }
    this.mesh.geometry.dispose();
    this.material.dispose();
    this.renderer.dispose();
  };
}

interface ShaderCanvasProps {
  className?: string;
  style?: CSSProperties;
  fragmentShader: string;
}

export const ShaderCanvas: FC<ShaderCanvasProps> = ({ className, style, fragmentShader }) => {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    let manager: ThreeShaderManager | null = null;
    try {
      setError(null);
      manager = new ThreeShaderManager(containerRef.current, fragmentShader);
      manager.init();
    } catch (err) {
      console.error("Shader Initialization Error:", err);
      setError(err instanceof Error ? err : new Error(String(err)));
    }

    return () => {
      if (manager) manager.cleanup();
    };
  }, [fragmentShader]);

  if (error) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-red-900 text-white p-4 rounded-lg">
        <div className="text-left font-mono text-sm max-w-full overflow-auto">
          <p className="font-bold text-lg mb-2">Shader Compilation Error</p>
          <pre className="whitespace-pre-wrap">{error.message}</pre>
        </div>
      </div>
    );
  }

  return <div ref={containerRef} className={className} style={style} />;
};

