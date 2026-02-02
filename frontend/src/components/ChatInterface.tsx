
import React, { useState, useRef, useEffect } from 'react';
import { Send, X, MessageSquare, Loader2 } from 'lucide-react'; // Lucide icons
import { useAuth } from "@/context/AuthContext";
import { API_BASE_URL, fetchWithRetry } from "@/lib/utils";

interface ChatMessage {
    role: 'user' | 'model';
    content: string;
}

const ChatInterface: React.FC = () => {
    const { user } = useAuth(); // Auth context
    const [isOpen, setIsOpen] = useState(false);
    const [messages, setMessages] = useState<ChatMessage[]>([
        { role: 'model', content: "Hi! I'm your Health AI Coach. Ask me anything about your training or recovery! 🏃‍♂️" }
    ]);
    const [input, setInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef<null | HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages, isOpen]);

    const handleSend = async () => {
        if (!input.trim() || isLoading) return;

        const userMsg = { role: 'user' as const, content: input };
        setMessages(prev => [...prev, userMsg]);
        setInput("");
        setIsLoading(true);

        try {
            if (!user) throw new Error("Not authenticated");
            const token = await user.getIdToken();

            const response = await fetchWithRetry(`${API_BASE_URL}/ai/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    message: userMsg.content,
                    history: messages.slice(-10) // Limit context size
                })
            });

            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.detail || 'Failed to fetch');
            }

            const data = await response.json();
            const botMsg = { role: 'model' as const, content: data.reply };
            setMessages(prev => [...prev, botMsg]);

        } catch (error) {
            console.error("Chat Error:", error);
            setMessages(prev => [...prev, { role: 'model', content: "Sorry, I'm having trouble connecting right now. Try again later." }]);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <>
            {/* Floating Action Button */}
            {!isOpen && (
                <button
                    onClick={() => setIsOpen(true)}
                    className="fixed bottom-6 right-6 w-14 h-14 bg-blue-600 hover:bg-blue-700 text-white rounded-full shadow-lg flex items-center justify-center transition-all z-50"
                >
                    <MessageSquare size={24} />
                </button>
            )}

            {/* Chat Window */}
            {isOpen && (
                <div className="fixed bottom-6 right-6 w-96 max-w-[calc(100vw-2rem)] h-[500px] max-h-[80vh] bg-white rounded-2xl shadow-2xl flex flex-col z-50 border border-gray-200 overflow-hidden font-sans">
                    {/* Header */}
                    <div className="bg-blue-600 text-white p-4 flex justify-between items-center">
                        <div className="flex items-center gap-2">
                            <span className="font-semibold">AI Coach</span>
                            <span className="text-xs bg-blue-500 px-2 py-0.5 rounded-full">Beta</span>
                        </div>
                        <button onClick={() => setIsOpen(false)} className="hover:bg-blue-700 p-1 rounded">
                            <X size={20} />
                        </button>
                    </div>

                    {/* Messages Area */}
                    <div className="flex-1 overflow-y-auto p-4 bg-gray-50 flex flex-col gap-3">
                        {messages.map((msg, idx) => (
                            <div key={idx} className={`max-w-[80%] rounded-2xl p-3 text-sm ${msg.role === 'user'
                                ? 'bg-blue-600 text-white self-end rounded-br-none'
                                : 'bg-white border border-gray-200 text-gray-800 self-start rounded-bl-none shadow-sm'
                                }`}>
                                {msg.content}
                            </div>
                        ))}
                        {isLoading && (
                            <div className="self-start bg-white border border-gray-200 p-3 rounded-2xl rounded-bl-none shadow-sm">
                                <Loader2 className="animate-spin text-blue-600" size={16} />
                            </div>
                        )}
                        <div ref={messagesEndRef} />
                    </div>

                    {/* Input Area */}
                    <div className="p-4 bg-white border-t border-gray-100 flex gap-2">
                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                            placeholder="Ask about your metrics..."
                            className="flex-1 bg-gray-100 text-gray-900 border-none rounded-full px-4 py-2 focus:ring-2 focus:ring-blue-500 focus:outline-none text-sm placeholder-gray-500"
                            disabled={isLoading}
                        />
                        <button
                            onClick={handleSend}
                            disabled={isLoading || !input.trim()}
                            className="w-10 h-10 bg-blue-600 text-white rounded-full flex items-center justify-center hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        >
                            <Send size={18} />
                        </button>
                    </div>
                </div>
            )}
        </>
    );
};

export default ChatInterface;

