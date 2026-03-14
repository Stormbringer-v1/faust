import type { FC } from 'react';

export const TopBar: FC = () => {
  return (
    <header className="flex items-center justify-between px-8 py-4 bg-surface-dim ghost-border border-b border-transparent z-10 relative shadow-[0_12px_40px_rgba(6,14,32,0.06)]">
      {/* Search */}
      <label className="flex items-center bg-surface-container-high rounded-full h-10 px-4 w-96 max-w-full focus-within:bg-surface-container-highest focus-within:ring-1 focus-within:ring-primary/20 transition-all">
        <span className="material-symbols-outlined text-on-surface-variant mr-2 text-[20px]">search</span>
        <input 
          className="w-full bg-transparent border-none text-on-surface text-sm focus:outline-none focus:ring-0 placeholder:text-on-surface-variant" 
          placeholder="Search assets, IP, CVE..." 
          type="text"
        />
      </label>
      {/* Profile & Actions */}
      <div className="flex items-center gap-6">
        <button className="text-on-surface-variant hover:text-primary transition-colors relative">
          <span className="material-symbols-outlined">notifications</span>
          <span className="absolute top-0 right-0 w-2 h-2 bg-error rounded-full block"></span>
        </button>
        <button className="text-on-surface-variant hover:text-primary transition-colors">
          <span className="material-symbols-outlined">settings</span>
        </button>
        <div 
          className="h-8 w-8 rounded-full bg-surface-container-high bg-cover bg-center border border-outline-variant/30 cursor-pointer" 
          title="User Avatar" 
          style={{ backgroundImage: 'url("https://lh3.googleusercontent.com/aida-public/AB6AXuA7CqswaaVFpVg0gxxVirxTLBAYRPaNnZ-aXL-yLcnmPSLVf-S_Pg0p9mHAzyQIArj-4lKLAX1UaWr6mtxO9plq4bNXiqANPHcGlC6ZRylgrMRFRk_OmjsAncdI2dIrajUs-mxlTvqc5MTLDdRa4oeTIjDOUQ8m1OtfMTVhNwgxTORoL3tz6skrmuGzMVpn0qNlcLv7KikVODkrVvfwbEE-eGmsrlEEtwAfUWHmCzkGqu9rZ-uaQlY7Jf45w1_xT-18HGlmvW8Fm7k")' }}
        ></div>
      </div>
    </header>
  );
};
