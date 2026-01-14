import { useEffect, useMemo, useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { reportChatApi } from '@/lib/api'
import { Loader2, Send, MessageSquareText, Quote } from 'lucide-react'

type Citation = {
    type: string
    reference: string
    snippet?: string | null
    meta?: Record<string, any> | null
}

type ChatMessage = {
    id: number
    role: 'user' | 'assistant' | 'system' | string
    content: string
    created_at: string
    citations?: Citation[]
}

type ChatSession = {
    id: number
    evaluation_id: number
    title?: string | null
    created_at: string
}

type HistoryResponse = {
    session: ChatSession
    messages: ChatMessage[]
}

export default function ReportChat({ evaluationId }: { evaluationId: number }) {
    const queryClient = useQueryClient()
    const [input, setInput] = useState('')
    const bottomRef = useRef<HTMLDivElement | null>(null)

    const sessionQuery = useQuery({
        queryKey: ['report-chat-session', evaluationId],
        queryFn: async () => {
            const res = await reportChatApi.createOrGetSession(evaluationId)
            return res.data as ChatSession
        },
        enabled: !!evaluationId,
        staleTime: 60_000,
    })

    const sessionId = sessionQuery.data?.id

    const historyQuery = useQuery({
        queryKey: ['report-chat-history', sessionId],
        queryFn: async () => {
            const res = await reportChatApi.getSessionHistory(sessionId!)
            return res.data as HistoryResponse
        },
        enabled: !!sessionId,
        refetchOnWindowFocus: false,
    })

    const sendMutation = useMutation({
        mutationFn: async (message: string) => {
            const res = await reportChatApi.sendMessage(sessionId!, message)
            return res.data as ChatMessage
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['report-chat-history', sessionId] })
        },
    })

    const messages = useMemo(() => historyQuery.data?.messages || [], [historyQuery.data])

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [messages.length, sendMutation.isPending])

    const onSend = async () => {
        const msg = input.trim()
        if (!msg || !sessionId || sendMutation.isPending) return
        setInput('')
        sendMutation.mutate(msg)
    }

    const isLoading = sessionQuery.isLoading || (sessionId ? historyQuery.isLoading : true)
    const error = (sessionQuery.error as any)?.message || (historyQuery.error as any)?.message

    return (
        <div className="bg-gray-900/50 backdrop-blur border border-gray-800 rounded-2xl overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-800 flex items-center gap-3">
                <div className="p-2 rounded-xl bg-purple-500/15 border border-purple-500/20">
                    <MessageSquareText className="w-5 h-5 text-purple-300" />
                </div>
                <div className="flex-1">
                    <p className="text-sm font-semibold text-white">Ask about this report</p>
                    <p className="text-xs text-gray-500">
                        Questions are answered using your uploaded documents + the saved report.
                    </p>
                </div>
                {isLoading ? <Loader2 className="w-4 h-4 text-gray-400 animate-spin" /> : null}
            </div>

            <div className="h-80 overflow-y-auto px-6 py-4 space-y-4">
                {error ? (
                    <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-sm text-red-200">
                        {error}
                    </div>
                ) : null}

                {messages.length === 0 && !isLoading ? (
                    <div className="text-sm text-gray-400">
                        Try: “Why did the report recommend CONDITIONAL_APPROVAL?”
                    </div>
                ) : null}

                {messages.map((m) => (
                    <div key={m.id} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div
                            className={`max-w-[85%] rounded-2xl px-4 py-3 border ${
                                m.role === 'user'
                                    ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-50'
                                    : 'bg-gray-950/30 border-gray-800 text-gray-100'
                            }`}
                        >
                            <div className="text-sm whitespace-pre-wrap leading-relaxed">{m.content}</div>

                            {(m.citations || []).length > 0 && m.role !== 'user' ? (
                                <details className="mt-3">
                                    <summary className="cursor-pointer select-none text-xs text-gray-400 hover:text-gray-300 flex items-center gap-2">
                                        <Quote className="w-3.5 h-3.5" />
                                        Evidence ({m.citations?.length})
                                    </summary>
                                    <div className="mt-2 space-y-2">
                                        {(m.citations || []).slice(0, 6).map((c, idx) => (
                                            <div key={idx} className="text-xs text-gray-400 border border-gray-800 rounded-xl p-3 bg-black/10">
                                                <div className="flex items-center justify-between gap-3">
                                                    <span className="text-gray-300 font-medium">{c.type}</span>
                                                    <span className="text-gray-500 truncate">{c.reference}</span>
                                                </div>
                                                {c.snippet ? <div className="mt-2 text-gray-500">{c.snippet}</div> : null}
                                            </div>
                                        ))}
                                    </div>
                                </details>
                            ) : null}
                        </div>
                    </div>
                ))}

                {sendMutation.isPending ? (
                    <div className="flex justify-start">
                        <div className="max-w-[85%] rounded-2xl px-4 py-3 border bg-gray-950/30 border-gray-800 text-gray-100">
                            <div className="flex items-center gap-2 text-sm text-gray-400">
                                <Loader2 className="w-4 h-4 animate-spin" />
                                Thinking…
                            </div>
                        </div>
                    </div>
                ) : null}

                <div ref={bottomRef} />
            </div>

            <div className="px-6 py-4 border-t border-gray-800">
                <div className="flex items-center gap-3">
                    <input
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={(e) => {
                            if (e.key === 'Enter' && !e.shiftKey) {
                                e.preventDefault()
                                onSend()
                            }
                        }}
                        placeholder="Ask a question about this report…"
                        className="flex-1 bg-gray-950/40 border border-gray-800 rounded-xl px-4 py-3 text-sm text-white placeholder:text-gray-600 focus:outline-none focus:ring-2 focus:ring-purple-500/40"
                        disabled={!sessionId || sendMutation.isPending}
                    />
                    <button
                        onClick={onSend}
                        disabled={!input.trim() || !sessionId || sendMutation.isPending}
                        className="inline-flex items-center gap-2 px-4 py-3 rounded-xl bg-purple-500 hover:bg-purple-600 disabled:opacity-60 disabled:cursor-not-allowed transition-colors text-sm font-semibold"
                    >
                        <Send className="w-4 h-4" />
                        Send
                    </button>
                </div>
            </div>
        </div>
    )
}
