import React, { useState, useEffect } from 'react';
import { BookOpen, Play, Layout, Settings, Search, ChevronRight, GraduationCap, Video, CheckCircle, Clock } from 'lucide-react';
import VideoPlayer from './VideoPlayer';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs) {
    return twMerge(clsx(inputs));
}

export default function Dashboard() {
    const [activeTab, setActiveTab] = useState('dashboard');
    const [selectedLanguage, setSelectedLanguage] = useState(null);
    const [syllabus, setSyllabus] = useState([]);
    const [selectedTopic, setSelectedTopic] = useState(null);
    const [loadingSyllabus, setLoadingSyllabus] = useState(false);

    const courses = [
        { id: 'python', name: 'Python', color: 'bg-yellow-500', progress: 0 },
        { id: 'java', name: 'Java', color: 'bg-orange-600', progress: 0 },
        { id: 'cpp', name: 'C++', color: 'bg-blue-600', progress: 0 },
    ];

    const handleCourseSelect = async (courseId) => {
        setSelectedLanguage(courseId);
        setSyllabus([]);
        setSelectedTopic(null);
        setActiveTab('lesson');

        setLoadingSyllabus(true);
        try {
            const response = await fetch('/api/syllabus?language=' + courseId);
            const data = await response.json();
            if (data.modules) {
                // Flatten modules to topics for the timeline list provided in the prompt's simplicity,
                // but the prompt asked to flatten generated topics.
                // The backend now returns structured modules. I should probably adapt the timeline to display modules or just flatten them.
                // For now, I'll flatten them to simple list as the UI expects a list of topics.
                const allTopics = data.modules.flatMap(m => m.topics.map(t => t.name));
                setSyllabus(allTopics);
            } else if (data.topics) {
                setSyllabus(data.topics);
            }
        } catch (error) {
            console.error("Failed to fetch syllabus", error);
        } finally {
            setLoadingSyllabus(false);
        }
    };

    const handleTopicSelect = (topic) => {
        setSelectedTopic(topic);
    };

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
                    <div className="bg-gray-800/50 rounded-xl p-4">
                        <div className="flex items-center space-x-3 mb-3">
                            <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-primary to-purple-500" />
                            <div>
                                <p className="font-medium text-sm">Student</p>
                                <p className="text-xs text-gray-400">Pro Plan</p>
                            </div>
                        </div>
                        <div className="h-1.5 w-full bg-gray-700 rounded-full overflow-hidden">
                            <div className="h-full bg-primary w-[75%]" />
                        </div>
                        <p className="text-xs text-gray-400 mt-2 text-right">75% Complete</p>
                    </div>
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1 overflow-y-auto p-8 relative">
                {activeTab === 'dashboard' && (
                    <div className="max-w-5xl mx-auto space-y-8">
                        <div className="flex items-center justify-between">
                            <div>
                                <h1 className="text-3xl font-bold">Welcome back!</h1>
                                <p className="text-gray-400 mt-1">Ready to continue learning?</p>
                            </div>
                            <div className="relative">
                                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                                <input
                                    type="text"
                                    placeholder="Search courses..."
                                    className="bg-surface pl-10 pr-4 py-2 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 w-64 border border-gray-800"
                                />
                            </div>
                        </div>

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
                                        <span>{course.progress}% Completed</span>
                                        <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                                    </div>
                                    <div className="mt-3 h-1.5 w-full bg-gray-800 rounded-full overflow-hidden">
                                        <div className="h-full bg-primary" style={{ width: `${course.progress}%` }} />
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
                                    syllabus.map((topic, index) => (
                                        <div
                                            key={index}
                                            onClick={() => handleTopicSelect(topic)}
                                            className={cn(
                                                "p-4 rounded-xl border border-gray-800 cursor-pointer transition-all hover:bg-gray-800 relative pl-10",
                                                selectedTopic === topic ? "bg-primary/10 border-primary/50" : "bg-gray-900/40"
                                            )}
                                        >
                                            <div className={cn(
                                                "absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 rounded-full border-2 flex items-center justify-center",
                                                selectedTopic === topic ? "border-primary" : "border-gray-600"
                                            )}>
                                                {selectedTopic === topic && <div className="w-2 h-2 rounded-full bg-primary" />}
                                            </div>
                                            <p className={cn("text-sm font-medium", selectedTopic === topic ? "text-primary" : "text-gray-300")}>
                                                {topic}
                                            </p>
                                        </div>
                                    ))
                                ) : (
                                    <p className="text-center text-gray-500 text-sm">Select a course to view syllabus</p>
                                )}
                            </div>
                        </div>

                        {/* Video Player & Content */}
                        <div className="flex-1 bg-surface rounded-2xl border border-gray-800 overflow-hidden flex flex-col">
                            <VideoPlayer topic={selectedTopic} />
                        </div>
                    </div>
                )}

                {activeTab === 'settings' && (
                    <div className="flex items-center justify-center h-full text-gray-500">Settings Page</div>
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
