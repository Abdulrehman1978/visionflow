import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { BookOpen, ChevronDown, ChevronRight, Play, ArrowLeft, Clock } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function CoursePage() {
    const { courseId } = useParams();
    const navigate = useNavigate();
    const { user } = useAuth();

    const [course, setCourse] = useState(null);
    const [loading, setLoading] = useState(true);
    const [expandedModules, setExpandedModules] = useState({});
    const [completedLessons, setCompletedLessons] = useState([]);

    useEffect(() => {
        // Fetch course details
        fetch(`/api/courses/${courseId}`)
            .then(res => res.json())
            .then(data => {
                setCourse(data);
                // Expand first module by default
                if (data.modules && data.modules.length > 0) {
                    setExpandedModules({ 0: true });
                }
            })
            .catch(console.error)
            .finally(() => setLoading(false));

        // Fetch user progress if logged in
        if (user) {
            fetch('/api/progress')
                .then(res => res.json())
                .then(data => setCompletedLessons(data))
                .catch(console.error);
        }
    }, [courseId, user]);

    const toggleModule = (index) => {
        setExpandedModules(prev => ({
            ...prev,
            [index]: !prev[index]
        }));
    };

    const handleLessonClick = (lessonId) => {
        navigate(`/player/${lessonId}`);
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-background flex items-center justify-center">
                <div className="text-gray-400 animate-pulse">Loading course...</div>
            </div>
        );
    }

    if (!course) {
        return (
            <div className="min-h-screen bg-background flex items-center justify-center">
                <div className="text-center">
                    <h2 className="text-2xl font-bold text-gray-100 mb-4">Course not found</h2>
                    <Link to="/" className="text-primary hover:underline">Back to Dashboard</Link>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-background text-gray-100">
            {/* Header */}
            <header className="bg-surface border-b border-gray-800 sticky top-0 z-10">
                <div className="max-w-5xl mx-auto px-6 py-4">
                    <Link to="/" className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors mb-4">
                        <ArrowLeft className="w-4 h-4" />
                        <span>Back to Dashboard</span>
                    </Link>
                    <div className="flex items-start gap-4">
                        <div className="w-16 h-16 bg-primary/20 rounded-xl flex items-center justify-center flex-shrink-0">
                            <BookOpen className="w-8 h-8 text-primary" />
                        </div>
                        <div>
                            <h1 className="text-2xl font-bold">{course.title}</h1>
                            <p className="text-gray-400 mt-1">{course.description}</p>
                        </div>
                    </div>
                </div>
            </header>

            {/* Syllabus Content */}
            <main className="max-w-5xl mx-auto px-6 py-8">
                <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
                    <BookOpen className="w-5 h-5 text-primary" />
                    Course Syllabus
                </h2>

                <div className="space-y-4">
                    {course.modules && course.modules.map((module, moduleIndex) => (
                        <div key={moduleIndex} className="bg-surface border border-gray-800 rounded-xl overflow-hidden">
                            {/* Module Header */}
                            <button
                                onClick={() => toggleModule(moduleIndex)}
                                className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-800/50 transition-colors"
                            >
                                <div className="flex items-center gap-3">
                                    <div className="w-8 h-8 bg-primary/20 rounded-lg flex items-center justify-center text-primary font-bold text-sm">
                                        {moduleIndex + 1}
                                    </div>
                                    <span className="font-semibold text-lg">{module.title}</span>
                                    <span className="text-gray-500 text-sm">
                                        ({module.topics?.length || 0} lessons)
                                    </span>
                                </div>
                                {expandedModules[moduleIndex] ? (
                                    <ChevronDown className="w-5 h-5 text-gray-400" />
                                ) : (
                                    <ChevronRight className="w-5 h-5 text-gray-400" />
                                )}
                            </button>

                            {/* Lessons List */}
                            {expandedModules[moduleIndex] && (
                                <div className="border-t border-gray-800">
                                    {module.topics && module.topics.map((lesson, lessonIndex) => {
                                        const isCompleted = completedLessons.includes(lesson.name);
                                        return (
                                            <button
                                                key={lesson.id || lessonIndex}
                                                onClick={() => handleLessonClick(lesson.id)}
                                                className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-800/30 transition-colors border-b border-gray-800/50 last:border-b-0"
                                            >
                                                <div className="flex items-center gap-4">
                                                    <div className={`w-8 h-8 rounded-full flex items-center justify-center ${isCompleted
                                                            ? 'bg-green-500/20 text-green-500'
                                                            : 'bg-gray-800 text-gray-400'
                                                        }`}>
                                                        <Play className="w-4 h-4" />
                                                    </div>
                                                    <div className="text-left">
                                                        <p className={`font-medium ${isCompleted ? 'text-green-500' : 'text-gray-200'}`}>
                                                            {lesson.name}
                                                        </p>
                                                        {lesson.duration && (
                                                            <p className="text-sm text-gray-500 flex items-center gap-1 mt-1">
                                                                <Clock className="w-3 h-3" />
                                                                {lesson.duration}
                                                            </p>
                                                        )}
                                                    </div>
                                                </div>
                                                <ChevronRight className="w-5 h-5 text-gray-600" />
                                            </button>
                                        );
                                    })}
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            </main>
        </div>
    );
}
