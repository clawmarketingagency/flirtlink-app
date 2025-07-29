'use client'

import { useState } from 'react'
import axios from 'axios'

const API_BASE = process.env.https://flirtlink-app.up.railway.app

export default function HomePage() {
  const [step, setStep] = useState<'form' | 'chat'>('form')
  const [personaName, setPersonaName] = useState('')
  const [prompt, setPrompt] = useState('')
  const [creatorId] = useState('demo-user')
  const [links, setLinks] = useState({ onlyfans: '', tip: '' })
  const [agentId, setAgentId] = useState('')
  const [userInput, setUserInput] = useState('')
  const [chatLog, setChatLog] = useState<string[]>([])
  const [loading, setLoading] = useState(false)

  const createAgent = async () => {
    try {
      const res = await axios.post(`${API_BASE}/create-agent`, {
        creator_id: creatorId,
        persona_name: personaName,
        personality_prompt: prompt,
        links,
      })
      setAgentId(res.data.agent_id)
      setStep('chat')
    } catch {
      alert('Error creating agent')
    }
  }

  const sendChat = async () => {
    if (!userInput) return
    setChatLog(prev => [...prev, `You: ${userInput}`])
    setLoading(true)
    try {
      const res = await axios.post(`${API_BASE}/chat`, {
        agent_id: agentId,
        user_input: userInput,
      })
      const bot = res.data.reply
      setChatLog(prev => [...prev, `Agent: ${bot}`])
      setUserInput('')
    } catch {
      alert('Chat error')
    }
    setLoading(false)
  }

  return (
    <main className="min-h-screen bg-black text-white p-6 max-w-xl mx-auto">
      {step === 'form' ? (
        <>
          <h1 className="text-3xl font-bold text-pink-500 mb-4">💋 Build Your AI FlirtLink</h1>
          <input
            className="w-full p-2 mb-2 bg-zinc-800 rounded"
            placeholder="Agent name"
            value={personaName}
            onChange={e => setPersonaName(e.target.value)}
          />
          <textarea
            className="w-full p-2 mb-2 bg-zinc-800 rounded"
            placeholder="Agent personality (e.g. flirty bratty submissive...)"
            rows={4}
            value={prompt}
            onChange={e => setPrompt(e.target.value)}
          />
          <input
            className="w-full p-2 mb-2 bg-zinc-800 rounded"
            placeholder="OnlyFans link"
            value={links.onlyfans}
            onChange={e => setLinks({ ...links, onlyfans: e.target.value })}
          />
          <input
            className="w-full p-2 mb-4 bg-zinc-800 rounded"
            placeholder="Tip Me link"
            value={links.tip}
            onChange={e => setLinks({ ...links, tip: e.target.value })}
          />
          <button
            className="w-full p-2 bg-pink-600 hover:bg-pink-700 rounded font-bold"
            onClick={createAgent}
          >
            🚀 Launch Agent
          </button>
        </>
      ) : (
        <>
          <h2 className="text-2xl font-bold text-pink-400 mb-3">Chat with {personaName}</h2>
          <div className="bg-zinc-900 rounded p-3 mb-4 max-h-96 overflow-y-auto">
            {chatLog.map((msg, idx) => (
              <p key={idx} className="mb-2">{msg}</p>
            ))}
          </div>
          <input
            className="w-full p-2 mb-2 bg-zinc-800 rounded"
            placeholder="Type a message..."
            value={userInput}
            onChange={e => setUserInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && sendChat()}
          />
          <button
            className="w-full p-2 bg-pink-600 hover:bg-pink-700 rounded font-bold"
            onClick={sendChat}
            disabled={loading}
          >
            {loading ? 'Talking...' : 'Send 💬'}
          </button>
        </>
      )}
    </main>
  )
}


