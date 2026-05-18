import { Navigate, Route, Routes } from "react-router-dom";

import Sidebar from "./components/Sidebar.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Workspace from "./pages/Workspace.jsx";
import ModelChat from "./pages/ModelChat.jsx";

export default function App() {
  return (
    <div className="min-h-screen bg-paper text-ink">
      <div className="flex min-h-screen">
        <Sidebar />
        <main className="flex min-w-0 flex-1 flex-col">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/workspace" element={<Workspace />} />
            <Route path="/upload" element={<Navigate to="/workspace?tab=documents" replace />} />
            <Route path="/chat" element={<Navigate to="/workspace?tab=chat" replace />} />
            <Route path="/model-chat" element={<ModelChat />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}
