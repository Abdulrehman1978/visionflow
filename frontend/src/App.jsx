import Dashboard from './components/Dashboard'
import { AuthProvider } from './context/AuthContext'

function App() {
    return (
        <AuthProvider>
            <div className="min-h-screen bg-background text-gray-100 font-sans">
                <Dashboard />
            </div>
        </AuthProvider>
    )
}

export default App
