import React, { useState } from 'react';
import {
  BookOpen,
  CheckSquare,
  Square,
  Phone,
  Shield,
  LifeBuoy,
  FileText,
  AlertTriangle,
} from 'lucide-react';

export const PreparednessPage: React.FC = () => {
  const [checkedItems, setCheckedItems] = useState<{ [key: string]: boolean }>({
    item1: true,
    item2: true,
  });

  const toggleItem = (id: string) => {
    setCheckedItems((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const checklist = [
    { id: 'item1', title: 'Water Purification Tablets & 3L Bottled Water', desc: 'Silt and turbidity in floodwaters render tap water unsafe.' },
    { id: 'item2', title: 'Waterproof Document Pouch', desc: 'Aadhaar, property deeds, identity cards, emergency insurance policies.' },
    { id: 'item3', title: 'Heavy Duty LED Flashlight & Spare 18650 Batteries', desc: 'Power grids are preemptively disconnected in flash floods.' },
    { id: 'item4', title: 'High-Calorie Non-Perishable Food (3 Days)', desc: 'Nuts, dried fruits, energy bars, roasted gram.' },
    { id: 'item5', title: 'Comprehensive Mountain First Aid Kit', desc: 'Bandages, antiseptic solution, ORS packets, personal prescription drugs.' },
    { id: 'item6', title: 'Thermal Emergency Blanket & Rain Poncho', desc: 'Hypothermia risk increases rapidly in glacial mountain runoff.' },
    { id: 'item7', title: 'Portable AM/FM / NOAA Weather Radio', desc: 'For emergency civil defense bulletins when cell towers go offline.' },
    { id: 'item8', title: 'Sturdy Waterproof Hiking Boots', desc: 'Required for walking through slippery shale and colluvium paths.' },
  ];

  const helplines = [
    { name: 'Himachal Pradesh State Emergency Ops (SEOC)', number: '1070', desc: '24/7 State Disaster Control' },
    { name: 'Kullu District Disaster Management (DEOC)', number: '1077', desc: 'District Magistrate Command Desk' },
    { name: 'National Disaster Response Force (NDRF)', number: '011-24363260', desc: 'Search & Rescue Battalion' },
    { name: 'Manali Police Station (Mall Road)', number: '01902-252322', desc: 'Local Emergency Dispatch' },
    { name: 'Civil Hospital Manali (Medical Helpline)', number: '01902-252338', desc: 'Trauma & Emergency Ward' },
    { name: 'Himachal Fire Services Emergency', number: '101', desc: 'Fire & Flood Rescue Units' },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white dark:bg-slate-900 p-6 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-1">
        <span className="text-xs font-mono font-bold uppercase tracking-wider text-blue-500">
          COMMUNITY RESILIENCE & PREPAREDNESS DIRECTORY
        </span>
        <h1 className="text-2xl font-extrabold text-slate-900 dark:text-white">
          Mountain Flash Flood Preparedness & Helplines
        </h1>
        <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-300">
          Essential survival protocols, go-bag checklists, and verified local contact channels for the Upper Beas Valley community.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Columns: Go-Bag Checklist & Flood Rules */}
        <div className="lg:col-span-2 space-y-6">
          {/* Go Bag Checklist */}
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 sm:p-8 space-y-5 shadow-sm">
            <div className="flex items-center justify-between pb-3 border-b border-slate-200 dark:border-slate-800">
              <div>
                <h2 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <LifeBuoy className="w-5 h-5 text-blue-500" />
                  <span>72-Hour "Go-Bag" Evacuation Checklist</span>
                </h2>
                <p className="text-xs text-slate-500 mt-0.5">
                  Pack items in a rugged waterproof backpack before monsoon cloudburst season.
                </p>
              </div>
              <span className="text-xs font-mono font-bold px-2.5 py-1 rounded-full bg-blue-500/10 text-blue-500">
                {Object.values(checkedItems).filter(Boolean).length} / {checklist.length} Packed
              </span>
            </div>

            <div className="space-y-3">
              {checklist.map((item) => {
                const isChecked = !!checkedItems[item.id];
                return (
                  <div
                    key={item.id}
                    onClick={() => toggleItem(item.id)}
                    className={`p-3.5 rounded-2xl border transition cursor-pointer flex items-start gap-3.5 ${
                      isChecked
                        ? 'bg-emerald-500/5 border-emerald-500/30'
                        : 'bg-slate-50 dark:bg-slate-800/50 border-slate-200 dark:border-slate-800'
                    }`}
                  >
                    <button className="mt-0.5 text-emerald-500 flex-shrink-0">
                      {isChecked ? <CheckSquare className="w-5 h-5" /> : <Square className="w-5 h-5 text-slate-400" />}
                    </button>
                    <div>
                      <div className={`text-xs font-bold ${isChecked ? 'line-through text-slate-400 dark:text-slate-500' : 'text-slate-800 dark:text-slate-200'}`}>
                        {item.title}
                      </div>
                      <div className="text-[11px] text-slate-500 mt-0.5">{item.desc}</div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Critical Survival Rules */}
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 sm:p-8 space-y-4 shadow-sm">
            <h3 className="font-bold text-base text-slate-900 dark:text-white flex items-center gap-2">
              <Shield className="w-5 h-5 text-emerald-500" />
              <span>Core Mountain Flood Survival Directives</span>
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
              <div className="p-3.5 rounded-2xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/70 space-y-1">
                <div className="font-bold text-red-500 uppercase text-[10px]">Rule 1: Never Cross Flowing Runoff</div>
                <p className="text-slate-600 dark:text-slate-300">
                  Just 15 cm of rapid water can knock over an adult; 30 cm will float small vehicles.
                </p>
              </div>

              <div className="p-3.5 rounded-2xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/70 space-y-1">
                <div className="font-bold text-emerald-500 uppercase text-[10px]">Rule 2: Climb to Stable Ridge Ground</div>
                <p className="text-slate-600 dark:text-slate-300">
                  Head immediately for rocky ridges (e.g. Hadimba temple ridge) rather than staying in valley floors.
                </p>
              </div>

              <div className="p-3.5 rounded-2xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/70 space-y-1">
                <div className="font-bold text-amber-500 uppercase text-[10px]">Rule 3: Beware Tributary Debris Outbursts</div>
                <p className="text-slate-600 dark:text-slate-300">
                  A sudden lull in river flow during heavy rain often signifies an upstream debris damming — prepare for immediate surge!
                </p>
              </div>

              <div className="p-3.5 rounded-2xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/70 space-y-1">
                <div className="font-bold text-blue-500 uppercase text-[10px]">Rule 4: Conserve Phone Battery</div>
                <p className="text-slate-600 dark:text-slate-300">
                  Switch to power-saving mode. Use SMS or HILL-SAFE offline mesh rather than high-bandwidth voice calls.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Emergency Helplines Directory */}
        <div className="space-y-4">
          <div className="text-xs font-bold uppercase tracking-wider text-slate-500 px-1">
            Emergency Contacts Directory
          </div>

          <div className="space-y-2.5">
            {helplines.map((hl, idx) => (
              <div
                key={idx}
                className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-4 shadow-sm space-y-1"
              >
                <div className="text-xs font-bold text-slate-800 dark:text-slate-200">
                  {hl.name}
                </div>
                <div className="text-[11px] text-slate-400">{hl.desc}</div>
                <div className="pt-2 flex items-center justify-between">
                  <a
                    href={`tel:${hl.number}`}
                    className="flex items-center gap-1.5 font-mono text-sm font-bold text-emerald-600 dark:text-emerald-400 hover:underline"
                  >
                    <Phone className="w-3.5 h-3.5" />
                    <span>{hl.number}</span>
                  </a>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-500 font-bold">
                    TOLL-FREE / 24x7
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
