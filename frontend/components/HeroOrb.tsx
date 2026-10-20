"use client";

import { Float, MeshDistortMaterial, MeshTransmissionMaterial, Sparkles } from "@react-three/drei";
import { Canvas, useFrame } from "@react-three/fiber";
import { useRef } from "react";
import type { Mesh } from "three";

function Orb() {
  const core = useRef<Mesh>(null);
  const ring = useRef<Mesh>(null);

  useFrame(({ pointer, clock }) => {
    if (core.current) {
      core.current.rotation.y = clock.elapsedTime * 0.25 + pointer.x * 0.6;
      core.current.rotation.x = pointer.y * 0.4;
    }
    if (ring.current) ring.current.rotation.z = clock.elapsedTime * 0.35;
  });

  return <Float speed={2} rotationIntensity={0.3} floatIntensity={1.4}>
    <mesh ref={core}>
      <icosahedronGeometry args={[1.25, 12]} />
      <MeshTransmissionMaterial backside samples={4} thickness={1.2} roughness={0.08} transmission={1} ior={1.4} chromaticAberration={0.12} anisotropicBlur={0.2} color="#ffd9a0" distortionScale={0.4} temporalDistortion={0.2} />
    </mesh>
    <mesh ref={ring} rotation={[Math.PI / 2.4, 0, 0]}>
      <torusGeometry args={[2.1, 0.012, 16, 200]} />
      <meshBasicMaterial color="#ff5d8f" transparent opacity={0.8} />
    </mesh>
    <mesh position={[0.3, 0.2, -0.4]} scale={1.9}>
      <sphereGeometry args={[1, 32, 32]} />
      <MeshDistortMaterial color="#9b7bff" distort={0.5} speed={1.5} transparent opacity={0.12} />
    </mesh>
  </Float>;
}

/** A transparent 3D glass orb that reacts to the pointer. It sits in the hero. */
export function HeroOrb() {
  return <div className="relative h-[340px] w-full md:h-[480px]" aria-hidden="true">
    <Canvas camera={{ position: [0, 0, 6], fov: 40 }} dpr={[1, 1.75]} gl={{ alpha: true, antialias: true }}>
      <ambientLight intensity={0.5} />
      <directionalLight position={[3, 4, 5]} intensity={2} color="#fff1d6" />
      <pointLight position={[-3, -2, 2]} intensity={20} color="#ff5d8f" />
      <Orb />
      <Sparkles count={40} scale={[7, 5, 4]} size={3} speed={0.4} color="#f2c46d" />
    </Canvas>
  </div>;
}
