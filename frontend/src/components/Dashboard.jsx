import React, { useState, useEffect } from 'react';
import { BookOpen, Play, Layout, Settings, Search, ChevronRight, GraduationCap, Video, CheckCircle, Clock, LogIn, LogOut } from 'lucide-react';
import LessonView from './LessonView';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { useAuth } from '../context/AuthContext';

function cn(...inputs) {
    return twMerge(clsx(inputs));
}

export default function Dashboard() {
    const { user, login, logout, loading } = useAuth();
    const [activeTab, setActiveTab] = useState('dashboard');
    const [selectedLanguage, setSelectedLanguage] = useState(null);
    const [syllabus, setSyllabus] = useState([]);
    const [selectedTopic, setSelectedTopic] = useState(null);
    const [selectedLesson, setSelectedLesson] = useState(null);
    const [loadingSyllabus, setLoadingSyllabus] = useState(false);
    const [completedTopics, setCompletedTopics] = useState([]);

    const [courses, setCourses] = useState([]);

    useEffect(() => {
        // Fetch Courses
        fetch('/api/courses')
            .then(res => res.json())
            .then(data => {
                // Add color mapping for UI since backend doesn't store it yet? Or just cycle colors.
                // For now let's map known IDs or random colors
                const colors = ['bg-yellow-500', 'bg-orange-600', 'bg-blue-600', 'bg-green-600', 'bg-purple-600'];
                const coursesWithUI = data.map((c, i) => ({
                    ...c,
                    color: colors[i % colors.length],
                    name: c.title // Mapping title to name for existing UI
                }));
                setCourses(coursesWithUI);
            })
            .catch(console.error);

        if (user) {
            fetch('/api/progress')
                .then(res => res.json())
                .then(data => setCompletedTopics(data))
                .catch(console.error);
        }
    }, [user]);

    const handleCourseSelect = async (courseId) => {
        setSelectedLanguage(courseId);
        setSyllabus([]);
        setSelectedTopic(null);
        setSelectedLesson(null);
        setActiveTab('lesson');

        setLoadingSyllabus(true);
        try {
            const response = await fetch('/api/courses/' + courseId);
            const data = await response.json();

            if (data.modules) {
                // Store full lesson objects with IDs
                const allLessons = data.modules.flatMap(m =>
                    m.topics.map(t => ({
                        id: t.id,
                        name: t.name,
                        video_id: t.video_id,
                        duration: t.duration,
                        quiz_count: t.quiz_count || 0,
                        practice_count: t.practice_count || 0
                    }))
                );
                setSyllabus(allLessons);
            } else {
                setSyllabus([]);
            }

        } catch (error) {
            console.error("Failed to fetch syllabus", error);
        } finally {
            setLoadingSyllabus(false);
        }
    };

    const handleTopicSelect = (lesson) => {
        setSelectedTopic(lesson.name);
        setSelectedLesson(lesson);
    };

    if (loading) return <div className="h-screen flex items-center justify-center">Loading...</div>;

    return (
        <div className="flex h-screen bg-background text-gray-100 overflow-hidden">
            {/* Sidebar */}
            <aside className="w-64 bg-surface border-r border-gray-800 flex flex-col">
                <div className="p-6 flex items-center space-x-3">
                    <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                        <Video className="w-5 h-5 text-white" />
                    </div>
                    <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary to-purple-400">
                        VisionFlow
                    </span>
                </div>

                <nav className="flex-1 px-4 space-y-2 mt-4">
                    <NavItem icon={<Layout />} label="Dashboard" active={activeTab === 'dashboard'} onClick={() => setActiveTab('dashboard')} />
                    <NavItem icon={<BookOpen />} label="My Lessons" active={activeTab === 'lesson'} onClick={() => setActiveTab('lesson')} />
                    <NavItem icon={<Settings />} label="Settings" active={activeTab === 'settings'} onClick={() => setActiveTab('settings')} />
                </nav>

                <div className="p-4 border-t border-gray-800">
                    {user ? (
                        <div className="bg-gray-800/50 rounded-xl p-4">
                            <div className="flex items-center space-x-3 mb-3">
                                {user.avatar ? (
                                    <img src={user.avatar} className="w-10 h-10 rounded-full" alt="Avatar" />
                                ) : (
                                    <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-primary to-purple-500" />
                                )}
                                <div className="overflow-hidden">
                                    <p className="font-medium text-sm truncate">{user.name}</p>
                                    <p className="text-xs text-gray-400 truncate">{user.email}</p>
                                </div>
                            </div>
                            <button onClick={logout} className="w-full mt-2 text-xs text-red-400 hover:text-red-300 flex items-center gap-1 justify-center">
                                <LogOut size={12} /> Logout
                            </button>
                        </div>
                    ) : (
                        <button onClick={login} className="w-full bg-primary hover:bg-primary/90 text-white rounded-lg py-2 flex items-center justify-center gap-2">
                            <LogIn size={16} /> Login with Google
                        </button>
                    )}
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1 overflow-y-auto p-8 relative">
                {activeTab === 'dashboard' && (
                    <div className="max-w-5xl mx-auto space-y-8">
                        <div className="flex items-center justify-between">
                            <div>
                                <h1 className="text-3xl font-bold">Welcome back{user ? `, ${user.name.split(' ')[0]}` : '!'}</h1>
                                <p className="text-gray-400 mt-1">Ready to continue learning?</p>
                            </div>
                        </div>

                        {/* Recent Progress Section */}
                        {user && completedTopics.length > 0 && (
                            <div className="bg-surface p-6 rounded-2xl border border-gray-800">
                                <h3 className="text-xl font-bold mb-4">My Progress</h3>
                                <div className="flex flex-wrap gap-2">
                                    {completedTopics.slice(0, 5).map(topic => (
                                        <span key={topic} className="px-3 py-1 bg-green-500/10 text-green-500 border border-green-500/20 rounded-full text-sm">
                                            {topic}
                                        </span>
                                    ))}
                                    {completedTopics.length > 5 && <span className="text-gray-400 text-sm mt-1">+{completedTopics.length - 5} more</span>}
                                </div>
                            </div>
                        )}

                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                            {courses.map((course) => (
                                <div
                                    key={course.id}
                                    onClick={() => handleCourseSelect(course.id)}
                                    className="bg-surface p-6 rounded-2xl border border-gray-800 hover:border-primary/50 transition-all cursor-pointer group"
                                >
                                    <div className={cn("w-12 h-12 rounded-xl flex items-center justify-center mb-4 text-white font-bold text-xl", course.color)}>
                                        {course.name[0]}
                                    </div>
                                    <h3 className="text-xl font-bold mb-1 group-hover:text-primary transition-colors">{course.name}</h3>
                                    <p className="text-sm text-gray-400 mb-4">Master {course.name} from scratch</p>
                                    <div className="flex items-center justify-between text-xs text-gray-400">
                                        <span>Start Learning</span>
                                        <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {activeTab === 'lesson' && (
                    <div className="flex h-[calc(100vh-4rem)] gap-6">
                        {/* Syllabus Timeline */}
                        <div className="w-80 flex-shrink-0 bg-surface rounded-2xl border border-gray-800 overflow-hidden flex flex-col">
                            <div className="p-4 border-b border-gray-800 bg-gray-900/50">
                                <h2 className="font-bold text-lg flex items-center gap-2">
                                    <GraduationCap className="w-5 h-5 text-primary" />
                                    {selectedLanguage ? `${selectedLanguage} Syllabus` : 'Select a course'}
                                </h2>
                            </div>
                            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                                {loadingSyllabus ? (
                                    <div className="text-center text-gray-400 py-10 animate-pulse">Generating syllabus...</div>
                                ) : syllabus.length > 0 ? (
                                    syllabus.map((lesson, index) => {
                                        const isCompleted = completedTopics.includes(lesson.name);
                                        const isSelected = selectedLesson?.id === lesson.id;
                                        return (
                                            <div
                                                key={lesson.id || index}
                                                onClick={() => handleTopicSelect(lesson)}
                                                className={cn(
                                                    "p-4 rounded-xl border border-gray-800 cursor-pointer transition-all hover:bg-gray-800 relative pl-10",
                                                    isSelected ? "bg-primary/10 border-primary/50" : "bg-gray-900/40"
                                                )}
                                            >
                                                <div className={cn(
                                                    "absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 rounded-full border-2 flex items-center justify-center",
                                                    isCompleted ? "border-green-500" : isSelected ? "border-primary" : "border-gray-600"
                                                )}>
                                                    {isCompleted ? <div className="w-2 h-2 rounded-full bg-green-500" /> : isSelected && <div className="w-2 h-2 rounded-full bg-primary" />}
                                                </div>
                                                <div>
                                                    <p className={cn("text-sm font-medium", isSelected ? "text-primary" : isCompleted ? "text-green-500" : "text-gray-300")}>
                                                        {lesson.name}
                                                    </p>
                                                    {(lesson.quiz_count > 0 || lesson.practice_count > 0) && (
                                                        <div className="flex gap-2 mt-1">
                                                            {lesson.quiz_count > 0 && <span className="text-xs text-purple-400">📝 Quiz</span>}
                                                            {lesson.practice_count > 0 && <span className="text-xs text-blue-400">💻 Practice</span>}
                                                        </div>
                                                    )}
                                                </div>
                                            </div>
                                        )
                                    })
                                ) : (
                                    <p className="text-center text-gray-500 text-sm">Select a course to view syllabus</p>
                                )}
                            </div>
                        </div>

                        {/* Lesson View & Content */}
                        <div className="flex-1 bg-surface rounded-2xl border border-gray-800 overflow-hidden flex flex-col">
                            <LessonView
                                lessonId={selectedLesson?.id}
                                topic={selectedTopic}
                                onProgressUpdate={() => user && fetch('/api/progress').then(res => res.json()).then(setCompletedTopics)}
                            />
                        </div>
                    </div>
                )}

                {activeTab === 'settings' && (
                    <div className="flex items-center justify-center h-full text-gray-500">
                        <div className="text-center space-y-4">
                            <h2 className="text-2xl font-bold">Settings</h2>
                            <p>Manage your account settings</p>
                            <div className="flex gap-4 justify-center">
                                <button className="px-4 py-2 bg-red-500/10 text-red-500 rounded-lg hover:bg-red-500/20 border border-red-500/20">Delete Account</button>
                                <button className="px-4 py-2 bg-blue-500/10 text-blue-500 rounded-lg hover:bg-blue-500/20 border border-blue-500/20">Export Data</button>
                            </div>
                        </div>
                    </div>
                )}
            </main>
        </div>
    );
}

function NavItem({ icon, label, active, onClick }) {
    return (
        <button
            onClick={onClick}
            className={cn(
                "w-full flex items-center space-x-3 px-4 py-3 rounded-xl text-sm font-medium transition-colors",
                active
                    ? "bg-primary/10 text-primary border border-primary/20"
                    : "text-gray-400 hover:bg-gray-800 hover:text-gray-200"
            )}
        >
            {icon}
            <span>{label}</span>
        </button>
    );
}
