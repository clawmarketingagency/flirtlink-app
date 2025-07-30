import { useState } from 'react'
import axios from 'axios'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'https://flirtlink-app.up.railway.app'

export default function Home() {
  const [step, setStep] = useState('create')
  const [personaName, setPersonaName] = useState('')
  const [prompt, setPrompt] = useState('')
  const [links, setLinks] = useState({ onlyfans: '', tip: '' })
  const [creatorId, setCreatorId] = useState('demo-123')
  const [agentId, setAgentId] = useState('')
  const [userInput, setUserInput] = useState('')
  const [chatLog, setChatLog] = useState([])
  const [loading, setLoading] = useState(false)

  const handleCreateAgent = async () => {
    try {
      const res = await axios.post(`${API_BASE}/create-agent`, {
        creator_id: creatorId,
        persona_name: personaName,
        personality_prompt: prompt,
        links,
      })
      setAgentId(res.data.agent_id)
      setStep('chat')
    } catch (e) {
      console.error('Create Agent Error:', e)
      alert('Error creating agent')
    }
  }

  const sendChat = async () => {
    if (!userInput) return
    setLoading(true)
    setChatLog(prev => [...prev, `You: ${userInput}`])
    try {
      const res = await axios.post(`${API_BASE}/chat`, {
        agent_id: agentId,
        user_input: userInput,
      })
      const botReply = res.data.reply
      setChatLog(prev => [...prev, `Agent: ${botReply}`])
      setUserInput('')
    } catch (e) {
      alert('Error sending message')
    }
    setLoading(false)
  }

  if (step === 'create') {
    return (
      <div className="min-h-screen bg-black text-white p-6 flex flex-col gap-4 max-w-lg mx-auto">
        <h1 className="text-3xl font-bold text-pink-500">💋 FlirtLink Agent Builder</h1>
        <input
          type="text"
          placeholder="Your Agent Name"
          className="p-2 rounded bg-zinc-800"
          value={personaName}
          onChange={e => setPersonaName(e.target.value)}
        />
        <textarea
          placeholder="Describe your personality (flirty, bratty, submissive...)"
          className="p-2 rounded bg-zinc-800"
          rows={4}
          value={prompt}
          onChange={e => setPrompt(e.target.value)}
        />
        <input
          type="text"
          placeholder="OnlyFans Link"
          className="p-2 rounded bg-zinc-800"
          value={links.onlyfans}
          onChange={e => setLinks({ ...links, onlyfans: e.target.value })}
        />
        <input
          type="text"
          placeholder="Tip Me Link"
          className="p-2 rounded bg-zinc-800"
          value={links.tip}
          onChange={e => setLinks({ ...links, tip: e.target.value })}
        />
        <button
          onClick={handleCreateAgent}
          className="bg-pink-600 hover:bg-pink-700 text-white p-2 rounded"
        >
          🚀 Launch My Agent
        </button>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-black text-white p-4 flex flex-col max-w-lg mx-auto">
      <h2 className="text-2xl font-bold text-pink-500 mb-2">💬 Chat with {personaName}</h2>
      <div className="flex-1 bg-zinc-900 p-3 rounded mb-4 overflow-y-auto max-h-[60vh]">
        {chatLog.map((msg, i) => (
          <p key={i} className="mb-2">{msg}</p>
        ))}
      </div>
      <input
        type="text"
        className="p-2 rounded bg-zinc-800 mb-2"
        placeholder="Type something..."
        value={userInput}
        onChange={e => setUserInput(e.target.value)}
        onKeyDown={e => e.key === 'Enter' && sendChat()}
      />
      <button
        onClick={sendChat}
        disabled={loading}
        className="bg-pink-600 hover:bg-pink-700 text-white p-2 rounded"
      >
        {loading ? 'Talking...' : 'Send 💦'}
      </button>
    </div>
  )
}
