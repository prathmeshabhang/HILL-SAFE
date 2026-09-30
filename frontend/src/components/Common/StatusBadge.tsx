import React from 'react';
import { ShieldAlert, ShieldCheck, Cpu, Database, AlertTriangle } from 'lucide-react';

interface StatusBadgeProps {
  type: 'PROTOTYPE_STAGING' | 'BENCHMARK' | 'SIMULATION' | 'PRELIMINARY' | 'FROZEN_VERIFIED' | 'PENDING';
  label?: string;
  size?: 'sm' | 'md';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ type, label, size = 'sm' }) => {
  const isSm = size === 'sm';
  const sizeClasses = isSm ? 'text-xs px-2 py-0.5 gap-1' : 'text-sm px-2.5 py-1 gap-1.5';

  switch (type) {
    case 'PROTOTYPE_STAGING':
      return (
        <span
          title="Hardware Classification: 5 bench-tested staging units. Zero (0) units deployed in active river water."
          className={`inline-flex items-center font-mono font-medium rounded-full bg-amber-500/15 text-amber-600 dark:text-amber-400 border border-amber-500/30 ${sizeClasses}`}
        >
          <Cpu className={isSm ? "w-3 h-3" : "w-4 h-4"} />
          {label || 'PROTOTYPE_STAGING (0 In-Water)'}
        </span>
      );

    case 'FROZEN_VERIFIED':
      return (
        <span
          title="Cryptographic model weight hash verified bit-identical against canonical registry."
          className={`inline-flex items-center font-mono font-medium rounded-full bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30 ${sizeClasses}`}
        >
          <ShieldCheck className={isSm ? "w-3 h-3" : "w-4 h-4"} />
          {label || 'FROZEN HASH VERIFIED'}
        </span>
      );

    case 'SIMULATION':
      return (
        <span
          title="Scientific Classification: Performance demonstrated through synthetic numerical hydrodynamic simulation."
          className={`inline-flex items-center font-mono font-medium rounded-full bg-blue-500/15 text-blue-600 dark:text-blue-400 border border-blue-500/30 ${sizeClasses}`}
        >
          <Database className={isSm ? "w-3 h-3" : "w-4 h-4"} />
          {label || 'SIMULATION_DEMONSTRATED'}
        </span>
      );

    case 'BENCHMARK':
      return (
        <span
          title="Scientific Classification: Empirically benchmarked on historical reanalysis or proxy records."
          className={`inline-flex items-center font-mono font-medium rounded-full bg-cyan-500/15 text-cyan-600 dark:text-cyan-400 border border-cyan-500/30 ${sizeClasses}`}
        >
          <ShieldAlert className={isSm ? "w-3 h-3" : "w-4 h-4"} />
          {label || 'EMPIRICALLY_BENCHMARKED'}
        </span>
      );

    case 'PRELIMINARY':
      return (
        <span
          title="Scientific Classification: Preliminary external proxy evidence."
          className={`inline-flex items-center font-mono font-medium rounded-full bg-teal-500/15 text-teal-600 dark:text-teal-400 border border-teal-500/30 ${sizeClasses}`}
        >
          <ShieldCheck className={isSm ? "w-3 h-3" : "w-4 h-4"} />
          {label || 'PRELIMINARY_EXTERNAL_EVIDENCE'}
        </span>
      );

    case 'PENDING':
    default:
      return (
        <span
          title="Scientific Classification: Awaiting external field calibration data."
          className={`inline-flex items-center font-mono font-medium rounded-full bg-purple-500/15 text-purple-600 dark:text-purple-400 border border-purple-500/30 ${sizeClasses}`}
        >
          <AlertTriangle className={isSm ? "w-3 h-3" : "w-4 h-4"} />
          {label || 'PENDING_EXTERNAL_DATA'}
        </span>
      );
  }
};
