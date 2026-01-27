import React, { useState, useEffect } from 'react';
import { Play, CheckCircle, Clock, AlertCircle } from 'lucide-react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs) {
    return twMerge(clsx(inputs));
}

const MOCK_VIDEOS = [
    { id: 'kqtD5dpn9C8', title: 'Python for Beginners - Full Course', thumbnail: 'https://img.youtube.com/vi/kqtD5dpn9C8/mqdefault.jpg', score: 10 },
    { id: '_uQrJ0TkZlc', title: 'Python Tutorial - Python for Beginners [Full Course]', thumbnail: 'https://img.youtube.com/vi/_uQrJ0TkZlc/mqdefault.jpg', score: 9 },
    { id: 'rfscVS0vtbw', title: 'Learn Python - Full Course for Beginners [Tutorial]', thumbnail: 'https://img.youtube.com/vi/rfscVS0vtbw/mqdefault.jpg', score: 8 },
];

export default function VideoPlayer({ topic }) {
    const [videos, setVideos] = useState([]);
    const [activeVideo, setActiveVideo] = useState(null);
    const [loading, setLoading] = useState(false);
    const [completed, setCompleted] = useState(false);

    useEffect(() => {
        if (!topic) return;

        const fetchVideos = async () => {
            setLoading(true);
            setVideos([]);
            setActiveVideo(null);
            setCompleted(false);

            try {
                const response = await fetch(`/api/videos?topic=${encodeURIComponent(topic)}`);
                if (!response.ok) throw new Error('API Failed');

                const data = await response.json();
                if (Array.isArray(data) && data.length > 0) {
                    setVideos(data);
                    setActiveVideo(data[0]);
                } else {
                    // If API returns empty array, use mock
                    throw new Error('No videos found');
                }
            } catch (error) {
                console.warn("Video Fetch Failed, using Mock Data:", error);
                setVideos(MOCK_VIDEOS);
                setActiveVideo(MOCK_VIDEOS[0]);
            } finally {
                setLoading(false);
            }
        };

        fetchVideos();
    }, [topic]);

    if (!topic) {
        return (
            <div className="flex-1 flex flex-col items-center justify-center text-gray-500 space-y-4 h-full">
                <div className="w-16 h-16 bg-gray-800 rounded-2xl flex items-center justify-center">
                    <Play className="w-8 h-8 text-gray-600" />
                </div>
                <p>Select a topic to start learning</p>
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

    if (!activeVideo) {
        return <div className="p-6 text-center text-gray-400">No videos available.</div>;
    }

    return (
        <div className="flex-1 flex flex-col h-full overflow-hidden">
            {/* Main Player */}
            <div className="aspect-video w-full bg-black relative flex-shrink-0">
                <iframe
                    src={`https://www.youtube.com/embed/${activeVideo.id}`}
                    className="w-full h-full"
                    allowFullScreen
                    title="Video player"
                />
            </div>

            {/* Video Info & Playlist */}
            <div className="flex-1 overflow-y-auto p-6">
                <div className="flex items-start justify-between mb-6">
                    <div>
                        <h2 className="text-2xl font-bold mb-2 text-white">{activeVideo.title}</h2>
                        <div className="flex items-center gap-2 text-gray-400 text-sm">
                            <span className="bg-primary/10 text-primary px-2 py-0.5 rounded text-xs font-medium">
                                AI Score: {activeVideo.score}/10
                            </span>
                        </div>
                    </div>
                    <button
                        onClick={() => setCompleted(!completed)}
                        className={cn(
                            "flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors",
                            completed
                                ? "bg-green-500/10 text-green-500 border border-green-500/20"
                                : "bg-gray-800 text-gray-300 hover:bg-gray-700"
                        )}
                    >
                        <CheckCircle className="w-4 h-4" />
                        {completed ? "Completed" : "Mark as Done"}
                    </button>
                </div>

                <h3 className="font-bold text-lg mb-4 flex items-center gap-2 text-white">
                    <Play className="w-4 h-4 text-primary" />
                    Up Next
                </h3>

                <div className="space-y-3">
                    {videos.map((video) => (
                        <div
                            key={video.id}
                            onClick={() => setActiveVideo(video)}
                            className={cn(
                                "flex gap-3 p-3 rounded-xl cursor-pointer transition-all border",
                                activeVideo.id === video.id
                                    ? "bg-primary/5 border-violet-500 shadow-sm shadow-violet-500/10"
                                    : "bg-surface border-gray-800 hover:bg-gray-800 hover:border-gray-700"
                            )}
                        >
                            <div className="w-32 h-20 bg-gray-900 rounded-lg flex-shrink-0 bg-cover bg-center relative overflow-hidden group">
                                <img src={video.thumbnail} alt="" className="w-full h-full object-cover" />
                                <div className="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                                    <Play className="w-8 h-8 text-white fill-white" />
                                </div>
                            </div>
                            <div className="flex-1 min-w-0">
                                <h4 className={cn(
                                    "font-medium text-sm line-clamp-2",
                                    activeVideo.id === video.id ? "text-primary" : "text-gray-200"
                                )}>
                                    {video.title}
                                </h4>
                                <p className="text-xs text-gray-500 mt-1 flex items-center gap-1">
                                    <Clock className="w-3 h-3" /> 10 mins
                                </p>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
