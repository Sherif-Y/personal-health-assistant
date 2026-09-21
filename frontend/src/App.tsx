import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { Labs } from "./pages/Labs";
import { Trends } from "./pages/Trends";
import { Reports } from "./pages/Reports";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Labs />} />
        <Route path="/trends" element={<Trends />} />
        <Route path="/reports" element={<Reports />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
