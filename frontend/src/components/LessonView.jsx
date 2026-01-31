import React, { useState, useEffect } from 'react';
import { Play, CheckCircle, BookOpen, Code, Trophy, Lightbulb, AlertCircle } from 'lucide-react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { useAuth } from '../context/AuthContext';

function cn(...inputs) {
    return twMerge(clsx(inputs));
}

export default function LessonView({ lessonId, topic, onProgressUpdate }) {
    const { user } = useAuth();
    const [lesson, setLesson] = useState(null);
    const [loading, setLoading] = useState(false);
    const [activeTab, setActiveTab] = useState('video');
    const [videoCompleted, setVideoCompleted] = useState(false);
    const [quizCompleted, setQuizCompleted] = useState(false);

    // Quiz state
    const [selectedAnswer, setSelectedAnswer] = useState(null);
    const [quizResult, setQuizResult] = useState(null);

    useEffect(() => {
        if (!lessonId && !topic) return;

        const fetchLesson = async () => {
            setLoading(true);
            setLesson(null);
            setSelectedAnswer(null);
            setQuizResult(null);

            try {
                if (lessonId) {
                    // Fetch from new endpoint with quiz/practice data
                    const response = await fetch(`/api/lessons/${lessonId}`);
                    if (!response.ok) throw new Error('Lesson not found');
                    const data = await response.json();
                    setLesson(data);
                } else if (topic) {
                    // Fallback: fetch video only (legacy support)
                    const response = await fetch(`/api/videos?topic=${encodeURIComponent(topic)}`);
                    const videos = await response.json();
                    if (videos && videos.length > 0) {
                        setLesson({
                            title: topic,
                            video_id: videos[0].id,
                            quizzes: [],
                            practice_questions: []
                        });
                    }
                }

                // Check completion status
                if (user) {
                    fetch('/api/progress')
                        .then(res => res.json())
                        .then(data => {
                            if (data.includes(topic)) {
                                setVideoCompleted(true);
                            }
                        })
                        .catch(console.error);
                }
            } catch (error) {
                console.error("Failed to fetch lesson:", error);
            } finally {
                setLoading(false);
            }
        };

        fetchLesson();
    }, [lessonId, topic, user]);

    const handleMarkCompleted = async () => {
        if (!user) {
            alert("Please login to save progress");
            return;
        }

        const newState = !videoCompleted;
        setVideoCompleted(newState);

        try {
            const res = await fetch('/api/progress/update', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    topic_id: topic || lesson?.title,
                    lesson_id: lessonId,
                    video_completed: newState,
                    is_completed: newState && quizCompleted
                })
            });
            if (res.ok && onProgressUpdate) {
                onProgressUpdate();
            }
        } catch (error) {
            console.error("Failed to update progress:", error);
            setVideoCompleted(!newState);
        }
    };

    const handleQuizAnswer = (option) => {
        if (quizResult) return; // Already answered

        setSelectedAnswer(option);
        const quiz = lesson?.quizzes?.[0];
        if (!quiz) return;

        const isCorrect = option === quiz.correct_answer;
        setQuizResult(isCorrect ? 'correct' : 'incorrect');

        if (isCorrect && user) {
            setQuizCompleted(true);
            // Update quiz completion
            fetch('/api/progress/update', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    topic_id: topic || lesson?.title,
                    lesson_id: lessonId,
                    quiz_completed: true,
                    is_completed: videoCompleted && true
                })
            }).catch(console.error);
        }
    };

    if (!lessonId && !topic) {
        return (
            <div className="flex-1 flex flex-col items-center justify-center text-gray-500 space-y-4 h-full">
                <div className="w-16 h-16 bg-gray-800 rounded-2xl flex items-center justify-center">
                    <Play className="w-8 h-8 text-gray-600" />
                </div>
                <p>Select a lesson to start learning</p>
            </div>
        );
    }

    if (loading) {
        return (
            <div className="flex-1 flex items-center justify-center h-full">
                <div className="animate-spin w-8 h-8 border-2 border-primary border-t-transparent rounded-full" />
            </div>
        );
    }

    if (!lesson) {
        return <div className="p-6 text-center text-gray-400">Lesson not available.</div>;
    }

    const hasQuiz = lesson.quizzes && lesson.quizzes.length > 0;
    const hasPractice = lesson.practice_questions && lesson.practice_questions.length > 0;

    return (
        <div className="flex-1 flex flex-col h-full overflow-hidden">
            {/* Tab Navigation */}
            <div className="flex-shrink-0 border-b border-gray-800 bg-gray-900/50">
                <div className="flex gap-1 p-2">
                    <TabButton
                        icon={<Play className="w-4 h-4" />}
                        label="Video"
                        active={activeTab === 'video'}
                        onClick={() => setActiveTab('video')}
                        badge={videoCompleted ? <CheckCircle className="w-3 h-3 text-green-500" /> : null}
                    />
                    {hasQuiz && (
                        <TabButton
                            icon={<Trophy className="w-4 h-4" />}
                            label="Quiz"
                            active={activeTab === 'quiz'}
                            onClick={() => setActiveTab('quiz')}
                            badge={quizCompleted ? <CheckCircle className="w-3 h-3 text-green-500" /> : null}
                        />
                    )}
                    {hasPractice && (
                        <TabButton
                            icon={<Code className="w-4 h-4" />}
                            label="Practice"
                            active={activeTab === 'practice'}
                            onClick={() => setActiveTab('practice')}
                        />
                    )}
                </div>
            </div>

            {/* Tab Content */}
            <div className="flex-1 overflow-y-auto">
                {activeTab === 'video' && (
                    <div className="flex flex-col h-full">
                        {/* Video Player */}
                        <div className="aspect-video w-full bg-black relative flex-shrink-0">
                            <iframe
                                src={`https://www.youtube.com/embed/${lesson.video_id}`}
                                className="w-full h-full"
                                allowFullScreen
                                title="Video player"
                            />
                        </div>

                        {/* Video Info */}
                        <div className="p-6 space-y-4">
                            <div className="flex items-start justify-between">
                                <div>
                                    <h2 className="text-2xl font-bold text-white mb-2">{lesson.title}</h2>
                                    {lesson.duration && (
                                        <p className="text-sm text-gray-400">Duration: {lesson.duration}</p>
                                    )}
                                </div>
                                <button
                                    onClick={handleMarkCompleted}
                                    className={cn(
                                        "flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all",
                                        videoCompleted
                                            ? "bg-green-500/10 text-green-500 border border-green-500/20"
                                            : "bg-primary hover:bg-primary/90 text-white"
                                    )}
                                >
                                    <CheckCircle className="w-4 h-4" />
                                    {videoCompleted ? "Completed" : "Mark as Done"}
                                </button>
                            </div>

                            {/* Next Steps */}
                            {(hasQuiz || hasPractice) && (
                                <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-700">
                                    <h3 className="font-semibold text-white mb-3 flex items-center gap-2">
                                        <Lightbulb className="w-4 h-4 text-yellow-500" />
                                        What's Next?
                                    </h3>
                                    <div className="space-y-2">
                                        {hasQuiz && !quizCompleted && (
                                            <button
                                                onClick={() => setActiveTab('quiz')}
                                                className="w-full text-left px-4 py-2 bg-purple-500/10 hover:bg-purple-500/20 border border-purple-500/20 rounded-lg text-sm text-purple-300 transition-colors"
                                            >
                                                📝 Take the quiz to test your knowledge
                                            </button>
                                        )}
                                        {hasPractice && (
                                            <button
                                                onClick={() => setActiveTab('practice')}
                                                className="w-full text-left px-4 py-2 bg-blue-500/10 hover:bg-blue-500/20 border border-blue-500/20 rounded-lg text-sm text-blue-300 transition-colors"
                                            >
                                                💻 Try the coding practice problem
                                            </button>
                                        )}
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                )}

                {activeTab === 'quiz' && hasQuiz && (
                    <div className="p-6 max-w-3xl mx-auto">
                        <div className="bg-gradient-to-br from-purple-500/10 to-pink-500/10 rounded-2xl p-6 border border-purple-500/20 mb-6">
                            <div className="flex items-center gap-3 mb-4">
                                <div className="w-12 h-12 bg-purple-500 rounded-xl flex items-center justify-center">
                                    <Trophy className="w-6 h-6 text-white" />
                                </div>
                                <div>
                                    <h2 className="text-2xl font-bold text-white">Quiz Time!</h2>
                                    <p className="text-sm text-gray-400">Test your understanding</p>
                                </div>
                            </div>

                            {lesson.quizzes.map((quiz, idx) => (
                                <div key={idx} className="space-y-4">
                                    <div className="bg-gray-900/50 rounded-xl p-4 border border-gray-700">
                                        <p className="text-lg font-medium text-white mb-4">{quiz.question}</p>

                                        <div className="space-y-2">
                                            {quiz.options?.map((option, optIdx) => (
                                                <button
                                                    key={optIdx}
                                                    onClick={() => handleQuizAnswer(option)}
                                                    disabled={quizResult !== null}
                                                    className={cn(
                                                        "w-full text-left px-4 py-3 rounded-lg border transition-all",
                                                        selectedAnswer === option
                                                            ? quizResult === 'correct'
                                                                ? "bg-green-500/20 border-green-500 text-green-300"
                                                                : "bg-red-500/20 border-red-500 text-red-300"
                                                            : quizResult && option === quiz.correct_answer
                                                                ? "bg-green-500/20 border-green-500 text-green-300"
                                                                : "bg-gray-800 border-gray-700 text-gray-300 hover:bg-gray-700 hover:border-gray-600",
                                                        quizResult && "cursor-not-allowed"
                                                    )}
                                                >
                                                    <span className="font-medium">{String.fromCharCode(65 + optIdx)}.</span> {option}
                                                </button>
                                            ))}
                                        </div>
                                    </div>

                                    {quizResult && (
                                        <div className={cn(
                                            "rounded-xl p-4 border flex items-start gap-3",
                                            quizResult === 'correct'
                                                ? "bg-green-500/10 border-green-500/20"
                                                : "bg-orange-500/10 border-orange-500/20"
                                        )}>
                                            {quizResult === 'correct' ? (
                                                <>
                                                    <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
                                                    <div>
                                                        <p className="font-semibold text-green-400">Correct! 🎉</p>
                                                        <p className="text-sm text-gray-300 mt-1">Great job! You've mastered this concept.</p>
                                                    </div>
                                                </>
                                            ) : (
                                                <>
                                                    <AlertCircle className="w-5 h-5 text-orange-500 flex-shrink-0 mt-0.5" />
                                                    <div>
                                                        <p className="font-semibold text-orange-400">Not quite right</p>
                                                        <p className="text-sm text-gray-300 mt-1">The correct answer is: <span className="font-medium text-green-400">{quiz.correct_answer}</span></p>
                                                    </div>
                                                </>
                                            )}
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {activeTab === 'practice' && hasPractice && (
                    <div className="p-6 max-w-4xl mx-auto">
                        <div className="bg-gradient-to-br from-blue-500/10 to-cyan-500/10 rounded-2xl p-6 border border-blue-500/20">
                            <div className="flex items-center gap-3 mb-6">
                                <div className="w-12 h-12 bg-blue-500 rounded-xl flex items-center justify-center">
                                    <Code className="w-6 h-6 text-white" />
                                </div>
                                <div>
                                    <h2 className="text-2xl font-bold text-white">Coding Practice</h2>
                                    <p className="text-sm text-gray-400">Apply what you've learned</p>
                                </div>
                            </div>

                            {lesson.practice_questions.map((practice, idx) => (
                                <div key={idx} className="space-y-4">
                                    {/* Problem Statement */}
                                    <div className="bg-gray-900/50 rounded-xl p-5 border border-gray-700">
                                        <h3 className="font-semibold text-white mb-3 flex items-center gap-2">
                                            <BookOpen className="w-4 h-4 text-blue-400" />
                                            Problem
                                        </h3>
                                        <p className="text-gray-300 leading-relaxed">{practice.problem_statement}</p>
                                    </div>

                                    {/* Test Cases */}
                                    {practice.test_cases && practice.test_cases.length > 0 && (
                                        <div className="bg-gray-900/50 rounded-xl p-5 border border-gray-700">
                                            <h3 className="font-semibold text-white mb-3">Test Cases</h3>
                                            <div className="space-y-2">
                                                {practice.test_cases.map((testCase, tcIdx) => (
                                                    <div key={tcIdx} className="bg-gray-800/50 rounded-lg p-3 font-mono text-sm">
                                                        <div className="text-gray-400">Input: <span className="text-cyan-400">{testCase.input}</span></div>
                                                        <div className="text-gray-400">Expected: <span className="text-green-400">{testCase.expected}</span></div>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    {/* Hints */}
                                    {practice.hints && practice.hints.length > 0 && (
                                        <div className="bg-yellow-500/10 rounded-xl p-5 border border-yellow-500/20">
                                            <h3 className="font-semibold text-yellow-400 mb-3 flex items-center gap-2">
                                                <Lightbulb className="w-4 h-4" />
                                                Hints
                                            </h3>
                                            <ul className="space-y-2">
                                                {practice.hints.map((hint, hintIdx) => (
                                                    <li key={hintIdx} className="text-sm text-gray-300 flex items-start gap-2">
                                                        <span className="text-yellow-500 flex-shrink-0">💡</span>
                                                        <span>{hint}</span>
                                                    </li>
                                                ))}
                                            </ul>
                                        </div>
                                    )}

                                    {/* Code Editor Placeholder */}
                                    <div className="bg-gray-900 rounded-xl p-5 border border-gray-700">
                                        <div className="flex items-center justify-between mb-3">
                                            <h3 className="font-semibold text-white">Your Solution</h3>
                                            <span className="text-xs text-gray-500">Code editor coming soon</span>
                                        </div>
                                        <div className="bg-gray-950 rounded-lg p-4 font-mono text-sm text-gray-500 border border-gray-800">
                                            // Write your code here...
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

function TabButton({ icon, label, active, onClick, badge }) {
    return (
        <button
            onClick={onClick}
            className={cn(
                "flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all relative",
                active
                    ? "bg-primary text-white shadow-lg shadow-primary/20"
                    : "text-gray-400 hover:text-gray-200 hover:bg-gray-800"
            )}
        >
            {icon}
            <span>{label}</span>
            {badge && <span className="ml-1">{badge}</span>}
        </button>
    );
}
