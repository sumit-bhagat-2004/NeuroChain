'use client';

import Link from 'next/link';
import { useWallet } from '@/lib/WalletContext';

export default function Home() {
  const { accountAddress, connectWallet } = useWallet();

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-950 via-gray-900 to-gray-950">
      {/* Navigation */}
      <nav className="border-b border-gray-800 bg-gray-900/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="text-2xl font-bold text-purple-400">NeuroChain</div>
          <div className="flex items-center gap-4">
            {accountAddress ? (
              <>
                <div className="px-3 py-2 bg-purple-900/50 border border-purple-700 rounded-lg text-xs text-purple-200 font-mono">
                  {accountAddress.slice(0, 6)}...{accountAddress.slice(-4)}
                </div>
              </>
            ) : (
              <button
                onClick={connectWallet}
                className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors text-sm font-medium"
              >
                Connect Wallet
              </button>
            )}
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-6 py-24">
        <div className="text-center mb-20">
          <h1 className="text-5xl md:text-7xl font-bold mb-6 bg-gradient-to-r from-purple-400 via-purple-500 to-blue-400 bg-clip-text text-transparent">
            NeuroChain
          </h1>
          <p className="text-xl md:text-2xl text-gray-300 mb-4">
            Knowledge Graph Visualization & Collaborative Debate Platform
          </p>
          <p className="text-lg text-gray-400 max-w-2xl mx-auto mb-8">
            Build interconnected knowledge networks in real-time while engaging in structured debates powered by AI and blockchain technology on Algorand.
          </p>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <Link
              href="/dashboard"
              className="px-8 py-4 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors font-medium text-lg flex items-center gap-2"
            >
              🧠 Launch Dashboard
            </Link>
            <Link
              href="/debate"
              className="px-8 py-4 bg-orange-600 hover:bg-orange-700 text-white rounded-lg transition-colors font-medium text-lg flex items-center gap-2"
            >
              🎤 Start Debate
            </Link>
          </div>
        </div>

        {/* Features Grid */}
        <div className="grid md:grid-cols-2 gap-8 mt-24">
          {/* Feature 1: Knowledge Graph */}
          <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-8 hover:border-purple-600 transition-colors">
            <div className="text-4xl mb-4">🧠</div>
            <h3 className="text-2xl font-bold text-purple-400 mb-3">Knowledge Graph</h3>
            <p className="text-gray-300 mb-4">
              Visualize and build interconnected knowledge networks in real-time. Watch as AI-powered connections emerge and thoughts evolve through intelligent merging.
            </p>
            <ul className="text-gray-400 space-y-2 text-sm">
              <li>✓ Real-time visualization</li>
              <li>✓ AI-powered connections</li>
              <li>✓ Thought evolution tracking</li>
              <li>✓ Interactive graph exploration</li>
            </ul>
          </div>

          {/* Feature 2: Debate Mode */}
          <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-8 hover:border-orange-600 transition-colors">
            <div className="text-4xl mb-4">🎤</div>
            <h3 className="text-2xl font-bold text-orange-400 mb-3">Debate Sessions</h3>
            <p className="text-gray-300 mb-4">
              Conduct structured debates on any topic with controlled access. Create sessions with specific creators and participants for focused discussions.
            </p>
            <ul className="text-gray-400 space-y-2 text-sm">
              <li>✓ Session-based debates</li>
              <li>✓ Access control via wallet</li>
              <li>✓ AI-powered analysis</li>
              <li>✓ Real-time statistics</li>
            </ul>
          </div>

          {/* Feature 3: AI Analytics */}
          <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-8 hover:border-blue-600 transition-colors">
            <div className="text-4xl mb-4">📊</div>
            <h3 className="text-2xl font-bold text-blue-400 mb-3">AI Analytics</h3>
            <p className="text-gray-300 mb-4">
              Get comprehensive insights into discussions and debates. AI-powered analysis reveals patterns, key arguments, and actionable recommendations.
            </p>
            <ul className="text-gray-400 space-y-2 text-sm">
              <li>✓ Speaker analytics</li>
              <li>✓ Topic analysis</li>
              <li>✓ Leaderboards</li>
              <li>✓ AI-generated conclusions</li>
            </ul>
          </div>

          {/* Feature 4: Blockchain Integration */}
          <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-8 hover:border-green-600 transition-colors">
            <div className="text-4xl mb-4">⛓️</div>
            <h3 className="text-2xl font-bold text-green-400 mb-3">Blockchain Security</h3>
            <p className="text-gray-300 mb-4">
              Built on Algorand blockchain for secure, transparent, and verifiable debate sessions. Wallet-based authentication ensures authenticity.
            </p>
            <ul className="text-gray-400 space-y-2 text-sm">
              <li>✓ Algorand integration</li>
              <li>✓ Pera wallet support</li>
              <li>✓ Immutable records</li>
              <li>✓ Secure transactions</li>
            </ul>
          </div>
        </div>

        {/* How It Works */}
        <div className="mt-24">
          <h2 className="text-4xl font-bold text-center text-purple-400 mb-12">How It Works</h2>
          <div className="grid md:grid-cols-3 gap-6">
            {/* Step 1 */}
            <div className="relative">
              <div className="absolute -top-12 left-1/2 transform -translate-x-1/2 w-8 h-8 bg-purple-600 rounded-full text-white font-bold flex items-center justify-center">
                1
              </div>
              <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-8 pt-12">
                <h4 className="text-xl font-bold text-purple-400 mb-3">Connect Wallet</h4>
                <p className="text-gray-400">
                  Connect your Pera wallet to authenticate your identity and participate in debates and knowledge graphs.
                </p>
              </div>
            </div>

            {/* Step 2 */}
            <div className="relative">
              <div className="absolute -top-12 left-1/2 transform -translate-x-1/2 w-8 h-8 bg-purple-600 rounded-full text-white font-bold flex items-center justify-center">
                2
              </div>
              <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-8 pt-12">
                <h4 className="text-xl font-bold text-purple-400 mb-3">Create or Join</h4>
                <p className="text-gray-400">
                  Create a new debate session with specific participants, or join an existing session to contribute your insights.
                </p>
              </div>
            </div>

            {/* Step 3 */}
            <div className="relative">
              <div className="absolute -top-12 left-1/2 transform -translate-x-1/2 w-8 h-8 bg-purple-600 rounded-full text-white font-bold flex items-center justify-center">
                3
              </div>
              <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-8 pt-12">
                <h4 className="text-xl font-bold text-purple-400 mb-3">Debate & Analyze</h4>
                <p className="text-gray-400">
                  Contribute ideas, watch them merge and evolve, and gain AI-powered insights into the discussion.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* CTA Section */}
        <div className="mt-24 bg-gradient-to-r from-purple-900/50 to-blue-900/50 border border-purple-700/50 rounded-lg p-12 text-center">
          <h2 className="text-3xl font-bold text-white mb-4">Ready to Start?</h2>
          <p className="text-gray-300 mb-6 text-lg">
            Explore the knowledge graph or create your first debate session today.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/dashboard"
              className="px-8 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors font-medium"
            >
              Go to Dashboard
            </Link>
            <Link
              href="/debate"
              className="px-8 py-3 bg-orange-600 hover:bg-orange-700 text-white rounded-lg transition-colors font-medium"
            >
              Start Debating
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-800 bg-gray-900/50 mt-24">
        <div className="max-w-7xl mx-auto px-6 py-12">
          <div className="grid md:grid-cols-4 gap-8 mb-8">
            <div>
              <h4 className="text-lg font-bold text-purple-400 mb-4">NeuroChain</h4>
              <p className="text-gray-400 text-sm">
                Building the future of collaborative intelligence on blockchain.
              </p>
            </div>
            <div>
              <h4 className="text-sm font-bold text-gray-300 mb-4">Features</h4>
              <ul className="space-y-2 text-sm text-gray-400">
                <li>
                  <Link href="/dashboard" className="hover:text-purple-400 transition-colors">
                    Knowledge Graph
                  </Link>
                </li>
                <li>
                  <Link href="/debate" className="hover:text-purple-400 transition-colors">
                    Debate Sessions
                  </Link>
                </li>
              </ul>
            </div>
            <div>
              <h4 className="text-sm font-bold text-gray-300 mb-4">Technology</h4>
              <ul className="space-y-2 text-sm text-gray-400">
                <li>Algorand</li>
                <li>Pera Wallet</li>
                <li>AI Analytics</li>
              </ul>
            </div>
            <div>
              <h4 className="text-sm font-bold text-gray-300 mb-4">Connect</h4>
              <ul className="space-y-2 text-sm text-gray-400">
                <li>GitHub</li>
                <li>Twitter</li>
                <li>Docs</li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-700 pt-8 text-center text-sm text-gray-400">
            <p>© 2026 NeuroChain. Powered by AI and Blockchain.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
