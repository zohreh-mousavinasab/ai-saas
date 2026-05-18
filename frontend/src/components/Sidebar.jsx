import { Bot, LayoutDashboard, PanelsTopLeft } from "lucide-react";
import { NavLink } from "react-router-dom";

const navigation = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/workspace", label: "Document Chat", icon: PanelsTopLeft },
  { to: "/model-chat", label: "Model Chat", icon: Bot },
];

export default function Sidebar() {
  return (
    <aside className="hidden w-64 shrink-0 border-r border-ink/10 bg-white px-4 py-5 md:block">
      <div className="mb-8 px-2">
        <p className="text-lg font-semibold tracking-normal">DocMind AI</p>
        <p className="mt-1 text-sm text-ink/60">Private document Q&A</p>
      </div>

      <nav className="space-y-1">
        {navigation.map((item) => {
          const Icon = item.icon;

          return (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                [
                  "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition",
                  isActive
                    ? "bg-moss text-white"
                    : "text-ink/70 hover:bg-ink/5 hover:text-ink",
                ].join(" ")
              }
            >
              <Icon aria-hidden="true" className="size-4" />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>
    </aside>
  );
}
