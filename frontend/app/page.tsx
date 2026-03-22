'use client';

import Link from 'next/link';
import { useWallet } from '@/lib/WalletContext';
import { Network, MessageSquare, BrainCircuit, ShieldCheck, ArrowRight, Zap } from 'lucide-react';

export default function Home() {
  const { accountAddress, connectWallet } = useWallet();

  return (
    <div className="min-h-screen bg-gray-950 text-gray-50 selection:bg-purple-500/30 overflow-hidden relative">
      {/* Ambient Background Effects */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[500px] opacity-20 pointer-events-none">
        <div className="absolute inset-0 bg-gradient-to-r from-purple-600 to-blue-600 blur-[100px] rounded-full mix-blend-screen" />
      </div>

      {/* Grid Pattern Overlay */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#4f4f4f2e_1px,transparent_1px),linear-gradient(to_bottom,#4f4f4f2e_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)] pointer-events-none" />

      {/* Navigation */}
      <nav className="border-b border-white/5 bg-gray-950/50 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <BrainCircuit className="w-8 h-8 text-purple-500" />
            <span className="text-2xl font-bold tracking-tight text-white">
              Neuro<span className="text-purple-400">Chain</span>
            </span>
          </div>
          <div className="flex items-center gap-4">
            {accountAddress ? (
              <div className="px-4 py-2 bg-purple-500/10 border border-purple-500/20 rounded-full text-sm text-purple-300 font-mono shadow-[0_0_15px_rgba(168,85,247,0.15)]">
                {accountAddress.slice(0, 6)}...{accountAddress.slice(-4)}
              </div>
            ) : (
              <button
                onClick={connectWallet}
                className="px-5 py-2.5 bg-white/5 hover:bg-white/10 border border-white/10 text-white rounded-full transition-all duration-300 text-sm font-medium flex items-center gap-2 hover:shadow-[0_0_20px_rgba(255,255,255,0.1)]"
              >
                Connect Wallet
              </button>
            )}
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative max-w-7xl mx-auto px-6 pt-32 pb-24 text-center z-10">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-purple-500/10 border border-purple-500/20 text-purple-300 text-sm font-medium mb-8">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-purple-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-purple-500"></span>
          </span>
          Live on Algorand Testnet
        </div>

        <h1 className="text-6xl md:text-8xl font-extrabold mb-8 tracking-tight leading-[1.1]">
          Architect the Future of <br className="hidden md:block" />
          <span className="bg-gradient-to-r from-purple-400 via-fuchsia-400 to-blue-400 bg-clip-text text-transparent">
            Collective Intelligence
          </span>
        </h1>

        <p className="text-xl text-gray-400 max-w-2xl mx-auto mb-12 leading-relaxed">
          Map your thoughts into a living knowledge graph. Engage in cryptographically secured debates powered by AI analysis and Algorand blockchain technology.
        </p>

        {/* CTA Buttons */}
        <div className="flex flex-col sm:flex-row gap-5 justify-center items-center">
          <Link
            href="/dashboard"
            className="group relative px-8 py-4 bg-purple-600 text-white rounded-full font-medium text-lg overflow-hidden transition-all hover:scale-105 hover:shadow-[0_0_40px_rgba(147,51,234,0.4)]"
          >
            <div className="absolute inset-0 bg-gradient-to-r from-purple-600 to-blue-600 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
            <span className="relative flex items-center gap-2 justify-center">
              <Network className="w-5 h-5" />
              Launch Graph
            </span>
          </Link>
          <Link
            href="/debate"
            className="group px-8 py-4 bg-white/5 border border-white/10 hover:bg-white/10 hover:border-white/20 text-white rounded-full transition-all font-medium text-lg flex items-center gap-2 backdrop-blur-sm"
          >
            <MessageSquare className="w-5 h-5 text-gray-400 group-hover:text-white transition-colors" />
            Start a Debate
          </Link>
        </div>
      </section>

      {/* Premium Features Grid (Bento Style) */}
      <section className="max-w-7xl mx-auto px-6 py-24 z-10 relative">
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">

          {/* Feature 1: Spans 2 columns on large screens */}
          <div className="lg:col-span-2 group bg-gradient-to-br from-gray-900 to-gray-950 border border-white/5 hover:border-purple-500/30 rounded-3xl p-8 transition-all duration-500 overflow-hidden relative">
            <div className="absolute top-0 right-0 w-64 h-64 bg-purple-500/5 rounded-full blur-3xl group-hover:bg-purple-500/10 transition-colors duration-500" />
            <Network className="w-12 h-12 text-purple-400 mb-6 group-hover:scale-110 transition-transform duration-500" />
            <h3 className="text-2xl font-bold text-white mb-3">Living Knowledge Graph</h3>
            <p className="text-gray-400 leading-relaxed max-w-md">
              Watch ideas physically connect in real-time. Our force-directed visualization merges semantic similarities, evolving raw thoughts into a structured network of human intelligence.
            </p>
          </div>

          {/* Feature 2 */}
          <div className="group bg-gradient-to-br from-gray-900 to-gray-950 border border-white/5 hover:border-orange-500/30 rounded-3xl p-8 transition-all duration-500 relative overflow-hidden">
            <div className="absolute top-0 right-0 w-64 h-64 bg-orange-500/5 rounded-full blur-3xl group-hover:bg-orange-500/10 transition-colors duration-500" />
            <MessageSquare className="w-12 h-12 text-orange-400 mb-6 group-hover:scale-110 transition-transform duration-500" />
            <h3 className="text-2xl font-bold text-white mb-3">Token-Gated Debates</h3>
            <p className="text-gray-400 leading-relaxed">
              Create structured, secure debate environments. Wallet-based authentication ensures genuine participation and immutable speaker records.
            </p>
          </div>

          {/* Feature 3 */}
          <div className="group bg-gradient-to-br from-gray-900 to-gray-950 border border-white/5 hover:border-blue-500/30 rounded-3xl p-8 transition-all duration-500 relative overflow-hidden">
            <div className="absolute top-0 right-0 w-64 h-64 bg-blue-500/5 rounded-full blur-3xl group-hover:bg-blue-500/10 transition-colors duration-500" />
            <BrainCircuit className="w-12 h-12 text-blue-400 mb-6 group-hover:scale-110 transition-transform duration-500" />
            <h3 className="text-2xl font-bold text-white mb-3">AI Sentience Engine</h3>
            <p className="text-gray-400 leading-relaxed">
              Machine learning models analyze debate semantics to find consensus, detect logical fallacies, and map argument trajectories in real-time.
            </p>
          </div>

          {/* Feature 4: Spans 2 columns */}
          <div className="lg:col-span-2 group bg-gradient-to-br from-gray-900 to-gray-950 border border-white/5 hover:border-green-500/30 rounded-3xl p-8 transition-all duration-500 relative overflow-hidden">
            <div className="absolute top-0 right-0 w-64 h-64 bg-green-500/5 rounded-full blur-3xl group-hover:bg-green-500/10 transition-colors duration-500" />
            <ShieldCheck className="w-12 h-12 text-green-400 mb-6 group-hover:scale-110 transition-transform duration-500" />
            <h3 className="text-2xl font-bold text-white mb-3">Algorand Immutable Ledger</h3>
            <p className="text-gray-400 leading-relaxed max-w-md">
              Every debate conclusion and knowledge node is hashed and anchored to the Algorand blockchain. Ensure absolute transparency, low latency, and unalterable proof of thought.
            </p>
          </div>

        </div>
      </section>

      {/* Dynamic CTA */}
      <section className="py-24 relative z-10">
        <div className="max-w-5xl mx-auto px-6">
          <div className="relative rounded-3xl overflow-hidden bg-gray-900 border border-white/10 p-12 md:p-20 text-center">
            {/* Inner Glow */}
            <div className="absolute inset-0 bg-gradient-to-b from-purple-500/10 to-transparent pointer-events-none" />

            <Zap className="w-12 h-12 text-purple-400 mx-auto mb-6" />
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-6 tracking-tight">
              Ready to wire your mind to the chain?
            </h2>
            <p className="text-xl text-gray-400 mb-10 max-w-2xl mx-auto">
              Connect your Pera Wallet instantly. No emails, no passwords, just pure decentralized discourse.
            </p>

            <button
              onClick={connectWallet}
              className="group inline-flex items-center gap-3 px-8 py-4 bg-white text-gray-950 rounded-full font-bold text-lg hover:bg-gray-200 transition-colors shadow-[0_0_30px_rgba(255,255,255,0.2)]"
            >
              Connect Pera Wallet
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/5 bg-gray-950 mt-12 relative z-10">
        <div className="max-w-7xl mx-auto px-6 py-12 flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-2">
            <BrainCircuit className="w-6 h-6 text-purple-500" />
            <span className="text-xl font-bold tracking-tight text-white">
              Neuro<span className="text-purple-400">Chain</span>
            </span>
          </div>
          <div className="flex gap-8 text-sm text-gray-400 font-medium">
            <Link href="/dashboard" className="hover:text-purple-400 transition-colors">Knowledge Graph</Link>
            <Link href="/debate" className="hover:text-purple-400 transition-colors">Debate Hub</Link>
            <a href="#" className="hover:text-purple-400 transition-colors">Algorand Integration</a>
            <a href="#" className="hover:text-purple-400 transition-colors">GitHub</a>
          </div>
          <p className="text-sm text-gray-500">
            © {new Date().getFullYear()} NeuroChain. MIT License.
          </p>
        </div>
      </footer>
    </div>
  );
}
