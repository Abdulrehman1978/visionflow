import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import YouTube from 'react-youtube';
import { ArrowLeft, CheckCircle, ChevronRight, Loader2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function PlayerPage() {
    const { lessonId } = useParams();
    const navigate = useNavigate();
    const { user, loading: authLoading } = useAuth();

    const [lesson, setLesson] = useState(null);
    const [loading, setLoading] = useState(true);
    const [marking, setMarking] = useState(false);
    const [completed, setCompleted] = useState(false);

    useEffect(() => {
        // Redirect to home if not logged in
        if (!authLoading && !user) {
            navigate('/');
            return;
        }

        if (lessonId) {
            setLoading(true);
            fetch(`/api/lessons/${lessonId}`)
                .then(res => res.json())
                .then(data => {
                    if (data.error) {
                        console.error(data.error);
                        return;
                    }
                    setLesson(data);
                    setCompleted(false);
                })
                .catch(console.error)
                .finally(() => setLoading(false));
        }
    }, [lessonId, user, authLoading, navigate]);

    const handleMarkComplete = async () => {
        if (!lesson || marking) return;

        setMarking(true);
        try {
            const response = await fetch('/api/progress/update', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({
                    topic_id: lesson.title,
                    is_completed: true
                })
            });

            if (response.ok) {
                setCompleted(true);

                // Auto-navigate to next lesson after a short delay
                if (lesson.next_lesson_id) {
                    setTimeout(() => {
                        navigate(`/player/${lesson.next_lesson_id}`);
                    }, 1000);
                }
            }
        } catch (error) {
            console.error('Failed to mark as complete:', error);
        } finally {
            setMarking(false);
        }
    };

    // YouTube player options - privacy mode with no related videos
    const opts = {
        height: '100%',
        width: '100%',
        playerVars: {
            autoplay: 0,
            rel: 0, // Minimize related videos
            modestbranding: 1,
            origin: window.location.origin
        }
    };

    if (authLoading || loading) {
        return (
            <div className="min-h-screen bg-background flex items-center justify-center">
                <div className="text-gray-400 animate-pulse flex items-center gap-2">
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Loading lesson...
                </div>
            </div>
        );
    }

    if (!user) {
        return (
            <div className="min-h-screen bg-background flex items-center justify-center">
                <div className="text-center">
                    <h2 className="text-2xl font-bold text-gray-100 mb-4">Please log in to continue</h2>
                    <Link to="/" className="text-primary hover:underline">Go to Home</Link>
                </div>
            </div>
        );
    }

    if (!lesson) {
        return (
            <div className="min-h-screen bg-background flex items-center justify-center">
                <div className="text-center">
                    <h2 className="text-2xl font-bold text-gray-100 mb-4">Lesson not found</h2>
                    <Link to="/" className="text-primary hover:underline">Back to Dashboard</Link>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-background text-gray-100">
            {/* Header */}
            <header className="bg-surface border-b border-gray-800">
                <div className="max-w-6xl mx-auto px-6 py-4">
                    <Link
                        to={`/course/${lesson.course_id}`}
                        className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors"
                    >
                        <ArrowLeft className="w-4 h-4" />
                        <span>Back to Course</span>
                    </Link>
                </div>
            </header>

            {/* Main Content */}
            <main className="max-w-6xl mx-auto px-6 py-8">
                {/* Lesson Info */}
                <div className="mb-6">
                    <p className="text-sm text-primary mb-1">{lesson.module_title}</p>
                    <h1 className="text-2xl font-bold">{lesson.title}</h1>
                    {lesson.duration && (
                        <p className="text-gray-400 mt-1">Duration: {lesson.duration}</p>
                    )}
                </div>

                {/* Video Player Container */}
                <div className="relative bg-black rounded-xl overflow-hidden mb-8" style={{ paddingBottom: '56.25%' }}>
                    <div className="absolute inset-0">
                        <YouTube
                            videoId={lesson.video_url}
                            opts={opts}
                            className="w-full h-full"
                            iframeClassName="w-full h-full"
                        // Use youtube-nocookie for privacy
                        // Note: react-youtube uses youtube.com by default, 
                        // but we can't change the host directly. The rel=0 helps minimize distractions.
                        />
                    </div>
                </div>

                {/* Control Buttons */}
                <div className="flex flex-col sm:flex-row items-center gap-4 justify-center">
                    {/* Mark as Complete Button */}
                    <button
                        onClick={handleMarkComplete}
                        disabled={marking || completed}
                        className={`
                            flex items-center gap-3 px-8 py-4 rounded-xl font-semibold text-lg transition-all
                            ${completed
                                ? 'bg-green-500/20 text-green-500 border border-green-500/30 cursor-default'
                                : 'bg-primary hover:bg-primary/90 text-white shadow-lg shadow-primary/25 hover:shadow-primary/40'
                            }
                            ${marking ? 'opacity-70 cursor-wait' : ''}
                        `}
                    >
                        {marking ? (
                            <>
                                <Loader2 className="w-6 h-6 animate-spin" />
                                Marking...
                            </>
                        ) : completed ? (
                            <>
                                <CheckCircle className="w-6 h-6" />
                                Completed!
                                {lesson.next_lesson_id && <span className="text-sm ml-2">Redirecting...</span>}
                            </>
                        ) : (
                            <>
                                <CheckCircle className="w-6 h-6" />
                                Mark as Complete
                            </>
                        )}
                    </button>

                    {/* Next Lesson Button (shown when not auto-redirecting) */}
                    {lesson.next_lesson_id && !completed && (
                        <Link
                            to={`/player/${lesson.next_lesson_id}`}
                            className="flex items-center gap-2 px-6 py-4 rounded-xl font-medium text-gray-300 hover:text-white border border-gray-700 hover:border-gray-600 transition-all"
                        >
                            Skip to Next
                            <ChevronRight className="w-5 h-5" />
                        </Link>
                    )}

                    {/* Course Complete Message */}
                    {!lesson.next_lesson_id && completed && (
                        <div className="text-center">
                            <p className="text-green-400 font-semibold mb-2">🎉 Congratulations! You've completed this course!</p>
                            <Link to={`/course/${lesson.course_id}`} className="text-primary hover:underline">
                                Back to Course Overview
                            </Link>
                        </div>
                    )}
                </div>
            </main>
        </div>
    );
}
