import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { Login } from "./pages/Login";
import { Register } from "./pages/Register";
import { Dashboard } from "./pages/Dashboard";
import { People } from "./pages/People";
import { PersonDetail } from "./pages/PersonDetail";
import { Tasks } from "./pages/Tasks";
import { Vocabularies } from "./pages/Vocabularies";
import { Settings } from "./pages/Settings";

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/people"
            element={
              <ProtectedRoute>
                <People />
              </ProtectedRoute>
            }
          />
          <Route
            path="/people/:id"
            element={
              <ProtectedRoute>
                <PersonDetail />
              </ProtectedRoute>
            }
          />
          <Route
            path="/vocabulary"
            element={
              <ProtectedRoute>
                <Vocabularies />
              </ProtectedRoute>
            }
          />
          <Route
            path="/tasks"
            element={
              <ProtectedRoute>
                <Tasks />
              </ProtectedRoute>
            }
          />
          <Route
            path="/settings"
            element={
              <ProtectedRoute>
                <Settings />
              </ProtectedRoute>
            }
          />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
