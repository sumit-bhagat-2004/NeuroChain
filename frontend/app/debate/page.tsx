'use client';

import React, { useState, useEffect } from 'react';
import { useWallet } from '@/lib/WalletContext';
import DebateTranscriptionInput from '@/components/DebateTranscriptionInput';
import DebateNodesList from '@/components/DebateNodesList';
import DebateStats from '@/components/DebateStats';
import SpeakerLeaderboard from '@/components/SpeakerLeaderboard';
import TopicsAnalysis from '@/components/TopicsAnalysis';
import DebateConclusion from '@/components/DebateConclusion';
import DebateSessionCreator from '@/components/DebateSessionCreator';
import {
  addDebateTranscription,
  getAllDebateNodes,
  getDebateStats,
  getDebateLeaderboard,
  getTopicsAnalysis,
  getDebateConclusion,
  getAIAnalysis,
  getDebateSession,
  DebateNode,
  DebateStats as DebateStatsType,
  LeaderboardResponse,
  TopicAnalysis,
  DebateConclusion as DebateConclusionType,
  AIAnalysis,
  DebateSessionResponse,
} from '@/lib/api';
import Link from 'next/link';

export default function DebatePage() {
  const [sessionMode, setSessionMode] = useState<'create' | 'join'>('create');
  const [activeSession, setActiveSession] = useState<DebateSessionResponse | null>(null);
  const [currentWalletAddress, setCurrentWalletAddress] = useState('');
  const [isValidParticipant, setIsValidParticipant] = useState(false);

  const [activeTab, setActiveTab] = useState<
    'contribute' | 'nodes' | 'stats' | 'leaderboard' | 'topics' | 'conclusion'
  >('contribute');

  const [walletAddress, setWalletAddress] = useState('');
  const [debateId, setDebateId] = useState('');

  // Data states
  const [nodes, setNodes] = useState<DebateNode[]>([]);
  const [stats, setStats] = useState<DebateStatsType | null>(null);
  const [leaderboard, setLeaderboard] = useState<LeaderboardResponse | null>(null);
  const [topicsAnalysis, setTopicsAnalysis] = useState<TopicAnalysis | null>(null);
  const [conclusion, setConclusion] = useState<DebateConclusionType | null>(null);
  const [aiAnalysis, setAIAnalysis] = useState<AIAnalysis | null>(null);

  // Loading states
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLoadingNodes, setIsLoadingNodes] = useState(false);
  const [isLoadingStats, setIsLoadingStats] = useState(false);
  const [isLoadingLeaderboard, setIsLoadingLeaderboard] = useState(false);
  const [isLoadingTopics, setIsLoadingTopics] = useState(false);
  const [isLoadingConclusion, setIsLoadingConclusion] = useState(false);

  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Validate if current wallet is creator or participant
  const validateWalletAccess = (walletAddress: string) => {
    if (!activeSession) return false;

    const isCreator = activeSession.creator_wallet.toLowerCase() === walletAddress.toLowerCase();
    const isParticipant = activeSession.participants.some(
      (p) => p.wallet_address.toLowerCase() === walletAddress.toLowerCase()
    );

    return isCreator || isParticipant;
  };

  // Handle new session creation
  const handleSessionCreated = (session: DebateSessionResponse) => {
    setActiveSession(session);
    setDebateId(session.session_id);
    setSessionMode('join');
    setSuccessMessage(`Debate session created: ${session.topic_name}`);
    setTimeout(() => setSuccessMessage(null), 5000);
  };

  // Load existing session
  const loadExistingSession = async (sessionId: string) => {
    try {
      const session = await getDebateSession(sessionId);
      setActiveSession(session);
      setDebateId(session.session_id);
      setSessionMode('join');
      setSuccessMessage(`Joined debate session: ${session.topic_name}`);
      setTimeout(() => setSuccessMessage(null), 5000);
    } catch (err) {
      setError(`Failed to load session: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  // Update contributed wallet validation
  useEffect(() => {
    if (currentWalletAddress && activeSession) {
      const isValid = validateWalletAccess(currentWalletAddress);
      setIsValidParticipant(isValid);
      if (!isValid) {
        setError('Your wallet address is not authorized for this debate session');
      }
    }
  }, [currentWalletAddress, activeSession]);

  // Load data based on active tab
  useEffect(() => {
    switch (activeTab) {
      case 'nodes':
        loadNodes();
        break;
      case 'stats':
        loadStats();
        break;
      case 'leaderboard':
        loadLeaderboard();
        break;
      case 'topics':
        loadTopicsAnalysis();
        break;
      case 'conclusion':
        loadConclusion();
        break;
    }
  }, [activeTab]);

  // Auto-refresh nodes when on contribute tab
  useEffect(() => {
    if (activeTab === 'contribute') {
      loadNodes();
      const interval = setInterval(loadNodes, 10000); // Refresh every 10 seconds
      return () => clearInterval(interval);
    }
  }, [activeTab]);

  const loadNodes = async () => {
    setIsLoadingNodes(true);
    try {
      const response = await getAllDebateNodes();
      setNodes(response.nodes);
    } catch (err) {
      console.error('Failed to load debate nodes:', err);
    } finally {
      setIsLoadingNodes(false);
    }
  };

  const loadStats = async () => {
    setIsLoadingStats(true);
    try {
      const data = await getDebateStats();
      setStats(data);
    } catch (err) {
      console.error('Failed to load stats:', err);
    } finally {
      setIsLoadingStats(false);
    }
  };

  const loadLeaderboard = async () => {
    setIsLoadingLeaderboard(true);
    try {
      const data = await getDebateLeaderboard(20);
      setLeaderboard(data);
    } catch (err) {
      console.error('Failed to load leaderboard:', err);
    } finally {
      setIsLoadingLeaderboard(false);
    }
  };

  const loadTopicsAnalysis = async () => {
    setIsLoadingTopics(true);
    try {
      const data = await getTopicsAnalysis();
      setTopicsAnalysis(data);
    } catch (err) {
      console.error('Failed to load topics analysis:', err);
    } finally {
      setIsLoadingTopics(false);
    }
  };

  const loadConclusion = async () => {
    setIsLoadingConclusion(true);
    try {
      const [conclusionData, aiData] = await Promise.all([
        getDebateConclusion(debateId !== 'default-debate' ? debateId : undefined),
        getAIAnalysis(debateId !== 'default-debate' ? debateId : undefined),
      ]);
      setConclusion(conclusionData);
      setAIAnalysis(aiData);
    } catch (err) {
      console.error('Failed to load conclusion:', err);
    } finally {
      setIsLoadingConclusion(false);
    }
  };

  const handleSubmitContribution = async (speaker: string, text: string) => {
    // Validate wallet access
    if (!validateWalletAccess(speaker)) {
      setError('Your wallet address is not registered as creator or participant for this session');
      return;
    }

    setIsSubmitting(true);
    setError(null);
    setSuccessMessage(null);

    try {
      const response = await addDebateTranscription({
        speaker,
        text,
        debate_id: debateId,
      });

      // Show success message
      const action = response.action === 'merged' ? 'merged' : 'created';
      setSuccessMessage(
        `Contribution ${action}! ${
          response.merge_count ? `Merged ${response.merge_count} times.` : ''
        }`
      );

      // Update wallet address for next contribution
      setWalletAddress(speaker);
      setCurrentWalletAddress(speaker);

      // Reload nodes
      await loadNodes();

      // Clear success message after 5 seconds
      setTimeout(() => setSuccessMessage(null), 5000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit contribution');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRefreshConclusion = () => {
    loadConclusion();
  };

  const tabs = [
    { key: 'contribute' as const, label: 'Contribute', icon: '✍️' },
    { key: 'nodes' as const, label: 'Discussion', icon: '💬' },
    { key: 'stats' as const, label: 'Statistics', icon: '📊' },
    { key: 'leaderboard' as const, label: 'Leaderboard', icon: '🏆' },
    { key: 'topics' as const, label: 'Topics', icon: '🔥' },
    { key: 'conclusion' as const, label: 'Conclusion', icon: '🎯' },
  ];

  return (
    <div className="min-h-screen bg-gray-950 flex flex-col">
      {/* If no session, show session creator */}
      {!activeSession ? (
        <>
          {/* Header */}
          <header className="bg-gray-900 border-b border-gray-700 px-6 py-4 flex-shrink-0">
            <div className="max-w-7xl mx-auto">
              <div className="flex items-center gap-4 mb-4">
                <Link
                  href="/"
                  className="text-purple-400 hover:text-purple-300 transition-colors"
                >
                  ← Home
                </Link>
                <div>
                  <h1 className="text-2xl font-bold text-purple-400">Debate Mode</h1>
                  <p className="text-sm text-gray-400 mt-1">
                    Initialize a debate session or join an existing one
                  </p>
                </div>
              </div>

              {/* Mode selector */}
              <div className="flex gap-2">
                <button
                  onClick={() => setSessionMode('create')}
                  className={`px-4 py-2 rounded-lg transition-all text-sm font-medium ${
                    sessionMode === 'create'
                      ? 'bg-purple-600 text-white'
                      : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                  }`}
                >
                  Create Session
                </button>
                <button
                  onClick={() => setSessionMode('join')}
                  className={`px-4 py-2 rounded-lg transition-all text-sm font-medium ${
                    sessionMode === 'join'
                      ? 'bg-purple-600 text-white'
                      : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                  }`}
                >
                  Join Existing
                </button>
              </div>
            </div>
          </header>

          {/* Main Content - Session Creation/Join */}
          <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-8">
            {/* Error/Success Messages */}
            {error && (
              <div className="mb-6 bg-red-900/50 border border-red-700 text-red-200 px-4 py-3 rounded-lg">
                {error}
              </div>
            )}
            {successMessage && (
              <div className="mb-6 bg-green-900/50 border border-green-700 text-green-200 px-4 py-3 rounded-lg">
                {successMessage}
              </div>
            )}

            {sessionMode === 'create' ? (
              <DebateSessionCreator onSessionCreated={handleSessionCreated} />
            ) : (
              <div className="max-w-3xl mx-auto">
                <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
                  <h2 className="text-2xl font-bold text-purple-400 mb-2">Join Debate Session</h2>
                  <p className="text-gray-400 text-sm mb-6">
                    Enter a session ID to join an existing debate.
                  </p>

                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">
                        Session ID <span className="text-red-400">*</span>
                      </label>
                      <input
                        type="text"
                        value={debateId}
                        onChange={(e) => setDebateId(e.target.value)}
                        placeholder="Enter session ID (UUID)"
                        className="w-full bg-gray-900 text-white border border-gray-700 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
                      />
                    </div>

                    <button
                      onClick={() => loadExistingSession(debateId)}
                      disabled={!debateId.trim()}
                      className="w-full bg-purple-600 hover:bg-purple-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white font-medium py-3 px-6 rounded-lg transition-colors"
                    >
                      Join Session
                    </button>
                  </div>
                </div>
              </div>
            )}
          </main>

          {/* Footer */}
          <footer className="bg-gray-900 border-t border-gray-700 px-6 py-4 flex-shrink-0">
            <div className="max-w-7xl mx-auto text-center text-sm text-gray-400">
              <p>NeuroChain Debate Mode - Powered by AI and Blockchain</p>
            </div>
          </footer>
        </>
      ) : (
        <>
          {/* Debate Session Active - Show full debate interface */}
          {/* Header */}
          <header className="bg-gray-900 border-b border-gray-700 px-6 py-4 sticky top-0 z-10 flex-shrink-0">
            <div className="max-w-7xl mx-auto">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <div className="flex items-center gap-4">
                    <button
                      onClick={() => {
                        setActiveSession(null);
                        setDebateId('');
                        setCurrentWalletAddress('');
                      }}
                      className="text-purple-400 hover:text-purple-300 transition-colors"
                    >
                      ← Home to Session Menu
                    </button>
                  </div>
                  <h1 className="text-2xl font-bold text-purple-400 mt-2">{activeSession.topic_name}</h1>
                  <p className="text-sm text-gray-400 mt-1">
                    Created by: {activeSession.creator_names.join(', ')} • Participants: {activeSession.participants.length}
                  </p>
                </div>

                {/* Session Info */}
                <div className="text-right">
                  <div className="text-sm text-gray-400 mb-2">Session ID:</div>
                  <div className="font-mono text-xs bg-gray-800 px-3 py-2 rounded border border-gray-700 text-gray-200 break-all">
                    {activeSession.session_id}
                  </div>
                  {!isValidParticipant && currentWalletAddress && (
                    <p className="text-xs text-red-400 mt-2">⚠️ Wallet not authorized</p>
                  )}
                </div>
              </div>

              {/* Tabs */}
              <div className="flex gap-2 overflow-x-auto">
                {tabs.map((tab) => (
                  <button
                    key={tab.key}
                    onClick={() => setActiveTab(tab.key)}
                    className={`px-4 py-2 rounded-lg transition-all text-sm font-medium whitespace-nowrap ${
                      activeTab === tab.key
                        ? 'bg-purple-600 text-white'
                        : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                    }`}
                  >
                    {tab.icon} {tab.label}
                  </button>
                ))}
              </div>
            </div>
          </header>

          {/* Main Content */}
          <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-8">
            {/* Error/Success Messages */}
            {error && (
              <div className="mb-6 bg-red-900/50 border border-red-700 text-red-200 px-4 py-3 rounded-lg">
                {error}
              </div>
            )}
            {successMessage && (
              <div className="mb-6 bg-green-900/50 border border-green-700 text-green-200 px-4 py-3 rounded-lg">
                {successMessage}
              </div>
            )}

            {/* Content based on active tab */}
            {activeTab === 'contribute' && (
              <div className="space-y-6">
                {/* Authorization Check */}
                {currentWalletAddress && !isValidParticipant && (
                  <div className="bg-amber-900/50 border border-amber-700 text-amber-200 px-4 py-3 rounded-lg">
                    ⚠️ Your wallet address ({currentWalletAddress}) is not registered for this debate session.
                    Only the creator and participants can contribute.
                  </div>
                )}

                {/* Input Section */}
                <DebateTranscriptionInput
                  onSubmit={handleSubmitContribution}
                  isLoading={isSubmitting}
                  currentSpeaker={walletAddress}
                />

                {/* Recent Contributions */}
                <div>
                  <h2 className="text-xl font-bold text-white mb-4">Recent Contributions</h2>
                  <DebateNodesList
                    nodes={nodes.slice(0, 10)}
                    isLoading={isLoadingNodes}
                  />
                </div>
              </div>
            )}

            {activeTab === 'nodes' && (
              <div>
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-xl font-bold text-white">All Discussion Nodes</h2>
                  <button
                    onClick={loadNodes}
                    className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-sm transition-colors"
                  >
                    Refresh
                  </button>
                </div>
                <DebateNodesList nodes={nodes} isLoading={isLoadingNodes} />
              </div>
            )}

            {activeTab === 'stats' && (
              <div>
                <h2 className="text-xl font-bold text-white mb-6">Debate Statistics</h2>
                <DebateStats stats={stats} isLoading={isLoadingStats} />
              </div>
            )}

            {activeTab === 'leaderboard' && (
              <div>
                <h2 className="text-xl font-bold text-white mb-6">Speaker Leaderboard</h2>
                <SpeakerLeaderboard
                  speakers={leaderboard?.speakers || []}
                  isLoading={isLoadingLeaderboard}
                />
              </div>
            )}

            {activeTab === 'topics' && (
              <div>
                <TopicsAnalysis analysis={topicsAnalysis} isLoading={isLoadingTopics} />
              </div>
            )}

            {activeTab === 'conclusion' && (
              <div>
                <DebateConclusion
                  conclusion={conclusion}
                  aiAnalysis={aiAnalysis}
                  isLoading={isLoadingConclusion}
                  onRefresh={handleRefreshConclusion}
                />
              </div>
            )}
          </main>

          {/* Footer */}
          <footer className="bg-gray-900 border-t border-gray-700 px-6 py-4 flex-shrink-0">
            <div className="max-w-7xl mx-auto text-center text-sm text-gray-400">
              <p>NeuroChain Debate Mode - Powered by AI and Blockchain</p>
            </div>
          </footer>
        </>
      )}
    </div>
  );
}
