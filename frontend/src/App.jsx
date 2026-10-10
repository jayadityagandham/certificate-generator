import { NavLink, Route, Routes } from "react-router-dom";
import SubmitPage from "./pages/SubmitPage";
import JobsPage from "./pages/JobsPage";
import JobDetailPage from "./pages/JobDetailPage";
import VerifyPage from "./pages/VerifyPage";

export default function App() {
  return (
    <>
      <header className="topbar">
        <div className="topbar-inner">
          <span className="brand">Certificate generator</span>
          <nav>
            <NavLink to="/" end>New batch</NavLink>
            <NavLink to="/jobs">Jobs</NavLink>
          </nav>
        </div>
      </header>
      <main className="page">
        <Routes>
          <Route path="/" element={<SubmitPage />} />
          <Route path="/jobs" element={<JobsPage />} />
          <Route path="/jobs/:id" element={<JobDetailPage />} />
          <Route path="/verify/:token" element={<VerifyPage />} />
          <Route path="*" element={<p>Page not found.</p>} />
        </Routes>
      </main>
    </>
  );
}
