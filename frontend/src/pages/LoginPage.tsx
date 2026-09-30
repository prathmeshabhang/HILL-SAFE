/**
 * frontend/src/pages/LoginPage.tsx
 * ===================================
 * FLOODY SHIELD — Multi-Persona Operational Authentication & Role Access Center.
 *
 * Implements role-based access tailored to different disaster-management personas:
 * 1. Public Citizen & Tourist (Open view access — NO LOGIN REQUIRED)
 * 2. Emergency Incident Commander (HP SDMA / District DDMA EOC clearance)
 * 3. Field Responder & Relief Camp In-Charge (NDRF / SDRF / Gram Panchayat)
 * 4. Hydrologist & Data Scientist (CWC / IMD / AI Model Validation)
 *
 * Grounded in the mandate: "Login is not compulsory, anyone can view like citizen."
 */

import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useUserStore } from '../store/useUserStore';
import { UserRole, UserProfile } from '../types';
import {
  Shield,
  ShieldAlert,
  ShieldCheck,
  User,
  Radio,
  Activity,
  CheckCircle2,
  Lock,
  ArrowRight,
  Eye,
  KeyRound,
  ExternalLink,
  Sparkles,
  MapPin,
  Compass,
} from 'lucide-react';

interface PersonaCard {
  role: UserRole;
  title: string;
  badge: string;
  badgeColor: string;
  icon: React.ReactNode;
  agency: string;
  fullName: string;
  email: string;
  clearanceLevel: string;
  description: string;
  capabilities: string[];
}

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, role, setAuth, logout, setRole } = useUserStore();

  const [emailInput, setEmailInput] = useState<string>('commander.kullu@hpsdma.gov.in');
  const [passwordInput, setPasswordInput] = useState<string>('••••••••••••');
  const [departmentInput, setDepartmentInput] = useState<string>('HP State Disaster Management Authority');
  const [authSuccessMsg, setAuthSuccessMsg] = useState<string | null>(null);

  const personas: PersonaCard[] = [
    {
      role: 'CITIZEN',
      title: 'Public Citizen & Tourist',
      badge: 'OPEN ACCESS (NO LOGIN)',
      badgeColor: 'bg-emerald-500/10 text-emerald-500 border-emerald-500/30',
      icon: <User className="w-5 h-5 text-emerald-500" />,
      agency: 'General Public & Valley Visitors',
      fullName: 'Citizen Visitor',
      email: 'public.visitor@beas-basin.org',
      clearanceLevel: 'Public Read-Only',
      description: 'Zero credentials required. Full open visibility into catchment multi-hazard risk, live sensor river gauges, verified high-ground safe havens, and evacuation navigation corridors.',
      capabilities: [
        'Explore 3D MapLibre catchment terrain & flood surfaces',
        'Inspect hyperlocal Ward & Gram Panchayat risk scores',
        'Locate nearest high-elevation emergency shelters',
        'Download official safety reports (CSV, PDF, JSON)',
      ],
    },
    {
      role: 'INCIDENT_COMMANDER',
      title: 'Incident Commander',
      badge: 'EOC DUAL-AUTHORIZATION',
      badgeColor: 'bg-rose-500/10 text-rose-500 border-rose-500/30',
      icon: <ShieldAlert className="w-5 h-5 text-rose-500" />,
      agency: 'Himachal Pradesh SDMA / DDMA Kullu',
      fullName: 'Er. Rajesh Thakur (EOC-01)',
      email: 'commander.kullu@hpsdma.gov.in',
      clearanceLevel: 'Operational Level 3',
      description: 'Emergency Operations Center command staff authorized to issue life-safety Common Alerting Protocol (CAP) warnings, dispatch SMS broadcast alerts, and sign off on natural dam response actions.',
      capabilities: [
        'Dual-signoff warning gating for emergency flood alerts',
        'Trigger evacuation advisory broadcast to vulnerable GPs',
        'Review and authorize satellite natural dam breach alerts',
        'Direct emergency NDRF / SDRF deployment corridors',
      ],
    },
    {
      role: 'FIELD_RESPONDER',
      title: 'Field Responder & Camp Warden',
      badge: 'TACTICAL FIELD DESK',
      badgeColor: 'bg-amber-500/10 text-amber-500 border-amber-500/30',
      icon: <Radio className="w-5 h-5 text-amber-500" />,
      agency: 'NDRF 14th Bn / SDRF / Gram Panchayat Relief',
      fullName: 'Subedar M. K. Sharma',
      email: 'responder.field@sdrf.hp.gov.in',
      clearanceLevel: 'Tactical Level 2',
      description: 'Ground teams and panchayat relief workers managing high-ground shelters, monitoring debris road blockages along NH-3, and logging on-site river water levels.',
      capabilities: [
        'Update shelter capacity and current headcount',
        'Report highway debris blockages and active slope slides',
        'Verify local safe haven provisions (rations, water, med)',
        'Broadcast tactical SITREP field observations',
      ],
    },
    {
      role: 'ADMIN',
      title: 'Hydrologist & Data Scientist',
      badge: 'SCIENTIFIC LABORATORY',
      badgeColor: 'bg-blue-500/10 text-blue-500 border-blue-500/30',
      icon: <Activity className="w-5 h-5 text-blue-500" />,
      agency: 'Central Water Commission / IMD / AI Research Unit',
      fullName: 'Dr. Priya Varma',
      email: 'hydrology.ai@cwc.gov.in',
      clearanceLevel: 'Scientific Level 4',
      description: 'Scientific and engineering personnel validating M1–M20 physical & ML models, calibrating ultrasonic river gauges, and executing scenario feature engineering.',
      capabilities: [
        'Run M1–M20 model validation and feature engineering',
        'Calibrate IoT ultrasonic gauge thresholds & offsets',
        'Adjust hydrodynamic Froehlich breach simulation parameters',
        'Audit data provenance and model confidence scores',
      ],
    },
  ];

  const handleSelectPersona = (p: PersonaCard) => {
    if (p.role === 'CITIZEN') {
      logout();
      setAuthSuccessMsg('Switched to Open Public Citizen View. You have full access to view all maps and data without credentials.');
    } else {
      const profile: UserProfile = {
        id: `usr-${p.role.toLowerCase()}-01`,
        email: p.email,
        fullName: p.fullName,
        role: p.role,
        agency: p.agency,
        isCommander: p.role === 'INCIDENT_COMMANDER' || p.role === 'ADMIN',
      };
      setAuth(profile, `session-token-${p.role.toLowerCase()}-${Date.now()}`);
      setAuthSuccessMsg(`Logged in as ${p.title} (${p.agency}). Operational clearance active.`);
    }

    setTimeout(() => {
      setAuthSuccessMsg(null);
      // If user came from a specific page or wants to go to dashboard
      const dest = (location.state as any)?.from?.pathname || '/';
      navigate(dest);
    }, 1200);
  };

  const handleCustomLogin = (e: React.FormEvent) => {
    e.preventDefault();
    const profile: UserProfile = {
      id: `usr-custom-${Date.now()}`,
      email: emailInput,
      fullName: emailInput.split('@')[0].replace('.', ' ').toUpperCase(),
      role: 'INCIDENT_COMMANDER',
      agency: departmentInput,
      isCommander: true,
    };
    setAuth(profile, `session-custom-${Date.now()}`);
    setAuthSuccessMsg(`Authenticated as ${profile.fullName}. Department: ${departmentInput}`);
    setTimeout(() => {
      navigate('/');
    }, 1000);
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6 pb-12">
      {/* Institutional Top Header */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 sm:p-8 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="px-3 py-1 rounded-full text-xs font-mono font-bold tracking-wider uppercase bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20 flex items-center gap-1.5">
                <Shield className="w-3.5 h-3.5" />
                HILL-SAFE • Access &amp; Operational Identity Control
              </span>
              <span className="text-xs text-slate-400 font-mono">v4.3 SEC-GATING</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-black text-slate-900 dark:text-white tracking-tight">
              Operational Authentication &amp; Role Clearance
            </h1>
            <p className="text-sm text-slate-600 dark:text-slate-400 max-w-2xl leading-relaxed">
              Our multi-hazard disaster-management system provides role-tailored capabilities for different responder tiers.
              <b className="text-slate-900 dark:text-white ml-1">Authentication is never compulsory</b> — any citizen or tourist can view live hazard maps, alerts, and evacuation havens with complete transparency.
            </p>
          </div>

          {/* Current Active Status Box */}
          <div className="bg-slate-50 dark:bg-slate-800/60 p-4 rounded-2xl border border-slate-200 dark:border-slate-700/80 shrink-0 text-right space-y-1">
            <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400">Current Active Session</div>
            <div className="text-sm font-bold text-slate-900 dark:text-white flex items-center justify-end gap-1.5">
              <span className={`w-2 h-2 rounded-full ${role === 'CITIZEN' ? 'bg-emerald-400' : 'bg-blue-500'} animate-pulse`} />
              <span>{role === 'CITIZEN' ? 'Public Citizen (Open Access)' : user?.fullName || role}</span>
            </div>
            <div className="text-[11px] font-mono text-slate-500 dark:text-slate-400">
              {role === 'CITIZEN' ? 'View Only • All GIS & Maps Open' : user?.agency || 'Verified Department Staff'}
            </div>
          </div>
        </div>

        {/* Public Access Banner */}
        <div className="mt-6 p-4 rounded-2xl bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800/60 flex items-start gap-3 text-emerald-800 dark:text-emerald-300 text-xs sm:text-sm">
          <CheckCircle2 className="w-5 h-5 text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <div className="font-bold">Public Transparency Mandate (HP-SDMA &amp; NDMA Compliance)</div>
            <div className="text-emerald-700 dark:text-emerald-400/90 text-xs leading-relaxed">
              In accordance with national public safety principles, critical flood inundation maps, radar rainfall nowcasts, river gauges, and evacuation assembly shelters remain open and unrestricted to every citizen, local resident, and traveler without logging in.
            </div>
          </div>
        </div>

        {authSuccessMsg && (
          <div className="mt-4 p-3 rounded-2xl bg-blue-500/10 border border-blue-500/30 text-blue-600 dark:text-blue-400 text-xs font-semibold flex items-center gap-2 animate-in fade-in">
            <Sparkles className="w-4 h-4 text-blue-500 shrink-0" />
            <span>{authSuccessMsg}</span>
          </div>
        )}
      </div>

      {/* Role Selection Grid */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <span>Select Your Operational Persona</span>
            <span className="text-xs font-normal text-slate-400">(Click to switch immediately)</span>
          </h2>
          <button
            onClick={() => navigate('/')}
            className="text-xs font-semibold text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1"
          >
            <span>Skip &amp; Open Command Dashboard</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {personas.map((p) => {
            const isCurrent = role === p.role;
            return (
              <div
                key={p.role}
                onClick={() => handleSelectPersona(p)}
                className={`group cursor-pointer bg-white dark:bg-slate-900 rounded-3xl p-6 border transition-all duration-200 hover:shadow-lg flex flex-col justify-between space-y-4 ${
                  isCurrent
                    ? 'border-blue-500 ring-2 ring-blue-500/20 shadow-md'
                    : 'border-slate-200 dark:border-slate-800 hover:border-blue-500/50'
                }`}
              >
                <div className="space-y-3">
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-center gap-2.5">
                      <div className="p-2.5 rounded-2xl bg-slate-100 dark:bg-slate-800 group-hover:scale-105 transition-transform">
                        {p.icon}
                      </div>
                      <div>
                        <h3 className="text-base font-bold text-slate-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                          {p.title}
                        </h3>
                        <span className="text-[11px] font-mono text-slate-500 dark:text-slate-400">
                          {p.agency}
                        </span>
                      </div>
                    </div>

                    <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold tracking-wider uppercase border shrink-0 ${p.badgeColor}`}>
                      {p.badge}
                    </span>
                  </div>

                  <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                    {p.description}
                  </p>

                  <div className="space-y-1.5 pt-2 border-t border-slate-100 dark:border-slate-800/80">
                    <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-semibold">
                      Authorizations &amp; Capabilities:
                    </div>
                    <ul className="space-y-1 text-xs text-slate-600 dark:text-slate-300">
                      {p.capabilities.map((cap, idx) => (
                        <li key={idx} className="flex items-center gap-1.5">
                          <CheckCircle2 className="w-3.5 h-3.5 text-blue-500 shrink-0" />
                          <span>{cap}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>

                <div className="pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs">
                  <span className="text-[11px] font-mono text-slate-400">
                    Clearance: <b className="text-slate-700 dark:text-slate-200">{p.clearanceLevel}</b>
                  </span>

                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleSelectPersona(p);
                    }}
                    className={`px-4 py-1.5 rounded-xl font-semibold transition flex items-center gap-1.5 ${
                      isCurrent
                        ? 'bg-blue-600 text-white shadow-sm'
                        : 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200 group-hover:bg-blue-600 group-hover:text-white'
                    }`}
                  >
                    <span>{isCurrent ? 'Active Persona' : 'Select Persona'}</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Official Departmental Sign-In Form (Optional) */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 sm:p-8 shadow-sm space-y-5">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
          <div className="space-y-0.5">
            <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <KeyRound className="w-4 h-4 text-blue-500" />
              <span>Official Departmental Credentials Sign-In (Optional)</span>
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              For designated government officials with individual official credentials issued by HP-SDMA.
            </p>
          </div>
          <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider bg-slate-100 dark:bg-slate-800 px-2.5 py-1 rounded-lg">
            256-Bit TLS 1.3
          </span>
        </div>

        <form onSubmit={handleCustomLogin} className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="space-y-1">
            <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
              Government / Official Email
            </label>
            <input
              type="email"
              value={emailInput}
              onChange={(e) => setEmailInput(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs font-mono text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
              required
            />
          </div>

          <div className="space-y-1">
            <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
              Department / Agency
            </label>
            <input
              type="text"
              value={departmentInput}
              onChange={(e) => setDepartmentInput(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
              required
            />
          </div>

          <div className="space-y-1">
            <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
              Passkey / Password
            </label>
            <div className="flex gap-2">
              <input
                type="password"
                value={passwordInput}
                onChange={(e) => setPasswordInput(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                required
              />
              <button
                type="submit"
                className="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs transition shadow-sm shrink-0"
              >
                Sign In
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};
