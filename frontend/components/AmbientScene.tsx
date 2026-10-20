"use client";

import { Float, MeshDistortMaterial, Sparkles } from "@react-three/drei";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { useMemo, useRef } from "react";
import { BufferAttribute, BufferGeometry, type Group, type Points } from "three";

const orbs = [
  { position: [-5, 2.5, -4] as const, scale: 2.4, color: "#ff5d8f", speed: 0.6 },
  { position: [5.5, -1.5, -6] as const, scale: 2.8, color: "#9b7bff", speed: 0.45 },
  { position: [0.5, -4.5, -5] as const, scale: 1.8, color: "#f2c46d", speed: 0.75 },
  { position: [-3.5, -3.5, -8] as const, scale: 1.4, color: "#3fd6c6", speed: 0.9 },
];

function starField(count: number): BufferGeometry {
  const positions = new Float32Array(count * 3);
  const seed = (value: number) => {
    const n = Math.sin(value * 127.1 + 311.7) * 43758.5453;
    return n - Math.floor(n);
  };
  for (let i = 0; i < count; i++) {
    positions[i * 3] = (seed(i * 3 + 1) - 0.5) * 30;
    positions[i * 3 + 1] = (seed(i * 3 + 2) - 0.5) * 18;
    positions[i * 3 + 2] = -seed(i * 3 + 3) * 14;
  }
  const geometry = new BufferGeometry();
  geometry.setAttribute("position", new BufferAttribute(positions, 3));
  return geometry;
}

/** Slow-moving distorted orbs, a star field and pointer parallax. It sits behind all content. */
function Scene() {
  const stars = useMemo(() => starField(900), []);
  const group = useRef<Group>(null);
  const points = useRef<Points>(null);
  const { pointer } = useThree();

  useFrame(({ clock }) => {
    if (group.current) {
      group.current.position.x += (pointer.x * 0.8 - group.current.position.x) * 0.03;
      group.current.position.y += (pointer.y * 0.5 - group.current.position.y) * 0.03;
    }
    if (points.current) points.current.rotation.z = clock.elapsedTime * 0.01;
  });

  return <>
    <ambientLight intensity={0.6} />
    <pointLight position={[4, 4, 4]} intensity={40} color="#ffd9a0" />
    <group ref={group}>
      {orbs.map((orb, index) => (
        <Float key={index} speed={orb.speed * 2} rotationIntensity={0.4} floatIntensity={1.2}>
          <mesh position={orb.position} scale={orb.scale}>
            <icosahedronGeometry args={[1, 6]} />
            <MeshDistortMaterial color={orb.color} distort={0.45} speed={orb.speed * 2} roughness={0.2} metalness={0.3} transparent opacity={0.28} />
          </mesh>
        </Float>
      ))}
    </group>
    <points ref={points} geometry={stars}>
      <pointsMaterial color="#f6eee2" size={0.03} sizeAttenuation transparent opacity={0.6} depthWrite={false} />
    </points>
    <Sparkles count={60} scale={[24, 14, 6]} size={2.5} speed={0.25} color="#f2c46d" opacity={0.5} />
  </>;
}

export function AmbientScene() {
  return <div className="pointer-events-none fixed inset-0 -z-0 overflow-hidden" aria-hidden="true">
    <div className="absolute -top-40 -left-32 size-[560px] rounded-full bg-rose/20 blur-[120px] animate-drift" />
    <div className="absolute top-1/3 -right-40 size-[620px] rounded-full bg-violet/20 blur-[140px] animate-drift [animation-delay:-6s]" />
    <div className="absolute -bottom-40 left-1/4 size-[520px] rounded-full bg-teal/15 blur-[120px] animate-drift [animation-delay:-11s]" />
    <Canvas className="absolute inset-0" camera={{ position: [0, 0, 8], fov: 50 }} dpr={[1, 1.5]} gl={{ alpha: true, antialias: true }}>
      <Scene />
    </Canvas>
  </div>;
}

