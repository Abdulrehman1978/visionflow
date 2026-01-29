import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Dashboard from './components/Dashboard'
import CoursePage from './pages/CoursePage'
import PlayerPage from './pages/PlayerPage'
import { AuthProvider } from './context/AuthContext'

function App() {
    return (
        <AuthProvider>
            <BrowserRouter>
                <div className="min-h-screen bg-background text-gray-100 font-sans">
                    <Routes>
                        <Route path="/" element={<Dashboard />} />
                        <Route path="/course/:courseId" element={<CoursePage />} />
                        <Route path="/player/:lessonId" element={<PlayerPage />} />
                    </Routes>
                </div>
            </BrowserRouter>
        </AuthProvider>
    )
}

export default App
